from django.contrib import admin
from catalog.models import Book, BookPreview, Author, Genre, Language
from services.metadata_generator import generate_book_metadata
import json

# --------------------------
# ADMIN ACTION
# --------------------------
@admin.action(description="Generate AI Metadata")
def generate_ai_metadata(modeladmin, request, queryset):
    for book in queryset:
        metadata = generate_book_metadata(book)

        preview, created = BookPreview.objects.get_or_create(book=book)
        preview.tags = metadata.get("tags", [])
        preview.summary = metadata.get("improved_summary", "")
        preview.reading_level = metadata.get("reading_level", "")
        preview.recommendations = json.dumps(metadata.get("similar_books", []))
        preview.preview_available = True
        preview.save()

    modeladmin.message_user(request, "AI metadata generated successfully!")


# --------------------------
# BOOK ADMIN
# --------------------------
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "real_isbn")
    actions = [generate_ai_metadata]


# --------------------------
# REGISTER MODELS
# --------------------------
admin.site.register(Book, BookAdmin)
admin.site.register(BookPreview)
admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Language)
