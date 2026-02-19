from django.urls import path
from . import views
from .views import CheckedOutBooksByUserView

app_name = "catalog"

urlpatterns = [
    path("", views.index, name="index"),

    # BOOK CRUD
    path("create_book/", views.BookCreate.as_view(), name="create_book"),
    path("book/<int:pk>/", views.BookDetail.as_view(), name="book-detail"),

    # BORROW / RETURN
    path("book/<int:pk>/borrow/", views.borrow_book, name="borrow_book"),
    path("return_book/<int:pk>/", views.return_book, name="return_book"),

    # USER BOOKS
    path("mybooks/", CheckedOutBooksByUserView.as_view(), name="my_books"),

    # BOOK LIST VIEWS
    path("all_books/", views.all_books, name="all_books"),
    path("books/available/", views.available_books, name="available_books"),
    path("borrowed_books/", views.borrowed_books, name="borrowed_books"),

    # AUTHORS
    path("authors/", views.authors_list, name="authors_list"),
    path("authors/<int:author_id>/books/", views.books_by_author, name="books_by_author"),

    # GENRES
    path("genres/", views.genres_list, name="genres_list"),
    path("genres/<int:genre_id>/books/", views.books_by_genre, name="books_by_genre"),

    # SEARCH & AUTOCOMPLETE
    path("search/", views.search_view, name="search"),
    path("autocomplete/", views.autocomplete_view, name="autocomplete"),

    # TEST GROQ
    path("test_groq/", views.test_groq),

]
