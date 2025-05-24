import time
from io import BytesIO

import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException, ElementNotVisibleException

from utils import initialize_web_driver, response_pdf_to_zipfile


def download_box_scores(team_data: dict, count: int, zip_buffer: BytesIO) -> None:
    """Downloads box scores into respective PDF files.

    Args:
        team_data: Dictionary containing team data.
        count: The number of box scores to print.
        zip_buffer: Bytes buffer containing box scores.

    Returns:
        None
    """
    driver = initialize_web_driver()

    try:
        if team_data["conference_schedule_provider"] == "Boost":
            schedule_url = f"{team_data['conference_base_url']}/msoc/schedule/?teamFilter={team_data['abbreviation']}"

            driver.get(schedule_url)
            time.sleep(1)
            doc = BeautifulSoup(driver.page_source, "lxml")

            box_score_pdf_urls = get_boost_box_score_pdf_urls(doc, count)

            for box_score_pdf_url in box_score_pdf_urls:
                filename = box_score_pdf_url.split("/")[-1]

                response_pdf_to_zipfile(box_score_pdf_url, filename, zip_buffer)
        elif team_data["conference_schedule_provider"] == "Sidearm":
            schedule_url = f"{team_data['conference_base_url']}/calendar.aspx?path=msoc"

            driver.get(schedule_url)
            time.sleep(1)
            doc = BeautifulSoup(driver.page_source, "lxml")

            box_score_pdf_urls = get_sidearm_match_data(driver, team_data, doc, count)

            for home_team, away_team, date, box_score_pdf_url in box_score_pdf_urls:
                filename = f"{home_team} vs {away_team} {date}.pdf"

                response_pdf_to_zipfile(box_score_pdf_url, filename, zip_buffer)
    except TimeoutException as e:
        st.write(e)
    finally:
        driver.quit()


def get_boost_box_score_pdf_urls(doc: BeautifulSoup, count: int) -> list[str]:
    """
    Get the URLs of the box scores from the conference websites provided by Boost.

    Args:
        doc: The BeautifulSoup object containing the parsed HTML.
        count: The number of box scores to print.

    Returns:
        List of box score PDF URLs.
    """
    schedule_table = doc.find("table")
    box_score_pdf_urls = [a["href"] for a in schedule_table.find_all("a", string="Box Score")]

    count = min(len(box_score_pdf_urls), count)
    return box_score_pdf_urls[-count:]


def get_sidearm_match_data(driver: webdriver.Chrome, team_data: dict, doc: BeautifulSoup, count: int) -> list[
    tuple[str, str, str, str]]:
    """
    Get the URLs of the box scores from the conference websites provided by Sidearm.

    Args:
        driver: The WebDriver.
        team_data: Dictionary containing team data.
        doc: The BeautifulSoup object containing the parsed HTML.
        count: The number of box scores to print.

    Returns:
        List of match data represented as a tuple of the form (home_team, away_team, date, box_score_pdf_url).
    """
    match_tables = doc.find_all("table")
    matches = extract_matches(team_data, match_tables)

    return fetch_pdf_urls_for_matches(driver, matches, team_data, count)


def extract_matches(team_data: dict, match_tables: list) -> list[tuple[str, str, str, str]]:
    """Extract matches from the match tables.

    Args:
        team_data: Dictionary containing team data.
        match_tables: List of match table elements.

    Returns:
        List of match data represented as a tuple of the form (home_team, away_team, date, box_score_url).
    """
    matches = []
    for match_table in match_tables:
        match_table_body = match_table.find("tbody")

        for tr in match_table_body.find_all("tr"):
            away_team = get_team_name(tr, 'sidearm-team-away')
            home_team = get_team_name(tr, 'sidearm-team-home')

            if (away_team != team_data["name"]) and (home_team != team_data["name"]):
                continue

            date = extract_match_date(match_table)
            box_score_href = team_data["conference_base_url"] + tr.find("a", string="Box Score")["href"]
            matches.append((home_team, away_team, date, box_score_href))

    return matches


def get_team_name(table_row: BeautifulSoup, team_class: str) -> str:
    """
    Extract the team name from a table row.

    Args:
        table_row: Table row element containing team data.
        team_class: Class name to identify the team.

    Returns:
        Extracted team name.
    """
    team_td = table_row.select_one(f'td[class*="{team_class}"]')
    return team_td.find("span", class_="sidearm-calendar-list-group-list-game-team-title").find(['a', 'span']).text


def extract_match_date(match_table: BeautifulSoup) -> str:
    """
    Extract the match date from the match table caption.

    Args:
        match_table: Match table element.

    Returns:
        Extracted match date.
    """
    match_table_caption = match_table.find("caption")
    return match_table_caption.find("span",
                                    class_="hide-on-medium sidearm-calendar-list-group-heading-date").text.replace("/",
                                                                                                                   "_")


def fetch_pdf_urls_for_matches(driver: webdriver.Chrome, matches: list[tuple[str, str, str, str]],
                               team_data: dict, count: int) -> list[tuple[str, str, str, str]]:
    """
    Fetch the PDF URLs for box scores for the given matches.

    Args:
        driver: The web driver instance.
        matches: List of matches containing details.
        team_data: Dictionary containing team data.
        count: The number of box scores to fetch.

    Returns:
        List of match data represented as a tuple of the form (home_team, away_team, date, box_score_pdf_url).
    """
    match_data = []

    for match in matches[-count:]:
        try:
            driver.get(match[3])
            time.sleep(1)

            doc = BeautifulSoup(driver.page_source, "lxml")
            print_bar = doc.find("div", id="print-bar")
            if print_bar:
                box_score_preview_url = team_data["conference_base_url"] + print_bar.find("a")["href"]
            else:
                raise ElementNotVisibleException(
                    f"No box score PDF available for {match[0]} vs. {match[1]} on {match[2]}")

            driver.get(box_score_preview_url)
            time.sleep(1)

            doc = BeautifulSoup(driver.page_source, "lxml")
            box_score_pdf_url = doc.find("object")["data"]

            match_data.append((match[0], match[1], match[2], box_score_pdf_url))
        except TimeoutException as e:
            st.write(f"**{match[0]} vs. {match[1]} {match[2]}.pdf** Failed!  \nReason: {e}")
        except ElementNotVisibleException as e:
            st.write(f"**{match[0]} vs. {match[1]} {match[2]}.pdf** Failed!  \nReason: {e}")

    return match_data
