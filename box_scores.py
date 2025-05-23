import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
from utils import initialize_web_driver
from selenium import webdriver

def download_box_scores(team_data: dict[str, str], count: int, output_folder_path: str) -> None:
    """Downloads box scores into respective PDF files.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        count (int): The number of box scores to print.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    st.write(f"Downloading {team_data['name']}'s box scores...")

    driver = initialize_web_driver()

    if team_data["conference_schedule_provider"] == "Boost":
        schedule_url = f"{team_data['conference_base_url']}/msoc/schedule/?teamFilter={team_data['abbreviation']}"

        driver.get(schedule_url)
        time.sleep(1)
        doc = BeautifulSoup(driver.page_source, "lxml")

        box_score_pdf_urls = get_boost_box_score_pdf_urls(doc, count)
        download_boost_box_score_pdfs(box_score_pdf_urls, output_folder_path)

    elif team_data["conference_schedule_provider"] == "Sidearm":
        schedule_url = f"{team_data['conference_base_url']}/calendar.aspx?path=msoc"

        driver.get(schedule_url)
        time.sleep(1)
        doc = BeautifulSoup(driver.page_source, "lxml")

        box_score_pdf_urls = get_sidearm_match_data(driver, team_data, doc, count)
        download_sidearm_box_score_pdfs(box_score_pdf_urls, output_folder_path)

    driver.quit()
    st.write(f"Finished downloading {team_data['name']}'s box scores!")

def download_boost_box_score_pdfs(box_score_pdf_urls: list[str], output_folder_path: str) -> None:
    """
    Downloads a PDF from the given URL.

    Args:
        box_score_pdf_urls (list[str]): URL of the box score PDF.
        output_folder_path (str): Path to save the downloaded PDF.

    Returns:
        None
    """
    for box_score_pdf_url in box_score_pdf_urls:
        filename = box_score_pdf_url.split("/")[-1]
        output_path = f"{output_folder_path}/{filename}"

        response = requests.get(box_score_pdf_url)
        with open(output_path, 'wb') as file:
            file.write(response.content)

def download_sidearm_box_score_pdfs(box_score_pdf_urls: list[tuple[str, str, str, str]], output_folder_path: str) -> None:
    """Downloads a PDF from the given URL.

    Args:
        box_score_pdf_urls (list[tuple[str, str, str, str]]): List of match data represented as a tuple of the form (home_team, away_team, date, box_score_pdf_url).
        output_folder_path (str): Path to save the downloaded PDF.

    Returns:
        None
    """
    for home_team, away_team, date, box_score_pdf_url in box_score_pdf_urls:
        filename = f"{home_team} vs {away_team} {date}.pdf"
        output_path = f"{output_folder_path}/{filename}"

        response = requests.get(box_score_pdf_url)
        with open(output_path, 'wb') as file:
            file.write(response.content)

def get_boost_box_score_pdf_urls(doc: BeautifulSoup, count: int) -> list[str]:
    """
    Get the URLs of the box scores from the conference websites provided by Boost.

    Args:
        doc (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
        count (int): The number of box scores to print.

    Returns:
        list[str]: List of box score PDF URLs.
    """
    schedule_table = doc.find("table")
    box_score_pdf_urls = [a["href"] for a in schedule_table.find_all("a", string="Box Score")]

    count = min(len(box_score_pdf_urls), count)
    return box_score_pdf_urls[-count:]

def get_sidearm_match_data(driver: webdriver.Chrome, team_data: dict[str, str], doc: BeautifulSoup, count: int) -> list[tuple[str, str, str, str]]:
    """
    Get the URLs of the box scores from the conference websites provided by Sidearm.

    Args:
        driver (webdriver.Chrome): The WebDriver.
        team_data (dict[str, str]): Dictionary containing team data.
        doc (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
        count (int): The number of box scores to print.

    Returns:
        list[tuple[str, str, str, str]]: List of match data represented as a tuple of the form (home_team, away_team, date, box_score_pdf_url).
    """
    match_tables = doc.find_all("table")
    matches = extract_matches(team_data, match_tables)

    return fetch_pdf_urls_for_matches(driver, matches, team_data, count)

def extract_matches(team_data: dict[str, str], match_tables: list) -> list[tuple[str, str, str, str]]:
    """Extract matches from the match tables.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        match_tables (list): List of match table elements.

    Returns:
        list[tuple[str, str, str, str]]: List of match data represented as a tuple of the form (home_team, away_team, date, box_score_url).
    """
    matches = []
    for match_table in match_tables:
        match_table_body = match_table.find("tbody")

        for tr in match_table_body.find_all("tr"):
            away_team = get_team_name(tr, 'sidearm-team-away')
            home_team = get_team_name(tr, 'sidearm-team-home')

            # Skip if both teams are not involved
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
        table_row (BeautifulSoup): Table row element containing team data.
        team_class (str): Class name to identify the team.

    Returns:
        str: Extracted team name.
    """
    team_td = table_row.select_one(f'td[class*="{team_class}"]')
    return team_td.find("span", class_="sidearm-calendar-list-group-list-game-team-title").find(['a', 'span']).text

def extract_match_date(match_table: BeautifulSoup) -> str:
    """
    Extract the match date from the match table caption.

    Args:
        match_table (BeautifulSoup): Match table element.

    Returns:
        str: Extracted match date.
    """
    match_table_caption = match_table.find("caption")
    return match_table_caption.find("span", class_="hide-on-medium sidearm-calendar-list-group-heading-date").text.replace("/", "_")

def fetch_pdf_urls_for_matches(driver: webdriver.Chrome, matches: list[tuple[str, str, str, str]], team_data: dict[str, str], count: int) -> list[tuple[str, str, str, str]]:
    """Fetch the PDF URLs for box scores for the given matches.

    Args:
        driver (WebDriver): The web driver instance.
        matches (list): List of matches containing details.
        team_data (dict[str, str]): Dictionary containing team data.
        count (int): The number of box scores to fetch.

    Returns:
        list[tuple[str, str, str, str]]: List of match data represented as a tuple of the form (home_team, away_team, date, box_score_pdf_url).
    """
    match_data = []

    for match in matches[-count:]:
        driver.get(match[3])
        time.sleep(1)

        doc = BeautifulSoup(driver.page_source, "lxml")
        box_score_preview_url = team_data["conference_base_url"] + doc.find("div", id="print-bar").find("a")["href"]

        driver.get(box_score_preview_url)
        time.sleep(1)

        doc = BeautifulSoup(driver.page_source, "lxml")
        box_score_pdf_url = doc.find("object")["data"]

        match_data.append((match[0], match[1], match[2], box_score_pdf_url))

    return match_data
