import datetime
import io
import json

import streamlit as st

from articles import download_articles, fetch_articles
from box_scores import download_box_scores
from roster import download_roster
from schedule import download_schedule
from stats import download_stats

with open("teams.json", "r") as file:
    teams: dict = json.load(file)

st.title = "NU Soccer Web Scraper"

team_name = st.selectbox(
    label="Enter a team name:",
    options=teams.keys(),
    index=None,
    placeholder="ie: Northwestern",
)

with st.container(border=True):
    if "disabled" not in st.session_state:
        st.session_state.disabled = False

    selected_data = st.segmented_control(
        label="Select the data you want to download:",
        options=["Roster", "Schedule", "Stats", "Box Scores", "Articles"],
        selection_mode="multi",
        disabled=st.session_state.disabled
    )

    select_all = st.toggle(
        label="Select all",
        key="disabled"
    )

data_to_scrape = ["Roster", "Schedule", "Stats", "Box Scores", "Articles"] if select_all else selected_data

if "Stats" in data_to_scrape:
    with st.container(border=True):
        years = st.multiselect(
            label="Select which year's stats you would like to download:",
            options=["2024", "2023"],
            default=["2024", "2023"],
            placeholder="ie: 2024"
        )

        with st.expander("**Disclaimer**"):
            st.warning(
                "Options for years will be added at the start of every Fall season. However, please be aware that depending on the time of the current season, there might not be stats available to download yet.")

if "Box Scores" in data_to_scrape:
    with st.container(border=True):
        count = st.number_input(
            label="Enter the number of box scores you would like download (1-10):",
            step=1,
            min_value=1,
            value=5,
            max_value=10,
            placeholder="ie: 5"
        )

        with st.expander("**Disclaimer**"):
            st.warning(
                "Box scores are downloaded in order from newest to oldest. Only the current season will be searched. If there are not enough box scores available, we will attempt to download as many as possible.")

if "Articles" in data_to_scrape:
    with st.container(border=True):
        season_start = datetime.date(2024, 8, 22)
        now = datetime.datetime.now()
        today = datetime.date(now.year, now.month, now.day)

        date_range = st.date_input(
            label="Enter the range of dates you would like to see articles:",
            value=(season_start, today),
            format="MM/DD/YYYY",
        )

scrape_button = st.button(
    label="Scrape",
    disabled=(not team_name) or (not data_to_scrape)
)

if scrape_button:
    team_data = teams[team_name]
    zip_buffer = io.BytesIO()

    if "Roster" in data_to_scrape:
        filename = f"{team_data['abbreviation']} Roster.pdf"
        download_roster(team_data["roster_url"], filename, zip_buffer)

    if "Schedule" in data_to_scrape:
        filename = f"{team_data["abbreviation"]} Schedule.pdf"
        download_schedule(team_data["name"], team_data["schedule_url"], filename, zip_buffer)

    if "Box Scores" in data_to_scrape:
        download_box_scores(team_data, count, zip_buffer)

    if "Stats" in data_to_scrape:
        download_stats(team_data, years, zip_buffer)

    if "Articles" in data_to_scrape:
        articles = fetch_articles(team_data, date_range)


        @st.fragment
        def select_articles():
            column_configuration = {
                "Date": st.column_config.DatetimeColumn(
                    width="small",
                    format="MM/DD/YYYY"
                ),
                "Posted": st.column_config.DatetimeColumn(
                    width="small",
                    format="MM/DD/YYYY"
                ),
                "Headline": st.column_config.TextColumn(
                    width="large"
                ),
                "URL": None
            }

            if "submitted" not in st.session_state:
                st.session_state.submitted = False

            st.write("Select which articles you would like to download:")

            all_articles = st.dataframe(
                data=articles,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi-row",
                column_config=column_configuration
            )

            article_indexes = all_articles.selection.rows
            filtered_articles = articles.iloc[article_indexes]

            if st.button("Download Selected Articles"):
                download_articles(filtered_articles, zip_buffer)
                st.session_state.submitted = True

            if st.session_state.submitted:
                st.download_button(
                    "Download PDFs",
                    file_name=f"{team_name}.zip",
                    mime="application/zip",
                    data=zip_buffer
                )

                del st.session_state.submitted

        if articles is not None:
            select_articles()
        else:
            st.write("No articles could be found.")
    else:
        st.download_button(
            "Download PDFs",
            file_name=f"{team_name}.zip",
            mime="application/zip",
            data=zip_buffer
        )
