import base64
import time
import os
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from selenium.webdriver.common.print_page_options import PrintOptions
from utils import initialize_web_driver, sanitize_html

def download_schedule(team_name: str, url: str, output_file_path: str) -> None:
    """
    Downloads the schedule page to a PDF file.

    Args:
        team_name (str): Name of the team.
        url (str): URL of the site.
        output_file_path (str): Path to the downloaded PDF file.

    Returns:
        None
    """
    st.write(f"Downloading {team_name}'s schedule...")

    driver = initialize_web_driver()

    script = """
        let removed = document.getElementById('divSatisfiChat'); 
        if (removed) removed.parentNode.removeChild(removed);

        removed = document.getElementById('transcend-consent-manager'); 
        if (removed) removed.parentNode.removeChild(removed);

        removed = document.getElementById('termly-code-snippet-support'); 
        if (removed) removed.parentNode.removeChild(removed);
    """

    driver.get(url)
    time.sleep(1)

    driver.execute_script(script)

    scrape_schedule = [
        "Northwestern",
        "Indiana",
        "Ohio State",
        "UCLA",
        "Michigan State",
        "Michigan",
        "DePaul"
    ]

    if team_name in scrape_schedule:
        soup = BeautifulSoup(driver.page_source, "lxml")

        extracted_tables = extract_tables(soup)

        full_html = build_html_document(soup.find("title").text, extracted_tables)

        with open("temp.html", "w") as f:
            f.write(full_html)

        driver.get(f"file:///{os.getcwd()}/temp.html")

    print_options = PrintOptions()
    pdf = driver.print_page(print_options)
    bytes = base64.b64decode(pdf)

    with open(output_file_path, "wb") as f:
        f.write(bytes)

    driver.quit()

    st.write(f"Finished downloading {team_name}'s schedule!")

def extract_tables(soup: BeautifulSoup) -> list[str]:
    """
    Extracts and processes tables from the HTML document.

    Args:
        soup (BeautifulSoup): Parsed HTML document.

    Returns:
        list[str]: List of HTML strings containing tables.
    """
    sanitized_html = sanitize_html(soup)
    dataframes = pd.read_html(sanitized_html)
    for dataframe in dataframes:
        dataframe.fillna("", inplace=True)

    return [dataframe.to_html(index=False) for dataframe in dataframes]

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
