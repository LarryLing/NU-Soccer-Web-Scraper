import base64
import time
import streamlit as st
from selenium.webdriver.common.print_page_options import PrintOptions
from utils import initialize_web_driver

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

    print_from_page = [
        "Maryland",
        "Rutgers"
        "Washington",
        "Wisconsin",
        "Penn State",
        "UIC",
        "Loyola",
        "Northern Illinois",
        "Chicago State"
    ]

    click_to_print = [
        "Northwestern",
        "Indiana",
        "Ohio State",
        "UCLA",
        "Michigan State",
        "Michigan",
        "DePaul"
    ]

    if team_name in print_from_page:
        print_options = PrintOptions()
        pdf = driver.print_page(print_options)
        bytes = base64.b64decode(pdf)

        with open(output_file_path, "wb") as f:
            f.write(bytes)

        driver.quit()
    elif team_name in click_to_print:
        pass

    st.write(f"Finished downloading {team_name}'s schedule!")
