import time
import pdfkit
import pandas as pd
import streamlit as st
import datetime as dt
from io import StringIO
from pandas import DataFrame
from bs4 import BeautifulSoup, Tag
from pdfkit.configuration import Configuration
from utils import initialize_web_driver, sanitize_html

def fetch_articles(team_data: dict[str, str], date_range: tuple[dt.date, dt.date]) -> DataFrame:
    """
    Fetches a team's articles, returning their headlines and URLs.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        date_range (tuple[date, date]): Range of dates to fetch articles from.

    Returns:
        DataFrame: DataFrame of articles to download containing the date posted, headline, and URL.
    """
    st.write(f"Fetching {team_data['name']}'s articles...")

    with initialize_web_driver() as driver:
        driver.get(team_data["articles_url"])
        time.sleep(1)
        doc = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

    article_display_type = team_data["article_display_type"]
    if (article_display_type == "table"):
        table = doc.find("table")
        articles_df = scan_table_for_articles(team_data, table, date_range)
    elif (article_display_type == "list"):
        ul = doc.find("div", class_="vue-archives-stories").find("ul")
        articles_df = scan_ul_for_articles(team_data, ul, date_range)

    st.write(f"Finished fetching {team_data['name']}'s articles!")
    return articles_df

def download_articles(team_data: dict[str, str], articles: DataFrame, output_folder_path: str, pdfkit_config: Configuration) -> None:
    """
    Downloads selected articles into respective PDF files. Articles whose URLs link to a website that does not share
    the same hostname will be printed out as a Streamlit DataFrame instance.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        articles (DataFrame): DataFrame of articles to download containing the date posted, headline, and URL.
        output_folder_path (str): Path to the output folder.
        pdfkit_config: (Configuration): Configuration object for pdfkit.

    Returns:
        None
    """
    st.write("Downloading selected articles...")

    with initialize_web_driver() as driver:
        undownloaded_articles = articles.iloc[0:0].copy()
        for _, row in articles.iterrows():
            driver.get(row["URL"])
            time.sleep(1)

            if (team_data["hostname"] not in driver.current_url):
                undownloaded_articles.loc[len(undownloaded_articles)] = row
                continue

            doc = BeautifulSoup(driver.page_source, "lxml")
            content = sanitize_html(doc.find("div", id="storyPageContentBody"))
            full_html = build_html_document(row["Headline"], content)
            output_file_path = f"{output_folder_path}/{row['Headline']}.pdf"
            pdfkit.from_string(full_html, output_file_path, configuration=pdfkit_config)

    if (not undownloaded_articles.empty):
        display_undownloaded_articles(undownloaded_articles)

    st.write("Finished downloading selected articles!")

def display_undownloaded_articles(undownloaded_articles: DataFrame) -> None:
    """
    Display undownloaded articles in a Streamlit dataframe.

    Args:
        undownloaded_articles (DataFrame): Articles that could not be downloaded.

    Returns:
        None
    """
    column_configuration = {
        "Date": None,
        "Posted": None,
        "Headline": st.column_config.TextColumn(width="medium"),
        "URL": st.column_config.LinkColumn(width="medium"),
    }

    st.write("We could not download the following articles. Please navigate to the URL and download them manually.")
    st.dataframe(
        data=undownloaded_articles,
        hide_index=True,
        column_config=column_configuration
    )

def scan_table_for_articles(team_data: dict[str, str], table: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    start_date, end_date = date_range
    sanitized_table = sanitize_html(table)

    links = [f"https://{team_data['hostname']}{a['href']}" for a in table.find_all("a") if (a["href"] != "#")]

    dataframe = pd.read_html(StringIO(sanitized_table))[0].drop(columns=["Sport", "Category"], errors="ignore")
    dataframe.drop(dataframe.columns[dataframe.columns.str.contains('Unnamed', case=False)], axis=1, inplace=True)
    dataframe["URL"] = links

    if ("Posted" in dataframe.columns):
        dataframe["Date"] = pd.to_datetime(dataframe["Posted"], format='%m/%d/%Y')
        dataframe.drop(columns=["Posted"], inplace=True)
    elif ("Date" in dataframe.columns):
        dataframe["Date"] = pd.to_datetime(dataframe["Date"], format='%B %d, %Y')

    if ("Title" in dataframe.columns):
        dataframe.rename(columns={"Title": "Headline"}, inplace=True)

    return dataframe[(dataframe["Date"].dt.date >= start_date) & (dataframe["Date"].dt.date <= end_date)]

def scan_ul_for_articles(team_data: dict[str, str], ul: Tag, date_range: tuple[dt.date, dt.date]) -> DataFrame:
    start_date, end_date = date_range
    sanitized_ul = sanitize_html(ul)
    sanitized_ul = BeautifulSoup(sanitized_ul, "lxml")

    articles_list = []
    for li in sanitized_ul.find_all("li", class_="vue-archives-item flex"):
        date_string = li.find("span").text.replace("Date: ", "")
        date = dt.datetime.strptime(date_string, '%B %d, %Y').date()

        if (start_date <= date <= end_date):
            a = li.find("a")
            articles_list.append({"Date": date, "Headline": a.text, "URL": f"https://{team_data['hostname']}{a['href']}"})

    return DataFrame(articles_list)

def build_html_document(title: str, content_string: str) -> str:
    """
    Initializes a blank HTML page and inserts article content.

    Args:
        title (str): Title for the HTML document.
        content_string (str): HTML string containing the article content.

    Returns:
        str: A string representation of the full .HTML document.
    """
    html_template = f"""
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
    doc = BeautifulSoup(html_template, "lxml")
    main = doc.find("main")
    content = BeautifulSoup(content_string, "lxml")
    main.append(content)

    return str(doc)
