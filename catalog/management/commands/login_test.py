from django.core.management.base import BaseCommand
from scraper.selenium_base import get_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

DJANGO_URL = "http://web:8000"

USERNAME = "admin"       # set your superuser here
PASSWORD = "Achal@07"

class Command(BaseCommand):
    help = "Tests login functionality using Selenium."

    def handle(self, *args, **options):
        self.stdout.write("Starting Selenium login test...")

        try:
            driver = get_driver(headless=True)
            wait = WebDriverWait(driver, 10)

            # 1️⃣ Open homepage
            driver.get(DJANGO_URL)

            # 2️⃣ Try clicking navbar toggler (if visible)
            try:
                toggler = driver.find_element(By.CLASS_NAME, "navbar-toggler")
                toggler.click()
                time.sleep(1)
            except Exception:
                pass  # toggler not visible means large-screen mode; ok.

            # 3️⃣ Now click LOGIN link
            login_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Login"))
            )
            login_link.click()

            # 4️⃣ Wait for login page
            wait.until(EC.visibility_of_element_located((By.NAME, "login")))

            # 5️⃣ Fill username
            username_input = driver.find_element(By.NAME, "login")
            username_input.clear()
            username_input.send_keys(USERNAME)

            # 6️⃣ Fill password
            password_input = driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(PASSWORD)

            # 7️⃣ Click Login button
            submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            submit_button.click()

            # 8️⃣ Confirm login succeeded → we expect a Logout link now
            wait.until(EC.visibility_of_element_located((By.LINK_TEXT, "Logout")))

            self.stdout.write(self.style.SUCCESS(
                "Login test passed! Successfully logged in."
            ))
        except Exception as e:
            # Save screenshot for debugging
            try:
                driver.save_screenshot("/app/selenium_error.png")
            except:
                pass

            self.stdout.write(self.style.ERROR(
                f"Login test failed: {e}. Screenshot saved to selenium_error.png"
            ))

