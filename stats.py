import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
from utils import initialize_web_driver

def download_stats(team_data: dict[str, str], years: list[int], output_folder_path: str) -> None:
    """
    Downloads a team's season stats to a PDF file.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        years (list[int]): Years for which to print stats for.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    st.write(f"Downloading {team_data['name']}'s stats...")

    if (team_data["name"] == "Penn State"):
        download_penn_state_stats(team_data, output_folder_path)
    else:
        download_other_team_stats(team_data, years, output_folder_path)

    st.write(f"Finished downloading {team_data['name']}'s stats!")

def download_penn_state_stats(team_data: dict[str, str], output_folder_path: str) -> None:
    """
    Downloads Penn State's stats PDF files.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    url = f"https://{team_data['hostname']}/sports/mens-soccer"
    stats_url = find_penn_state_stats_pdf_url(url)

    response = requests.get(stats_url)

    if (response.status_code == 404):
        return

    output_path = f"{output_folder_path}/{team_data['abbreviation']} Stats.pdf"
    with open(output_path, 'wb') as file:
        file.write(response.content)

def download_other_team_stats(team_data: dict[str, str], years: list[int], output_folder_path: str) -> None:
    """
    Downloads the team's stats PDF files.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        years (list[int]): Years for which to print stats for.
        output_folder_path (str): Path to the output folder.

    Returns:
        None
    """
    for year in years:
        stats_url = construct_stats_url(team_data, year)
        response = requests.get(stats_url)

        if (response.status_code == 404):
            st.write(f"Unable to find stats for {year} with the following URL: {stats_url}.")
            st.write("Continuing...")
            continue

        output_path = f"{output_folder_path}/{team_data['abbreviation']} {year} Stats.pdf"
        with open(output_path, 'wb') as file:
            file.write(response.content)

def construct_stats_url(team_data: dict[str, str], year: int) -> str:
    """
    Construct a URL to find the stats PDF.

    Args:
        team_data (dict[str, str]): Dictionary containing team data.
        year (int): The year in which to generate the URL for.

    Returns:
        str: The URL for the stats PDF.
    """
    base_url = "https://dxbhsrqyrr690.cloudfront.net/sidearm.nextgen.sites" if (team_data["base_website_type"] == 1) else "https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites"
    return f"{base_url}/{team_data['hostname']}/stats/msoc/{year}/pdf/cume.pdf"

def find_penn_state_stats_pdf_url(url: str) -> str:
    """
    Get the URLs of the stats PDF for Penn State.

    Args:
        url (str): The base URL of Penn State's Mens Soccer.

    Returns:
        str: The URL of the stats PDF for Penn State.
    """
    driver = initialize_web_driver()
    driver.get(url)
    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")
    stats_page_url = extract_penn_state_stats_page_url(doc)

    driver.get(stats_page_url)
    time.sleep(1)

    doc = BeautifulSoup(driver.page_source, "lxml")
    stats_pdf_url = extract_stats_pdf_url(doc)

    driver.quit()
    return stats_pdf_url

def extract_penn_state_stats_page_url(doc: BeautifulSoup) -> str:
    """
    Get the URL of the page containing the embedded stats PDF.

    Args:
        doc (BeautifulSoup): The page content of the base page URL.

    Returns:
        str: The URL of the page containing the embedded stats PDF.
    """
    ul = doc.find("ul", class_="menu menu--level-0 menu--sport")
    li = ul.find_all("li", class_="menu-item menu-item--static-url menu-item--show-on-mobile menu-item--show-on-desktop menu__item")[5]
    return li.find("a")["href"]

def extract_stats_pdf_url(doc: BeautifulSoup) -> str:
    """
    Get the URL of the stats PDF for Penn State.

    Args:
        doc (BeautifulSoup): The page content of the page that containing embedded stats PDF.

    Returns:
        str: The URL of the stats PDF for Penn State.
    """
    div = doc.find("div", class_="container pdf-block__container")
    return div.find("a")["href"]
