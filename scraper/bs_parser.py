# scraper/selenium_base.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import time
import random
from urllib.parse import urlparse
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from selenium.common.exceptions import WebDriverException, TimeoutException

logger = logging.getLogger(__name__)

# If SELENIUM_REMOTE_URL is set (recommended for docker-compose), use Remote WebDriver.
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")

def _make_local_driver(headless=True, window_size="1920,1080"):
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={window_size}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # randomize UA if available externally; keep default otherwise
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass
    return driver

def _make_remote_driver(remote_url=SELENIUM_REMOTE_URL, headless=True, window_size="1920,1080"):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={window_size}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    caps = DesiredCapabilities.CHROME.copy()
    caps.update(options.to_capabilities())
    driver = webdriver.Remote(command_executor=remote_url, desired_capabilities=caps)
    return driver

def get_driver(headless=True, window_size="1920,1080"):
    """
    Return a webdriver instance.
    If SELENIUM_REMOTE_URL env var present, use remote driver (recommended for Docker).
    """
    if SELENIUM_REMOTE_URL:
        logger.info("Using remote selenium at %s", SELENIUM_REMOTE_URL)
        return _make_remote_driver(remote_url=SELENIUM_REMOTE_URL, headless=headless, window_size=window_size)
    return _make_local_driver(headless=headless, window_size=window_size)

def polite_sleep(min_s=1.0, max_s=2.5):
    time.sleep(random.uniform(min_s, max_s))

# Retry decorator for common transient Selenium exceptions
retry_on_selenium = retry(
    retry=retry_if_exception_type((WebDriverException, TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True
)
