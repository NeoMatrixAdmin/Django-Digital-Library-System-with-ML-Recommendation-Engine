# catalog/management/commands/generate_embeddings.py
import json
from django.core.management.base import BaseCommand, CommandError
from catalog.models import Book, BookPreview
from services.embedding_service import generate_embedding_from_text
from django.utils import timezone

class Command(BaseCommand):
    help = "Create or refresh embeddings for a single book or all books."

    def add_arguments(self, parser):
        parser.add_argument("book_id", nargs="?", type=int, help="ID of book")
        parser.add_argument("--all", action="store_true", help="Generate embeddings for all books")

    def handle(self, *args, **options):
        book_id = options.get("book_id")
        do_all = options.get("all")

        if book_id:
            try:
                book = Book.objects.get(pk=book_id)
            except Book.DoesNotExist:
                raise CommandError("Book not found")
            self._process_book(book)
            return

        if do_all:
            qs = Book.objects.all()
            for book in qs:
                self._process_book(book)
            self.stdout.write(self.style.SUCCESS("Completed embeddings for all books"))
            return

        raise CommandError("Provide book_id or use --all")

    def _process_book(self, book):
        preview, _ = BookPreview.objects.get_or_create(book=book)
        # embed using title + improved summary if available else book.summary
        text = f"{book.title}\n\n{preview.summary or book.summary or ''}"
        try:
            vec = generate_embedding_from_text(text)
            preview.embedding = vec
            preview.embedding_updated_at = timezone.now()
            preview.save()
            self.stdout.write(self.style.SUCCESS(f"Saved embedding for: {book.title}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed for {book.title}: {e}"))
