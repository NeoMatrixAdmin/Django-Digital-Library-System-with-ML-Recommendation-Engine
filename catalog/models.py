from django.db import models
from django.contrib.auth.models import User


class Genre(models.Model):
    """Book genres (e.g., Fiction, Romance)"""
    name = models.CharField(max_length=200, help_text="Enter a book genre")

    def __str__(self):
        return self.name


class Language(models.Model):
    """Language of the book (English, Hindi, etc.)"""
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Author(models.Model):
    """Author details"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    summary = models.TextField(max_length=1000)
    isbn = models.CharField(max_length=50)  # long enough for fallback values
    genre = models.ManyToManyField(Genre)
    ai_preview = models.TextField(blank=True, null=True)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)

    # REAL WORLD fields
    real_isbn = models.CharField(max_length=20, null=True, blank=True)
    ol_work_id = models.CharField(max_length=50, null=True, blank=True)  # <-- REQUIRED

    def __str__(self):
        return self.title


class BookInstance(models.Model):
    """Individual copy of a book"""
    book = models.ForeignKey(Book, on_delete=models.RESTRICT)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True)
    borrower = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default='m',
    )
    borrowed_on = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.book.title} ({self.id})"


class ScrapeRecord(models.Model):
    """History of scraped ISBN results"""
    query = models.CharField(max_length=200)
    isbn_found = models.CharField(max_length=13, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.query} -> {self.isbn_found}"

# catalog/models.py  (append this near other models)

from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import json

class BookPreview(models.Model):
    SOURCE_OPENLIB = "openlibrary"
    SOURCE_OPENAI = "openai"

    book = models.OneToOneField("Book", on_delete=models.CASCADE, related_name="preview")

    # ————— REQUIRED FOR PREVIEW SYSTEM ————— #
    real_isbn = models.CharField(max_length=30, null=True, blank=True)
    openlibrary_url = models.URLField(null=True, blank=True)
    preview_available = models.BooleanField(default=False)
    # ———————————————————————————————————————— #

    summary = models.TextField(blank=True, null=True)
    cover_url = models.URLField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    reading_level = models.CharField(max_length=100, blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)

    source = models.CharField(
        max_length=20,
        choices=[
            (SOURCE_OPENLIB, "OpenLibrary"),
            (SOURCE_OPENAI, "OpenAI"),
        ],
        default=SOURCE_OPENLIB,
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    embedding = models.JSONField(null=True, blank=True)
    embedding_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Preview for {self.book.title} ({self.source})"
