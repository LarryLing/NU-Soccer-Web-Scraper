import time

import streamlit as st
from selenium.common import TimeoutException

from utils import initialize_web_driver, print_to_pdf


def download_roster(url: str, output_file_path: str) -> None:
    """
    Downloads the roster page to a PDF file.

    Args:
        url: URL of the site.
        output_file_path: Path to the downloaded PDF file.

    Returns:
        None
    """
    driver = initialize_web_driver()

    script = """
        let removed = document.getElementById('divSatisfiChat'); 
        if (removed) removed.parentNode.removeChild(removed);

        removed = document.getElementById('transcend-consent-manager'); 
        if (removed) removed.parentNode.removeChild(removed);

        removed = document.getElementById('termly-code-snippet-support'); 
        if (removed) removed.parentNode.removeChild(removed);
    """

    try:
        driver.get(url)
        time.sleep(1)

        driver.execute_script(script)

        print_to_pdf(driver, output_file_path)
    except TimeoutException as e:
        st.write(f"**{output_file_path.split('/')[-1]}** Failed!  \nReason: {e}")
    finally:
        driver.quit()
