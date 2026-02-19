import json
from django.core.management.base import BaseCommand, CommandError
from catalog.models import Book, BookPreview
from services.metadata_generator import generate_book_metadata


class Command(BaseCommand):
    help = "Generate AI metadata for a single book or all books."
    preview.preview_available = True
    def add_arguments(self, parser):
        parser.add_argument(
            "book_id",
            nargs="?",
            type=int,
            help="ID of the book to generate metadata for"
        )

        parser.add_argument(
            "--all",
            action="store_true",
            help="Generate metadata for all books that don't have a preview yet"
        )

    def handle(self, *args, **options):

        book_id = options.get("book_id")
        generate_all = options.get("all")

        # CASE 1 — Generate for one book
        if book_id:
            try:
                book = Book.objects.get(pk=book_id)
            except Book.DoesNotExist:
                raise CommandError(f"Book with id {book_id} does not exist")

            self.stdout.write(self.style.WARNING(f"Generating metadata for: {book.title}"))
            metadata = generate_book_metadata(book)
            self.save_metadata(book, metadata)
            return

        # CASE 2 — Generate for all books missing preview
        if generate_all:
            books = Book.objects.all()

            for book in books:
                self.stdout.write(self.style.WARNING(f"\nProcessing: {book.title}"))

                metadata = generate_book_metadata(book)
                self.save_metadata(book, metadata)

            self.stdout.write(self.style.SUCCESS("Completed generating metadata for all books."))
            return

        # No arguments provided
        raise CommandError("Provide a book_id OR use --all")

    def save_metadata(self, book, metadata):
        """Save AI metadata into BookPreview."""
        preview, created = BookPreview.objects.get_or_create(book=book)

        preview.tags = metadata.get("tags", [])
        preview.summary = metadata.get("improved_summary", "")
        preview.reading_level = metadata.get("reading_level", "")
        preview.recommendations = json.dumps(metadata.get("similar_books", []))

        preview.save()

        self.stdout.write(
            self.style.SUCCESS(f"Saved metadata for {book.title} (created={created})")
        )
