from django.core.management.base import BaseCommand
from catalog.models import Book
import requests
from time import sleep


EDITION_API = "https://openlibrary.org/works/{work_id}/editions.json?limit=50"


class Command(BaseCommand):
    help = "Scrape REAL ISBN-10 and ISBN-13 from OpenLibrary Edition API"

    def handle(self, *args, **options):
        books = Book.objects.filter(real_isbn__isnull=True)

        if not books.exists():
            self.stdout.write(self.style.SUCCESS("No books need ISBN scraping."))
            return

        self.stdout.write(self.style.WARNING(f"Scanning {books.count()} books...\n"))

        for book in books:
            work_id = getattr(book, "ol_work_id", None)

            if not work_id:
                self.stdout.write(self.style.ERROR(f"No work_id for {book.title}, skipping."))
                continue

            url = EDITION_API.format(work_id=work_id)
            res = requests.get(url)

            if res.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Failed API for {book.title}"))
                continue

            data = res.json()
            editions = data.get("entries", [])

            isbn_found = None

            for ed in editions:
                isbn_list = ed.get("isbn_13") or ed.get("isbn_10")

                if isbn_list:
                    isbn_found = isbn_list[0]
                    break

            if isbn_found:
                book.real_isbn = isbn_found
                book.save()
                self.stdout.write(self.style.SUCCESS(
                    f"{book.title} → {isbn_found}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"{book.title} → No ISBN found"
                ))

            sleep(0.2)  # respect API

        self.stdout.write(self.style.SUCCESS("\nDone scraping all ISBNs!"))
