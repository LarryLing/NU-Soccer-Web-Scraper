import base64
import zipfile
from io import BytesIO

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


def print_pdf_to_zipfile(driver: webdriver.Chrome, filename: str, zip_buffer: BytesIO) -> None:
    """
    Performs Selenium's print function and saves the PDF bytes to the zip file.

    Args:
        driver: Selenium webdriver instance.
        filename: The filename of the PDF file.
        zip_buffer: The buffer to write the PDF file to.

    Returns:
        None
    """
    try:
        print(driver.current_url)
        print_options = PrintOptions()
        pdf = driver.print_page(print_options)
        pdf_bytes = base64.b64decode(pdf)

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(filename, pdf_bytes)

        st.write(f"**{filename}** Downloaded!")
    except InvalidArgumentException as e:
        st.write(f"**{filename}** Failed!  \nReason: {e}")


def response_pdf_to_zipfile(pdf_url: str, filename: str, zip_buffer: BytesIO) -> None:
    """
    Sends an HTTP GET request for PDF bytes and writes them to a zip file.

    Args:
        pdf_url: The URL of the PDF file.
        filename: The filename of the PDF file.
        zip_buffer: The buffer to write the PDF file to.

    Returns:
        None
    """
    response = requests.get(pdf_url)
    if response.status_code == 404:
        st.write(
            f"**{filename}** Failed!  \nReason: Found a PDF URL, but it doesn't link to an existing file.")
        return

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(filename, response.content)

    st.write(f"**{filename}** Downloaded!")
