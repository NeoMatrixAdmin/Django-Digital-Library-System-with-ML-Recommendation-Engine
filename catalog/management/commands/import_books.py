import requests
from django.core.management.base import BaseCommand
from catalog.models import Book, Author, Genre, Language, BookInstance
from time import sleep

OPENLIBRARY_SUBJECT_URL = "https://openlibrary.org/subjects/{subject}.json?limit={limit}"


class Command(BaseCommand):
    help = "Import books from OpenLibrary by subject"

    def add_arguments(self, parser):
        parser.add_argument(
            '--subject',
            type=str,
            required=True,
            help='Book subject, e.g. fantasy, romance, science_fiction, self_help'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='How many books to fetch'
        )

    def handle(self, *args, **options):
        subject = options['subject']
        limit = options['limit']

        url = OPENLIBRARY_SUBJECT_URL.format(subject=subject, limit=limit)
        self.stdout.write(self.style.WARNING(f"Fetching books for subject: {subject}"))

        response = requests.get(url)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR("Failed to fetch data from OpenLibrary"))
            return

        data = response.json()
        works = data.get("works", [])

        count = 0

        # Default language
        language_obj, _ = Language.objects.get_or_create(name="English")

        for work in works:
            title = work.get("title", "Unknown Title")

            # Work ID (OL45804W)
            work_key = work["key"].split("/")[-1]

            # Summary handling
            summary = work.get("description", "")
            if isinstance(summary, dict):
                summary = summary.get("value", "")

            # Fake fallback ISBN (internal purpose)
            fake_internal_isbn = f"OLISBN-{work_key}"

            # Extract author
            authors = work.get("authors", [])
            author_obj = None
            if authors:
                name = authors[0].get("name", "")
                if name:
                    first, *rest = name.split(" ")
                    last = " ".join(rest) if rest else ""
                    author_obj, _ = Author.objects.get_or_create(
                        first_name=first,
                        last_name=last or "Unknown"
                    )

            # Create or update book
            book, created = Book.objects.get_or_create(
                title=title,
                defaults={
                    "summary": summary,
                    "isbn": fake_internal_isbn,
                    "language": language_obj,
                    "ol_work_id": work_key,
                    "author": author_obj,
                }
            )

            # If book existed but missing author
            if not created and author_obj and not book.author:
                book.author = author_obj
                book.save()

            # Store Work ID
            if hasattr(book, "ol_work_id") and not book.ol_work_id:
                book.ol_work_id = work_key
                book.save()

            # Handle genres
            work_subjects = work.get("subject", []) or work.get("subjects", [])
            for sub in work_subjects[:5]:
                genre_obj, _ = Genre.objects.get_or_create(name=sub)
                book.genre.add(genre_obj)

            # ⭐ AUTO-CREATE AT LEAST 1 COPY
            if BookInstance.objects.filter(book=book).count() == 0:
                BookInstance.objects.create(
                    book=book,
                    imprint="Imported Copy",
                    status="a"   # Available
                )

            count += 1
            self.stdout.write(f"Imported: {title}")

            sleep(0.1)

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully imported {count} books!"))
