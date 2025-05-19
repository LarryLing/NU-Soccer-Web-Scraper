import time
import pdfkit
import requests
import pandas as pd
import streamlit as st
import datetime as dt

from io import StringIO
from utils import find_penn_state_stats_url, insert_article_content, insert_html_tables, get_boost_box_score_pdf_urls, get_sidearm_match_data, initialize_web_driver, sanitize_html, scan_table_for_articles, scan_ul_for_articles
from bs4 import BeautifulSoup
from pdfkit.configuration import Configuration
from pandas import DataFrame

def download_tables(team_name: str, type: str, url: str, output_file_path: str, ignored_columns: list[str], pdfkit_config: Configuration) -> None:
    """
    Downloads the roster page to a PDF file.

    Args:
        team_name (str): Name of the team.
        type (str): Type of table(s) to download. Either "roster" or "schedule".
        url (str): URL of the site.
        output_file_path (str): Path to the downloaded PDF file.
        ignored_columns (list[str]): List of columns to ignore.
        pdfkit_config: (Configuration): Configuration object for pdfkit.

    Returns:
        None
    """
    st.write(f"Downloading {team_name}'s {type}...")

    driver = initialize_web_driver()
    driver.get(url)
    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")

    driver.quit()

    extracted_tables = []
    for table in doc(["table"]):
        if (not table.find("thead")):
            continue

        sanitized_table = sanitize_html(str(table))
        extracted_tables.append(StringIO(sanitized_table))

    html_tables = []
    for extracted_table in extracted_tables:
        dataframe = pd.read_html(extracted_table)[0]
        dataframe = dataframe.drop(columns=ignored_columns, errors="ignore")
        dataframe = dataframe.fillna("")

        html_tables.append(dataframe.to_html(index=False))

    full_html = insert_html_tables(doc.find("title"), html_tables)

    pdfkit.from_string(full_html, output_file_path, configuration=pdfkit_config)

    st.write(f"Finished downloading {team_name}'s {type}!")

def download_stats(team_data: dict[str, str], years: list[int], output_folder_path: str) -> None:
    """
    Downloads a team's season stats to a PDF file.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        years (list[int]): Years for which to print stats for.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    st.write(f"Downloading {team_data["name"]}'s stats...")

    if (team_data["name"] == "Penn State"):
        url = f"https://{team_data["hostname"]}/sports/mens-soccer"
        stats_url = find_penn_state_stats_url(url)

        response = requests.get(stats_url)

        if (response.status_code == 404):
            return

        output_path = f"{output_folder_path}\\{team_data["abbreviation"]} Stats.pdf"

        with open(output_path, 'wb') as file:
            file.write(response.content)

        st.write(f"Finished downloading {team_data["name"]}'s stats!")
        return

    for year in years:
        stats_url = None

        if (team_data["base_website_type"] == 1):
            stats_url = f"https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites/{team_data["hostname"]}/stats/msoc/{year}/pdf/cume.pdf"
        elif (team_data["base_website_type"] == 2):
            stats_url = f"https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/{team_data["hostname"]}/stats/msoc/{year}/pdf/cume.pdf"

        response = requests.get(stats_url)

        if (response.status_code == 404):
            continue

        output_path = f"{output_folder_path}\\{team_data["abbreviation"]} {year} Stats.pdf"

        with open(output_path, 'wb') as file:
            file.write(response.content)

    st.write(f"Finished downloading {team_data["name"]}'s stats!")

def download_box_scores(team_data: dict[str, str], count: int, output_folder_path: str) -> None:
    """
    Downloads box scores into respective PDF files.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        count (int): The number of box scores to print.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    st.write(f"Downloading {team_data["name"]}'s box scores...")

    driver = initialize_web_driver()
    driver.get(team_data["conference_schedule_url"])

    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")

    if (team_data["conference_schedule_provider"] == "Boost"):
        box_score_pdf_urls = get_boost_box_score_pdf_urls(doc, count)

        for box_score_pdf_url in box_score_pdf_urls:
            filename = box_score_pdf_url.split("/")[-1]

            response = requests.get(box_score_pdf_url)
            output_path = f"{output_folder_path}\\{filename}"

            with open(output_path, 'wb') as file:
                file.write(response.content)
    elif (team_data["conference_schedule_provider"] == "Sidearm"):
        match_data = get_sidearm_match_data(driver, team_data, doc, count)

        for home_team, away_team, date, box_score_pdf_url in match_data:
            filename = f"{home_team} vs {away_team} {date}.pdf"

            response = requests.get(box_score_pdf_url)
            output_path = f"{output_folder_path}\\{filename}"

            with open(output_path, 'wb') as file:
                file.write(response.content)

    driver.quit()

    st.write(f"Finished downloading {team_data["name"]}'s box scores!")

def fetch_articles(team_data: dict[str, str], date_range: tuple[dt.date, dt.date]) -> DataFrame:
    """
    Fetches a team's articles, returnin their headlines and URLs.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        date_range (tuple[date, date]): Range of dates to fetch articles from.

    Returns:
        DataFrame: Dataframe of articles to download containing the date posted, headline, and URL.
    """
    st.write(f"Fetching {team_data["name"]}'s articles...")

    driver = initialize_web_driver()
    driver.get(team_data["articles_url"])

    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")

    driver.quit()

    if (team_data["article_display_type"] == "table"):
        table = doc.find("table")
        dataframe = scan_table_for_articles(team_data, table, date_range)
    elif (team_data["article_display_type"] == "list"):
        ul = doc.find("div", class_="vue-archives-stories").find("ul")
        dataframe = scan_ul_for_articles(team_data, ul, date_range)

    st.write(f"Finished fetching {team_data["name"]}'s articles!")
    return dataframe

def download_articles(team_data: dict[str, str], articles: DataFrame, output_folder_path: str, pdfkit_config: Configuration) -> None:
    """
    Downloads selected articles into respective PDF files. Article's who's URLs link to a website that does not share
    the same hostname will be printed out as a Streamlit Dataframe instance.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        articles (DataFrame): Dataframe of articles to download containing the date posted, headline, and URL.
        output_folder_path (str): Path to the output folder.
        pdfkit_config: (Configuration): Configuration object for pdfkit.

    Returns:
        None
    """
    st.write(f"Downloading selected articles...")

    driver = initialize_web_driver()

    undownloaded_articles = articles.iloc[0:0].copy()
    for _, row in articles.iterrows():
        driver.get(row["URL"])
        time.sleep(1)

        if (team_data["hostname"] not in driver.current_url):
            undownloaded_articles.loc[len(undownloaded_articles)] = row
            continue

        doc = BeautifulSoup(driver.page_source, "lxml")

        content = doc.find("div", id="storyPageContentBody")
        content = sanitize_html(str(content))

        full_html = insert_article_content(row["Headline"], content)

        output_file_path = f"{output_folder_path}\\{row["Headline"]}.pdf"
        pdfkit.from_string(full_html, output_file_path, configuration=pdfkit_config)

    driver.quit()

    if (len(undownloaded_articles) != 0):
        column_configuration = {
            "Date": None,
            "Posted": None,
            "Headline": st.column_config.TextColumn(
                width="medium"
            ),
            "URL": st.column_config.LinkColumn(
                width="medium"
            )
        }

        st.write("We could not download the following articles. Please navigate to the URL and download them manually.")

        st.dataframe(
            data=undownloaded_articles,
            hide_index=True,
            column_config=column_configuration
        )

    st.write(f"Finished downloading selected articles!")
