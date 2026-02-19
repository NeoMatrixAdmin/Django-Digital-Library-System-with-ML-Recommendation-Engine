# scraper/pipeline.py
from django.db import transaction
from django.utils.text import Truncator
from catalog.models import Book, Author, Genre, ScrapeRecord
from .utils import make_fingerprint
import logging

logger = logging.getLogger(__name__)

def normalize_author_name(name):
    parts = (name or "").strip().split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    return first, last

@transaction.atomic
def save_item_to_db(item, source_url=None):
    """
    item: dict with keys title, authors (list), isbns (list), publish_year, cover_url, subjects(list)
    Creates Book, Author, Genre and creates/updates ScrapeRecord.
    Returns tuple (book_obj, created_bool, reason)
    """
    title = item.get("title") or "Untitled"
    authors = item.get("authors") or []
    isbns = item.get("isbns") or []
    fingerprint = make_fingerprint(title, authors, isbns)

    # Check ScrapeRecord for duplicates
    existing_record = ScrapeRecord.objects.filter(fingerprint=fingerprint).first()
    if existing_record and existing_record.status == ScrapeRecord.STATUS_DONE:
        # get linked book if any
        book = None
        if existing_record.book_id:
            try:
                book = Book.objects.get(pk=existing_record.book_id)
            except Book.DoesNotExist:
                book = None
        return (book, False, "already_imported")

    # Try dedupe by ISBN if available
    if isbns:
        for isbn in isbns:
            e = Book.objects.filter(isbn__iexact=isbn).first()
            if e:
                # mark record
                r = ScrapeRecord.objects.create(
                    url=source_url or "",
                    fingerprint=fingerprint,
                    status=ScrapeRecord.STATUS_DONE,
                    book=e
                )
                return (e, False, "existing_isbn")

    # fallback dedupe by title + first author
    qs = Book.objects.filter(title__iexact=title)
    if authors:
        qs = qs.filter(authors__first_name__icontains=authors[0].split()[0])
    if qs.exists():
        book = qs.first()
        ScrapeRecord.objects.create(url=source_url or "", fingerprint=fingerprint, status=ScrapeRecord.STATUS_DONE, book=book)
        return (book, False, "existing_title_author")

    # Create book
    book = Book.objects.create(
        title=Truncator(title).chars(255),
        summary = Truncator(", ".join(item.get("subjects") or [])).chars(2000),
        isbn = isbns[0] if isbns else "",
        publish_year = item.get("publish_year")
    )

    # authors (supports M2M or FK)
    for a in authors:
        first, last = normalize_author_name(a)
        author_obj, _ = Author.objects.get_or_create(first_name=first, last_name=last)
        try:
            book.authors.add(author_obj)
        except Exception:
            book.author = author_obj
            book.save()

    # subjects -> Genre
    for s in (item.get("subjects") or [])[:8]:
        g, _ = Genre.objects.get_or_create(name=s)
        try:
            book.genre.add(g)
        except Exception:
            pass

    # cover_url if model supports it
    if getattr(book, "cover_url", None) is not None and item.get("cover_url"):
        book.cover_url = item.get("cover_url")
        book.save(update_fields=["cover_url"])

    # Save scrape record as done
    rec = ScrapeRecord.objects.create(
        url=source_url or "",
        fingerprint=fingerprint,
        status=ScrapeRecord.STATUS_DONE,
        book=book
    )

    return (book, True, "created")
