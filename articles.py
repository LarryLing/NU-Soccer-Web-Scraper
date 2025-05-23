import time
import pandas as pd
import streamlit as st
import datetime as dt
from io import StringIO
from pandas import DataFrame
from bs4 import BeautifulSoup, Tag
from selenium.common import TimeoutException
from utils import initialize_web_driver, sanitize_html, print_to_pdf


def fetch_articles(team_data: dict, date_range: tuple[dt.date, dt.date]) -> DataFrame | None:
    """
    Fetches a team's articles, returning their headlines and URLs.

    Args:
        team_data: Dictionary containing team data.
        date_range: Range of dates to fetch articles from.

    Returns:
        DataFrame of articles to download containing the date posted, headline, and URL. None is returned if no articles were found.
    """
    driver = initialize_web_driver()

    article_display_type = team_data["article_display_type"]
    articles_df = None

    try:
        driver.get(team_data["articles_url"])
        time.sleep(1)

        doc = BeautifulSoup(driver.page_source, "lxml")

        if article_display_type == "table":
            table = doc.find("table")
            if table:
                articles_df = scan_table_for_articles(team_data, table, date_range)
        elif article_display_type == "list":
            div = doc.find("div", class_="vue-archives-stories")
            if div:
                ul = div.find("ul")
                articles_df = scan_ul_for_articles(team_data, ul, date_range)

        if articles_df is not None:
            st.write(f"**Fetching Articles** Success!")
            return articles_df
    except TimeoutException as e:
        st.write(f"**Fetching Articles** Failed!\nReason: {e}")
    finally:
        driver.quit()

    return None


def download_articles(articles: DataFrame, output_folder_path: str) -> None:
    """
    Downloads selected articles into respective PDF files.

    Args:
        articles: DataFrame of articles to download containing the date posted, headline, and URL.
        output_folder_path: Path to the output folder.

    Returns:
        None
    """
    if (len(articles) == 0):
        return

    driver = initialize_web_driver()

    script = """
        let removed = document.getElementById('divSatisfiChat'); 
        if (removed) removed.parentNode.removeChild(removed);
        
        removed = document.getElementById('transcend-consent-manager'); 
        if (removed) removed.parentNode.removeChild(removed);
        
        removed = document.getElementById('termly-code-snippet-support'); 
        if (removed) removed.parentNode.removeChild(removed);
    """

    for _, row in articles.iterrows():
        headline = row["Headline"].replace("/", "_")
        output_file_path = f"{output_folder_path}/{headline}.pdf"

        try:
            driver.get(row["URL"])
            time.sleep(1)

            driver.execute_script(script)

            print_to_pdf(driver, output_file_path)
        except TimeoutException as e:
            st.write(f"**{output_file_path.split('/')[-1]}** Failed!\nReason: {e}")

    driver.quit()


def scan_table_for_articles(team_data: dict, table: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    """
    Scans through an HTML table and returns a DataFrame containing the date posted, headline, and URL.

    Args:
        team_data: Dictionary containing team data.
        table: Table tag extracted from the HTML page.
        date_range: Tuple containing start and end dates of articles to download.

    Returns:
        DataFrame of articles to download containing the date posted, headline, and URL.
    """
    start_date, end_date = date_range
    sanitized_table = sanitize_html(table)

    links = [f"{team_data['base_url']}{a['href']}" for a in table.find_all("a") if (a["href"] != "#")]

    dataframe = pd.read_html(StringIO(sanitized_table))[0].drop(columns=["Sport", "Category"], errors="ignore")
    dataframe.drop(dataframe.columns[dataframe.columns.str.contains('Unnamed', case=False)], axis=1, inplace=True)
    dataframe["URL"] = links

    if "Posted" in dataframe.columns:
        dataframe["Date"] = pd.to_datetime(dataframe["Posted"], format='%m/%d/%Y')
        dataframe.drop(columns=["Posted"], inplace=True)
    elif "Date" in dataframe.columns:
        dataframe["Date"] = pd.to_datetime(dataframe["Date"], format='%B %d, %Y')

    if "Title" in dataframe.columns:
        dataframe.rename(columns={"Title": "Headline"}, inplace=True)

    return dataframe[(dataframe["Date"].dt.date >= start_date) & (dataframe["Date"].dt.date <= end_date)]


def scan_ul_for_articles(team_data: dict, ul: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    """
    Scans through an HTML list and returns a DataFrame containing the date posted, headline, and URL.

    Args:
        team_data: Dictionary containing team data.
        ul: Ul tag extracted from the HTML page.
        date_range: Tuple containing start and end dates of articles to download.

    Returns:
        DataFrame of articles to download containing the date posted, headline, and URL.
    """
    start_date, end_date = date_range
    sanitized_ul = sanitize_html(ul)
    sanitized_ul = BeautifulSoup(sanitized_ul, "lxml")

    articles_list = []
    for li in sanitized_ul.find_all("li", class_="vue-archives-item flex"):
        span = li.find("div", class_="vue-archives-item--metadata").find("span")
        date_string = span.text.replace("Date: ", "")
        date = dt.datetime.strptime(date_string, '%B %d, %Y').date()

        if start_date <= date <= end_date:
            a = li.find("a")
            articles_list.append({"Date": date, "Headline": a.text, "URL": f"{team_data['base_url']}{a['href']}"})

    return DataFrame(articles_list)
