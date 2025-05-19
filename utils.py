import time
import tkinter as tk
import datetime as dt
import pandas as pd
import streamlit as st

from io import StringIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from bs4 import BeautifulSoup, Tag
from tkinter import filedialog
from pandas import DataFrame

def prompt(teams: dict[str, dict[str, any]]) -> str:
    """
    Prompts the user for a team name returns it.

    Args:
        teams (dict[str, dict[str, any]]): Dictionary containing settings.

    Returns:
        str: The name of the team.
    """
    try:
        print()
        print("Enter A Team:")

        for team in teams.keys():
            print(f"   {team}")

        print("   Exit")

        team_name = input()
        return team_name

    except Exception as e:
        print("ERROR")
        print("ERROR: invalid input")
        print("ERROR")
        return -1

def select_output_folder() -> str:
    """
    Opens the file dialog, allowing users to select an output folder.

    Args:
        None

    Returns:
        str: The full path to the selected folder.
    """
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(master=root)
    root.destroy()

    return folder_path

def initialize_web_driver() -> webdriver.Chrome:
    """
    Initializes a new web driver instance.

    Args:
        None

    Returns:
        WebDriver: A new web driver instance.
    """
    service = Service(executable_path="chromedriver.exe")

    chrome_options = ChromiumOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    return webdriver.Chrome(service=service, options=chrome_options)

def sanitize_html(html_str: str) -> str:
    """
    Removes any embedded tweets and advertisement content from HTML string.

    Args:
        html_str (str): The unsanitized HTML string.

    Returns:
        str: The sanitized HTML table.
    """
    doc = BeautifulSoup(html_str, "lxml")

    for tweet in doc.find_all("div", class_="twitter-tweet twitter-tweet-rendered"):
        tweet.extract()

    tables = doc.find_all("table")
    for table in tables:
        table_rows = table(["tr"])
        for table_row in table_rows:
            if ("skip ad" in table_row.get_text().lower()):
                table_row.extract()

    return str(doc)

