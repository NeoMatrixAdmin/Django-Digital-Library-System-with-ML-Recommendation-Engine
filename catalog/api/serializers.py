from rest_framework import serializers
from catalog.models import Book, BookInstance, BookPreview, Author, Genre, Language


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "first_name", "last_name"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]


# ——————————————————————————————
# PREVIEW SERIALIZER
# ——————————————————————————————
class BookPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookPreview
        fields = [
            "real_isbn",
            "openlibrary_url",
            "preview_available",
            "summary",
            "cover_url",
            "tags",
            "reading_level",
            "recommendations",
            "source",
            "created_at",
            "updated_at",
        ]


# ——————————————————————————————
# BOOK SERIALIZER (MAIN)
# ——————————————————————————————
class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    language = LanguageSerializer(read_only=True)

    preview = BookPreviewSerializer(read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "summary",
            "isbn",
            "real_isbn",
            "genre",
            "language",
            "ai_preview",
            "preview",  # <-- VERY IMPORTANT
        ]


# ——————————————————————————————
# BOOK INSTANCE SERIALIZER
# ——————————————————————————————
class BookInstanceSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = BookInstance
        fields = [
            "id",
            "book",
            "imprint",
            "due_back",
            "borrower",
            "status",
        ]
