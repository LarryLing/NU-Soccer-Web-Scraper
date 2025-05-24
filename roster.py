import time
from io import BytesIO

import streamlit as st
from selenium.common import TimeoutException

from utils import initialize_web_driver, print_pdf_to_zipfile


def download_roster(url: str, filename: str, zip_buffer: BytesIO) -> None:
    """
    Downloads the roster page to a PDF file.

    Args:
        url: URL of the site.
        filename: Name of the downloaded file.
        zip_buffer: Bytes buffer containing the roster page.

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

        print_pdf_to_zipfile(driver, filename, zip_buffer)
    except TimeoutException as e:
        st.write(f"**{filename}** Failed!  \nReason: {e}")
    finally:
        driver.quit()
