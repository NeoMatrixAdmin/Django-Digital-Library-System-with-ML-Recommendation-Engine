from django.core.management.base import BaseCommand
from scraper.selenium_base import get_driver
import time

DJANGO_URL = "http://web:8000"     # IMPORTANT: Selenium must use container hostname

class Command(BaseCommand):
    help = "Tests Selenium → Django site UI connectivity."

    def handle(self, *args, **options):
        self.stdout.write("Starting Selenium UI test...")

        try:
            driver = get_driver(headless=True)
            driver.get(DJANGO_URL)
            time.sleep(2)

            title = driver.title or "(no title)"
            self.stdout.write(self.style.SUCCESS(
                f"Loaded homepage successfully! Title: {title}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Selenium UI test failed: {e}"
            ))

        finally:
            try:
                driver.quit()
            except:
                pass
