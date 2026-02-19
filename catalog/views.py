from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Case, When, BooleanField
from django.core.paginator import Paginator

from .models import (
    Book,
    Author,
    BookInstance,
    Genre,
    Language,
    BookPreview,
)

# ----------------------------
# HOME PAGE
# ----------------------------
def index(request):
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()
    num_genres = Genre.objects.count()
    num_languages = Language.objects.count()

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_languages': num_languages,
    }
    return render(request, 'catalog/index.html', context)


# ----------------------------
# BOOK VIEWS
# ----------------------------
class BookCreate(CreateView):
    model = Book
    fields = '__all__'


class BookDetail(DetailView):
    model = Book
    template_name = "catalog/book_detail.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Attach AI metadata preview
        try:
            context["preview"] = self.object.preview
        except BookPreview.DoesNotExist:
            context["preview"] = None

        return context


def all_books(request):
    books = Book.objects.all()
    return render(request, "catalog/all_books.html", {"books": books})


@login_required
def available_books(request):
    books = Book.objects.prefetch_related('bookinstance_set', 'genre', 'author')
    books_with_available_instance = []
    for book in books:
        available_instance = book.bookinstance_set.filter(status='a').first()
        books_with_available_instance.append((book, available_instance))
    return render(request, 'catalog/available_books.html', {
        'books_with_available_instance': books_with_available_instance
    })


# ----------------------------
# AUTH + USER VIEWS
# ----------------------------
def logout_view(request):
    logout(request)
    return redirect(request.GET.get('next', '/'))


@login_required
def my_view(request):
    return render(request, 'catalog/my_view.html')


class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


class CheckedOutBooksByUserView(LoginRequiredMixin, ListView):
    model = BookInstance
    template_name = 'catalog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(
            borrower=self.request.user,
            status='o'
        ).order_by('due_back')


@login_required
def borrow_book(request, pk):
    instance = get_object_or_404(BookInstance, pk=pk)

    if instance.status == "a":
        instance.status = "o"
        instance.borrower = request.user
        instance.borrowed_on = timezone.now()
        instance.save()

    return redirect("catalog:my_books")


@login_required
def return_book(request, pk):
    instance = get_object_or_404(BookInstance, pk=pk)

    if instance.borrower == request.user or request.user.is_staff:
        instance.status = "a"
        instance.borrower = None
        instance.borrowed_on = None
        instance.due_back = None
        instance.save()

    return redirect("catalog:my_books")
@login_required
def borrowed_books(request):
    my_books = BookInstance.objects.filter(borrower=request.user)
    return render(request, "catalog/borrowed_books.html", {"books": my_books})


@login_required
def user_account(request):
    return render(request, "catalog/user_account.html")


# ----------------------------
# AUTHOR & GENRE LISTS
# ----------------------------
def authors_list(request):
    authors = Author.objects.all()
    return render(request, 'catalog/authors_list.html', {'authors': authors})


def genres_list(request):
    genres = Genre.objects.all()
    return render(request, 'catalog/genres_list.html', {'genres': genres})


def books_by_author(request, author_id):
    author = get_object_or_404(Author, pk=author_id)
    books = author.book_set.all()
    return render(request, 'catalog/books_by_author.html', {'author': author, 'books': books})


def books_by_genre(request, genre_id):
    genre = get_object_or_404(Genre, pk=genre_id)
    books = Book.objects.filter(genre=genre)
    return render(request, 'catalog/all_books.html', {'books': books, 'filter_title': f"Books in {genre.name}"})


# ----------------------------
# SEARCH & AUTOCOMPLETE
# ----------------------------
def search_view(request):
    query = request.GET.get("q", "").strip()

    genre_filter = [g for g in request.GET.getlist("genre") if g]
    author_filter = [a for a in request.GET.getlist("author") if a]
    language_filter = [l for l in request.GET.getlist("language") if l]

    availability_filter = request.GET.get("availability")
    preview_filter = request.GET.get("has_preview")
    real_isbn_filter = request.GET.get("has_real_isbn")

    books = Book.objects.all()

    # TEXT QUERY
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(real_isbn__icontains=query)
        )

    # APPLY FILTERS
    if genre_filter:
        books = books.filter(genre__id__in=genre_filter).distinct()

    if author_filter:
        books = books.filter(author__id__in=author_filter)

    if language_filter:
        books = books.filter(language__id__in=language_filter)

    books = books.annotate(
        is_available=Case(
            When(bookinstance__status='a', then=True),
            default=False,
            output_field=BooleanField()
        )
    ).distinct()

    if availability_filter == "available":
        books = books.filter(is_available=True)

    if preview_filter == "1":
        books = books.filter(preview__preview_available=True)

    if real_isbn_filter == "1":
        books = books.filter(real_isbn__isnull=False).exclude(real_isbn="")

    paginator = Paginator(books, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "page_obj": page_obj,
        "results": page_obj.object_list,
        "genres": Genre.objects.all(),
        "authors": Author.objects.all(),
        "languages": Language.objects.all(),
        "filters": {
            "genre": genre_filter,
            "author": author_filter,
            "language": language_filter,
            "availability": availability_filter,
            "has_preview": preview_filter,
            "has_real_isbn": real_isbn_filter,
        }
    }

    return render(request, "catalog/search_results.html", context)


def autocomplete_view(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    title_matches = Book.objects.filter(title__icontains=query)
    author_matches = Book.objects.filter(
        Q(author__first_name__icontains=query) |
        Q(author__last_name__icontains=query)
    )
    summary_matches = Book.objects.filter(summary__icontains=query)

    combined = list(title_matches) + list(author_matches) + list(summary_matches)

    seen = set()
    unique = []
    for b in combined:
        if b.id not in seen:
            seen.add(b.id)
            unique.append(b)

    unique = unique[:7]

    def snippet(text, q):
        text = text or ""
        ql = q.lower()
        idx = text.lower().find(ql)
        if idx == -1:
            return text[:120] + "..." if len(text) > 120 else text
        start = max(0, idx - 40)
        end = min(len(text), idx + 40)
        return ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")

    results = []
    for b in unique:
        results.append({
            "title": b.title,
            "author": str(b.author) if b.author else "Unknown",
            "snippet": snippet(b.summary, query),
            "url": f"/catalog/book/{b.id}/",
        })

    return JsonResponse({"results": results})


# ----------------------------
# GROQ TEST
# ----------------------------
def test_groq(request):
    from services.groq_client import call_llama
    output = call_llama("Say 'Groq setup successful'")
    return HttpResponse(output)
