import time

import streamlit as st
from bs4 import BeautifulSoup
from selenium.common import TimeoutException

from utils import initialize_web_driver, download_pdf


def download_stats(team_data: dict, years: list[int], output_folder_path: str) -> None:
    """
    Downloads a team's season stats to a PDF file.

    Args:
        team_data: Dictionary containing team data.
        years: Years for which to print stats for.
        output_folder_path: Path to the output folder.

    Returns:
        None
    """
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
        "Loyola Chicago",
        "Northern Illinois",
        "Chicago State"
    ]

    for year in years:
        output_file_path = f"{output_folder_path}/{team_data['abbreviation']} {year} Stats.pdf"

        try:
            if (team_data["name"] == "Penn State") or (team_data["name"] == "Northern Illinois"):
                driver.get(team_data["stats_url"][str(year)])
            else:
                driver.get(team_data["stats_url"].format(year))

            time.sleep(1)
        except TimeoutException as e:
            st.write(f"**{output_file_path.split('/')[-1]}** Failed!  \nReason: {e}")
            continue

        doc = BeautifulSoup(driver.page_source, "lxml")

        if team_data["name"] in pdf_url_in_embed:
            embed_tag = doc.find("embed")
            if embed_tag:
                download_pdf(embed_tag["src"], output_file_path)
                continue
        elif team_data["name"] in pdf_url_in_object:
            object_tag = doc.find("object")
            if object_tag:
                download_pdf(object_tag["data"], output_file_path)
                continue

        st.write(f"**{output_file_path.split('/')[-1]}** Failed!  \nReason: Could not find the PDF url.")

    driver.quit()
