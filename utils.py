import tkinter as tk
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import Tag
from tkinter import filedialog

def select_output_folder() -> str:
    """
    Opens the file dialog, allowing users to select an output folder.

    Returns:
        str: The full path to the selected folder.
    """
    os.environ['TK_SILENCE_DEPRECATION'] = '1'

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(parent=root)
    root.destroy()

    return folder_path

def initialize_web_driver() -> webdriver.Chrome:
    """
    Initializes a new web driver instance.

    Returns:
        WebDriver: A new web driver instance.
    """
    service = Service(executable_path="/usr/local/bin/chromedriver")

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    return webdriver.Chrome(service=service, options=chrome_options)

def sanitize_html(doc: Tag | None) -> str:
    """
    Removes any embedded tweets and advertisement content from HTML string.

    Args:
        doc (Tag | None): BeautifulSoup Tag with the unsanitized HTML.

    Returns:
        str: The sanitized HTML table as a string.
    """
    if not doc:
        return ""

    for tweet in doc.find_all("div", class_="twitter-tweet twitter-tweet-rendered"):
        tweet.extract()

    for table_row in doc.find_all("tr"):
        if ("class" in table_row) and ("s-table-body__row--ad" in table_row["class"]):
            table_row.extract()

    return str(doc)