def insert_html_tables(title: str, html_tables: list[str]) -> str:
    """
    Initialize a HTML table.

    Args:
        title (str): Title for the HTML document.
        html_tables (list[str]): List of HTML strings containing tables to insert.

    Returns:
        str: A string representation of the full .HTML document.
    """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
        table {{ width: 100%; border-collapse: collapse; }}
            thead {{ display: table-row-group; }}
            th, td {{ font-size: 12px; border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
        </style>
    </head>
    <body>
        <main>
            <h1>{title}</h1>
        </main>
    </body>
    </html>
    """
    doc = BeautifulSoup(html, "lxml")

    main = doc.find("main")

    for html_table in html_tables:
        div_tag = doc.new_tag("div")
        main.append(div_tag)

        table = BeautifulSoup(html_table, "lxml")
        main.append(table)

    return str(doc)

def insert_article_content(title: str, content_string: str) -> str:
    """
    Initialize a HTML table.

    Args:
        title (str): Title for the HTML document.
        content_string (list[str]): HTML string containing the article content.

    Returns:
        str: A string representation of the full .HTML document.
    """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body>
        <main>
            <h1>{title}</h1>
        </main>
    </body>
    </html>
    """
    doc = BeautifulSoup(html, "lxml")

    main = doc.find("main")

    content = BeautifulSoup(content_string, "lxml")
    main.append(content)

    return str(doc)

def find_penn_state_stats_url(url: str) -> str:
    """
    Get the URLs of the stats PDF for Penn State.

    Args:
        url (str): The base URL of Penn State's Mens Soccer

    Returns:
        str: The URL of the stats PDF for Penn State.
    """
    driver = initialize_web_driver()
    driver.get(url)
    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")

    ul = doc.find("ul", class_="menu menu--level-0 menu--sport")
    li = ul.find_all("li", class_="menu-item menu-item--static-url menu-item--show-on-mobile menu-item--show-on-desktop menu__item")[5]
    stats_url = li.find("a")["href"]

    driver.get(stats_url)
    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")

    div = doc.find("div", class_="container pdf-block__container")
    stats_pdf_url = div.find("a")["href"]

    driver.quit()

    return stats_pdf_url

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
    return box_score_pdf_urls[(-1 * count):]

def get_sidearm_match_data(driver: webdriver.Chrome, team_data: dict[str, str], doc: BeautifulSoup, count: int) -> list[tuple[str, str, str, str]]:
    """
    Get the URLs of the box scores from the conference websites provided by Sidearm.

    Args:
        driver (WebDriver): The web driver instance.
        team_data (dict[str, str]): Dictionary containing team data.
        doc (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
        count (int): The number of box scores to print.

    Returns:
        list[tuple[str, str, str, str]]: List of match data represented as a tuple of the form (home_team, away_team, date, box_score_url) where:
            home_team (str): Name of the home team.
            away_team (str): Name of the away team.
            date (str): The date of the match.
            box_score_url (str): The box score PDF url.
    """
    matchday_tables = doc.find_all("table")

    matches = []
    for matchday_table in matchday_tables:
        matchday_table_body = matchday_table.find("tbody")

        for tr in matchday_table_body.find_all("tr"):
            away_team_td = tr.select_one('td[class*="sidearm-team-away"]')
            home_team_td = tr.select_one('td[class*="sidearm-team-home"]')

            away_team = away_team_td.find("span", class_="sidearm-calendar-list-group-list-game-team-title").find(['a', 'span']).text
            home_team = home_team_td.find("span", class_="sidearm-calendar-list-group-list-game-team-title").find(['a', 'span']).text
            if (away_team != team_data["name"] and home_team != team_data["name"]): continue

            matchday_table_caption = matchday_table.find("caption")
            date = matchday_table_caption.find("span", class_="hide-on-medium sidearm-calendar-list-group-heading-date").text.replace("/", "_")

            box_score_href = team_data["conference_base_url"] + tr.find("a", string="Box Score")["href"]

            matches.append([home_team, away_team, date, box_score_href])

    count = min(len(matches), count)

    match_data = []
    for match in matches[(-1 * count):]:
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

def scan_table_for_articles(team_data: dict[str, str], table: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    team_name = team_data["name"]
    start_date = date_range[0]
    end_date = date_range[1]

    sanitized_table = sanitize_html(str(table))

    links = [f"https://{team_data["hostname"]}{a["href"]}" for a in table.find_all("a") if (a["href"] != "#")]

    dataframe = pd.read_html(StringIO(sanitized_table))[0]
    dataframe = dataframe.drop(columns=["Sport", "Category"], errors="ignore")
    dataframe["URL"] = links

    if (team_name == "Maryland") or (team_name == "Washington") or (team_name == "UIC") or (team_name == "Northern Illinois") or (team_name == "Chicago State"):
        dataframe["Posted"] = pd.to_datetime(dataframe["Posted"], format='%m/%d/%Y')

        for index, row in dataframe.iterrows():
            if not (start_date <= row["Posted"].date() <= end_date):
                dataframe.drop(index, inplace=True)
    else:
        dataframe["Date"] = pd.to_datetime(dataframe["Date"], format='%B %d, %Y')

        for index, row in dataframe.iterrows():
            if not (start_date <= row["Date"].date() <= end_date):
                dataframe.drop(index, inplace=True)

    st.write(f"Finished fetching {team_data["name"]}'s articles!")
    return dataframe

def scan_ul_for_articles(team_data: dict[str, str], ul: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    start_date = date_range[0]
    end_date = date_range[1]

    sanitized_ul = sanitize_html(str(ul))
    sanitized_ul = BeautifulSoup(sanitized_ul, "lxml")

    dataframe = DataFrame(columns=["Date", "Headline", "URL"])

    for li in sanitized_ul.find_all("li", class_="vue-archives-item flex"):
        date_string = li.find("span").text
        if ("Date: " in date_string):
            date_string = date_string.replace("Date: ", "")

        date = dt.datetime.strptime(date_string, '%B %d, %Y').date()

        if not (start_date <= date):
            continue

        if not (date <= end_date):
            break

        a = li.find("a")
        headline = a.text
        url = f"https://{team_data["hostname"]}{a["href"]}"
        dataframe.loc[len(dataframe)] = [date, headline, url]

    st.write(f"Finished fetching {team_data["name"]}'s articles!")
    return dataframe
