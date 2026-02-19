# catalog/management/commands/scrape_real_isbns.py
from django.core.management.base import BaseCommand
from catalog.models import Book
from scraper.extract_real_isbn import process_single_book
from django.db import transaction
import time

class Command(BaseCommand):
    help = "Scrape OpenLibrary work/edition pages and fill Book.real_isbn (for preview)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="How many books to process in this run")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes to DB")

    def handle(self, *args, **options):
        limit = options['limit']
        dry = options['dry_run']

        qs = Book.objects.filter(real_isbn__isnull=True).exclude(isbn__isnull=True)[:limit]
        total = qs.count()
        self.stdout.write(f"Found {total} books to process (limit={limit}).")

        processed = 0
        for book in qs:
            self.stdout.write(f"Processing Book id={book.pk} title={book.title} ...", ending="")
            processed += 1
            b, real = process_single_book(book, save=not dry)
            if real:
                self.stdout.write(self.style.SUCCESS(f" → Found ISBN: {real}"))
            else:
                self.stdout.write(self.style.WARNING(" → No ISBN found"))
            # polite pause between books
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS(f"Done. Processed {processed} books."))
