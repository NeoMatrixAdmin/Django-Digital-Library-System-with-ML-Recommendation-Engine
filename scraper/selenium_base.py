# scraper/selenium_base.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
import random
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from selenium.common.exceptions import WebDriverException, TimeoutException

logger = logging.getLogger(__name__)

SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")


# -------------------------------
# LOCAL DRIVER (NOT USED IN DOCKER)
# -------------------------------
def _make_local_driver(headless=True, window_size="1920,1080"):
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={window_size}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass

    return driver


# -------------------------------
# REMOTE DRIVER (Selenium Grid)
# -------------------------------
def _make_remote_driver(remote_url, headless=True, window_size="1920,1080"):
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--window-size={window_size}")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    # Modern Selenium capability setup
    options.set_capability("browserName", "chrome")
    options.set_capability("platformName", "Linux")

    driver = webdriver.Remote(
        command_executor=remote_url,
        options=options  # <-- CORRECT for Selenium 4.38+
    )

    return driver


# -------------------------------
# MAIN FUNCTION TO GET DRIVER
# -------------------------------
def get_driver(headless=True, window_size="1920,1080"):
    if SELENIUM_REMOTE_URL:
        logger.info("Using remote Selenium at %s", SELENIUM_REMOTE_URL)
        return _make_remote_driver(SELENIUM_REMOTE_URL, headless=headless, window_size=window_size)

    return _make_local_driver(headless=headless, window_size=window_size)


# -------------------------------
# UTILITIES
# -------------------------------
def polite_sleep(min_s=1.0, max_s=2.5):
    time.sleep(random.uniform(min_s, max_s))


retry_on_selenium = retry(
    retry=retry_if_exception_type((WebDriverException, TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True
)
