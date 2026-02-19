# scraper/extract_real_isbn.py

import time
import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from scraper.selenium_base import get_driver, polite_sleep
from catalog.models import Book

logger = logging.getLogger(__name__)


def extract_real_isbn_from_html(html):
    """
    Parse ISBN from the edition-list page HTML using BeautifulSoup.
    We try multiple possible labels because OpenLibrary is not consistent.
    """
    soup = BeautifulSoup(html, "html.parser")

    possible_labels = [
        "ISBN 10:",
        "ISBN 13:",
        "ISBN:",
    ]

    # Look for <td> or <div> containing ISBN labels
    for label in possible_labels:
        cell = soup.find(string=lambda t: t and label in t)
        if cell:
            # Parent <tr> or <div> may contain the actual value
            parent = cell.parent
            text = parent.get_text(strip=True)
            # Extract digits only (ISBN10 or ISBN13)
            import re
            digits = re.sub(r"[^0-9Xx]", "", text)
            if 10 <= len(digits) <= 13:
                return digits

    return None


def fetch_edition_page_html(driver, url):
    """
    Navigate Selenium to the OpenLibrary editions page and return the HTML.
    """
    logger.info(f"Fetching edition page: {url}")
    driver.get(url)
    polite_sleep(1.5, 2.5)

    return driver.page_source


def process_single_book(book: Book, save=True):
    """
    Given a Book object, determine the correct OpenLibrary 'work key'
    from its internal ISBN, download edition list, parse real ISBN,
    and optionally save.
    Returns: (book, real_isbn or None)
    """

    logger.info(f"Processing book id={book.pk} title='{book.title}'")

    # Internal ISBN format:  "OLISBN-OL15839737W-b4a3a3"
    internal = book.isbn
    if not internal.startswith("OLISBN-"):
        logger.warning(f"Book {book.pk}: Internal ISBN format unexpected: {internal}")
        return book, None

    try:
        parts = internal.split("-")
        work_key = parts[1]  # OL15839737W
    except Exception:
        logger.error(f"Could not parse work key from internal ISBN: {internal}")
        return book, None

    edition_url = f"https://openlibrary.org/works/{work_key}/editions"

    driver = get_driver(headless=True)

    try:
        html = fetch_edition_page_html(driver, edition_url)
        real = extract_real_isbn_from_html(html)

        if real and save:
            book.real_isbn = real
            book.save(update_fields=["real_isbn"])

        return book, real

    except Exception as e:
        logger.error(f"Error while scraping book {book.pk}: {e}")
        return book, None

    finally:
        try:
            driver.quit()
        except:
            pass
