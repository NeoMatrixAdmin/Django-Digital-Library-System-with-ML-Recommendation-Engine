from catalog.models import Book, BookPreview


def save_preview_from_scraper(book: Book, real_isbn: str, cover_url: str = None):
    """
    Called by Selenium when it finds a real ISBN.
    Creates or updates the BookPreview entry.
    """

    # Save ISBN on the Book model
    if book.real_isbn != real_isbn:
        book.real_isbn = real_isbn
        book.save()

    # Build OpenLibrary preview URL
    openlib_url = f"https://openlibrary.org/isbn/{real_isbn}/preview"

    preview_values = {
        "cover_url": cover_url,
        "summary": None,  # will fill later from AI if needed
        "reading_level": None,
        "tags": [],
        "recommendations": None,
        "source": BookPreview.SOURCE_OPENLIB,
    }

    preview, created = BookPreview.objects.update_or_create(
        book=book,
        defaults=preview_values,
    )

    return preview
