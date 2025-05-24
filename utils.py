import base64

import requests
import streamlit as st
from bs4 import Tag
from selenium import webdriver
from selenium.common import InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.print_page_options import PrintOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType


def initialize_web_driver() -> webdriver.Chrome:
    """
    Initializes a new web driver instance.

    Returns:
        A new web driver instance.
    """
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    return webdriver.Chrome(service=service, options=chrome_options)


def sanitize_html(doc: Tag | None) -> str:
    """
    Removes any embedded tweets and advertisement content from HTML string.

    Args:
        doc: BeautifulSoup Tag with the unsanitized HTML.

    Returns:
        The sanitized HTML table as a string.
    """
    if not doc:
        return ""

    for table_row in doc.find_all("tr"):
        if ("class" in table_row.attrs) and ("s-table-body__row--ad" in table_row["class"]):
            table_row.extract()

    return str(doc)


def download_pdf(pdf_url: str, output_file_path: str) -> None:
    """
    Downloads a PDF file from a HTTP request with.

    Args:
        pdf_url: The URL of the PDF file.
        output_file_path: The path to the output file.

    Returns:
        None
    """
    response = requests.get(pdf_url)
    if response.status_code == 404:
        st.write(
            f"**{output_file_path.split('/')[-1]}** Failed!  \nReason: Found a PDF URL, but it doesn't link to an existing file.")
        return

    with open(output_file_path, 'wb') as file:
        file.write(response.content)

    st.write(f"**{output_file_path.split('/')[-1]}** Downloaded!")


def print_to_pdf(driver: webdriver.Chrome, output_file_path: str) -> None:
    """
    Downloads a PDF file  using Selenium's print function.

    Args:
        driver: The web driver instance.
        output_file_path: The path to the output file.

    Returns:
        None
    """
    try:
        print_options = PrintOptions()
        pdf = driver.print_page(print_options)
        pdf_bytes = base64.b64decode(pdf)

        with open(output_file_path, "wb") as f:
            f.write(pdf_bytes)

        st.write(f"**{output_file_path.split('/')[-1]}** Downloaded!")
    except InvalidArgumentException as e:
        st.write(f"**{output_file_path.split('/')[-1]}** Failed!  \nReason: {e}")
