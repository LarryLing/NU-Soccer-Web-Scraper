import tkinter as tk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import ChromiumOptions
from bs4 import Tag
from tkinter import filedialog

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

def sanitize_html(doc: Tag | None) -> str:
    """
    Removes any embedded tweets and advertisement content from HTML string.

    Args:
        doc (Tag | None): BeautifulSoup Tag with the unsanitized HTML.

    Returns:
        str: The sanitized HTML table as a string.
    """
    if (not doc):
        return ""

    for tweet in doc.find_all("div", class_="twitter-tweet twitter-tweet-rendered"):
        tweet.extract()

    tables = doc.find_all("table")
    for table in tables:
        table_rows = table(["tr"])
        for table_row in table_rows:
            if ("skip ad" in table_row.get_text().lower()):
                table_row.extract()

    return str(doc)
