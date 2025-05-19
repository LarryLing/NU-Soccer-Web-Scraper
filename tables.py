import time
import pdfkit
import pandas as pd
import streamlit as st
from io import StringIO
from bs4 import BeautifulSoup
from pdfkit.configuration import Configuration
from utils import initialize_web_driver, sanitize_html

def download_tables(team_name: str, table_type: str, url: str, output_file_path: str, ignored_columns: list[str], pdfkit_config: Configuration) -> None:
    """
    Downloads the roster page to a PDF file.

    Args:
        team_name (str): Name of the team.
        table_type (str): Type of table(s) to download. Either "roster" or "schedule".
        url (str): URL of the site.
        output_file_path (str): Path to the downloaded PDF file.
        ignored_columns (list[str]): List of columns to ignore.
        pdfkit_config: (Configuration): Configuration object for pdfkit.

    Returns:
        None
    """
    st.write(f"Downloading {team_name}'s {table_type}...")

    with initialize_web_driver() as driver:
        driver.get(url)
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

    extracted_tables = extract_tables(soup, ignored_columns)

    full_html = build_html_document(soup.find("title"), extracted_tables)

    pdfkit.from_string(full_html, output_file_path, configuration=pdfkit_config)
    st.write(f"Finished downloading {team_name}'s {table_type}!")

def extract_tables(soup: BeautifulSoup, ignored_columns: list[str]) -> list[str]:
    """
    Extracts and processes tables from the HTML document.

    Args:
        soup (BeautifulSoup): Parsed HTML document.
        ignored_columns (list[str]): List of columns to ignore.

    Returns:
        list[str]: List of HTML strings containing tables.
    """
    tables = []
    for table in soup(["table"]):
        if (not table.find("thead")):
            continue

        sanitized_table = sanitize_html(table)
        dataframe = pd.read_html(StringIO(sanitized_table))[0]
        dataframe = dataframe.drop(columns=ignored_columns, errors="ignore")
        dataframe.fillna("", inplace=True)

        tables.append(dataframe.to_html(index=False))

    return tables

def build_html_document(title: str, html_tables: list[str]) -> str:
    """
    Initializes a blank HTML page and inserts HTML table content.

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
    document = BeautifulSoup(html, "lxml")

    main = document.find("main")

    for html_table in html_tables:
        div_tag = document.new_tag("div")
        main.append(div_tag)

        table = BeautifulSoup(html_table, "lxml")
        main.append(table)

    return str(document)
