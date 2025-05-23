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

    driver = initialize_web_driver()

    pdf_url_in_embed = [
        "Northwestern",
        "Indiana",
        "Ohio State",
        "UCLA",
        "Michigan State",
        "Michigan",
        "DePaul"
    ]

    pdf_url_in_object = [
        "Maryland",
        "Washington",
        "Rutgers",
        "Wisconsin",
        "Penn State",
        "UIC",
        "Loyola",
        "Northern Illinois",
        "Chicago State"
    ]

    for year in years:
        if (team_data["name"] == "Penn State") or (team_data["name"] == "Northern Illinois"):
            driver.get(team_data["stats_url"][str(year)])
            time.sleep(1)
        else:
            driver.get(team_data["stats_url"].format(year))
            time.sleep(1)

        doc = BeautifulSoup(driver.page_source, "lxml")

        output_path = f"{output_folder_path}/{team_data['abbreviation']} {year} Stats.pdf"

        if team_data["name"] in pdf_url_in_embed:
            embed_tag = doc.find("embed")
            if embed_tag:
                download_pdf(embed_tag["src"], output_path)
                continue
        elif team_data["name"] in pdf_url_in_object:
            object_tag = doc.find("object")
            if object_tag:
                download_pdf(object_tag["data"], output_path)
                continue

        st.write(f"Could not find stats for the year {year}, continuing...")

    driver.quit()

    st.write(f"Finished downloading {team_data['name']}'s stats!")

def download_pdf(pdf_url: str, output_path: str) -> None:
    response = requests.get(pdf_url)

    if response.status_code == 404:
        st.write(f"{pdf_url} does not link to an existing PDF, continuing...")
        return

    with open(output_path, 'wb') as file:
        file.write(response.content)
