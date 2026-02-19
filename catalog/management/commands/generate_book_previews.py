# catalog/management/commands/generate_book_previews.py
from django.core.management.base import BaseCommand
from catalog.models import Book, BookPreview
from scraper.preview_generator import fetch_openlibrary_by_isbn, openlibrary_cover_from_data, fetch_openlibrary_work, call_openai_generate_preview
import time

class Command(BaseCommand):
    help = "Generate or update BookPreview entries. Falls back to OpenAI if OpenLibrary lacks description."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="Items to process")
        parser.add_argument("--dry-run", action="store_true", help="Don't save changes")

    def handle(self, *args, **options):
        limit = options['limit']
        dry = options['dry_run']

        qs = Book.objects.all()[:limit]
        self.stdout.write(f"Processing {qs.count()} books (limit={limit})")
        for book in qs:
            self.stdout.write(f"→ {book.title} (isbn={book.isbn}) ... ", ending="")
            # try OpenLibrary by isbn
            ol = None
            summary = None
            cover = None
            tags = []
            reading_level = ""
            recommendations = ""

            if book.isbn:
                ol = fetch_openlibrary_by_isbn(book.isbn)
            # if ISBN didn't give a work, try to guess work key from internal isbn like OLISBN-... (if you have work key saved)
            if ol:
                # prefer 'description' or 'subtitle' or 'excerpt'
                desc = ol.get("description")
                if isinstance(desc, dict):
                    summary = desc.get("value")
                elif isinstance(desc, str):
                    summary = desc
                cover = openlibrary_cover_from_data(ol)
                # try to find authors and subjects
                tags = ol.get("subjects") or []
            # If no summary, try to call OpenAI
            if not summary:
                authors = [book.author.name] if book.author else []
                ai = call_openai_generate_preview(book.title, authors, short_context=book.summary[:800] if book.summary else "")
                if ai:
                    summary = ai.get("summary")
                    tags = ai.get("tags") or tags
                    reading_level = ai.get("reading_level") or ""
                    recommendations = ai.get("recommendations") or ""
                    source = BookPreview.SOURCE_OPENAI
                else:
                    source = BookPreview.SOURCE_OPENLIB
            else:
                source = BookPreview.SOURCE_OPENLIB

            # create or update
            if not dry:
                preview, created = BookPreview.objects.update_or_create(
                    book=book,
                    defaults={
                        "summary": summary or "",
                        "cover_url": cover or "",
                        "tags": tags or [],
                        "reading_level": reading_level,
                        "recommendations": recommendations,
                        "source": source,
                    }
                )
            self.stdout.write(self.style.SUCCESS("done"))
            time.sleep(0.3)
        self.stdout.write(self.style.SUCCESS("All done."))
