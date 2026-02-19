# dashboard/views.py
import os
from collections import OrderedDict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from catalog.models import Book, BookInstance, Author, Genre, Language

# ensure charts directory exists
CHART_DIR = os.path.join(settings.MEDIA_ROOT, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

def _save_barh_topN(series, path, title, xlabel="Count", figsize=(8, 5)):
    plt.figure(figsize=figsize)
    sns.set_style("darkgrid")
    plt.rcParams.update({'text.color': 'white', 'axes.labelcolor': 'white', 'axes.edgecolor': 'white'})

    # horizontal bar for readability
    sns.barplot(x=series.values, y=series.index, palette="mako")
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel)
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(path, facecolor='#0d0d0d', transparent=False)
    plt.close()

def _save_pie(series, path, title, figsize=(6,6)):
    plt.figure(figsize=figsize)
    plt.rcParams.update({'text.color': 'white'})
    wedges, texts, autotexts = plt.pie(series.values, labels=series.index, autopct='%1.1f%%', startangle=140)
    plt.title(title, color="white")
    plt.tight_layout()
    plt.savefig(path, facecolor='#0d0d0d')
    plt.close()

@login_required
def dashboard_home(request):
    # KPI metrics
    total_books = Book.objects.count()
    total_authors = Author.objects.count()
    total_genres = Genre.objects.count()
    total_instances = BookInstance.objects.count()
    total_borrowed = BookInstance.objects.filter(status="o").count()
    total_available = BookInstance.objects.filter(status="a").count()

    # ---------- GENRE DATA ----------
    # full dataset for interactive chart
    books_genre = Book.objects.all().values("id", "title", "genre__name")
    df_genre = pd.DataFrame(list(books_genre))
    if "genre__name" in df_genre.columns:
        df_genre = df_genre.dropna(subset=["genre__name"])
        genre_counts = df_genre["genre__name"].value_counts()
    else:
        genre_counts = pd.Series(dtype=int)

    # static top5
    top5_genres = genre_counts.nlargest(5)
    genre_chart_path = os.path.join(CHART_DIR, "genre_chart.png")
    if not top5_genres.empty:
        _save_barh_topN(top5_genres, genre_chart_path, "Top 5 Genres")

    # ---------- AUTHORS DATA ----------
    books_author = Book.objects.all().values("id", "title", "author__first_name", "author__last_name")
    df_author = pd.DataFrame(list(books_author))
    if not df_author.empty and ("author__first_name" in df_author.columns):
        df_author["author_name"] = df_author["author__first_name"].fillna("") + \
                                   (" " + df_author["author__last_name"].fillna("")).str.strip()
        author_counts = df_author["author_name"].replace("", np.nan).dropna().value_counts()
    else:
        author_counts = pd.Series(dtype=int)

    top10_authors = author_counts.nlargest(10)
    author_chart_path = os.path.join(CHART_DIR, "author_chart.png")
    if not top10_authors.empty:
        _save_barh_topN(top10_authors, author_chart_path, "Top 10 Authors")

    # ---------- AVAILABLE vs BORROWED ----------
    status_counts = BookInstance.objects.values_list("status", flat=True)
    status_series = pd.Series(list(status_counts))
    avail_vs_borrowed = pd.Series({
        "Available": (status_series == "a").sum(),
        "Borrowed": (status_series == "o").sum()
    })
    avail_borrowed_chart = os.path.join(CHART_DIR, "avail_borrowed_pie.png")
    _save_pie(avail_vs_borrowed, avail_borrowed_chart, "Available vs Borrowed")

    # ---------- BORROWED PER MONTH ----------
    borrowed_qs = BookInstance.objects.filter(borrowed_on__isnull=False).values_list("borrowed_on", flat=True)
    borrowed_dates = pd.to_datetime(list(borrowed_qs))
    if not borrowed_dates.empty:
        # group by month-year
        borrowed_month = borrowed_dates.to_series().dt.to_period("M").value_counts().sort_index()
        borrowed_month.index = borrowed_month.index.astype(str)
        borrowed_month_chart = os.path.join(CHART_DIR, "borrowed_per_month.png")
        _save_barh_topN(borrowed_month, borrowed_month_chart, "Borrowed per Month", xlabel="Borrows", figsize=(9,5))
    else:
        borrowed_month = pd.Series(dtype=int)
        borrowed_month_chart = None

    # ---------- Prepare interactive data (lists for Chart.js) ----------
    genre_labels = list(genre_counts.index)
    genre_values = list(genre_counts.values)

    author_labels = list(author_counts.index)
    author_values = list(author_counts.values)

    avail_labels = list(avail_vs_borrowed.index)
    avail_values = list(avail_vs_borrowed.values)

    borrowed_month_labels = list(borrowed_month.index) if not borrowed_month.empty else []
    borrowed_month_values = list(borrowed_month.values) if not borrowed_month.empty else []

    # build context
    context = {
        "total_books": total_books,
        "total_authors": total_authors,
        "total_genres": total_genres,
        "total_instances": total_instances,
        "total_borrowed": total_borrowed,
        "total_available": total_available,

        "genre_chart_url": "/media/charts/genre_chart.png" if os.path.exists(genre_chart_path) else None,
        "genre_labels": genre_labels,
        "genre_values": genre_values,

        "author_chart_url": "/media/charts/author_chart.png" if os.path.exists(author_chart_path) else None,
        "author_labels": author_labels,
        "author_values": author_values,

        "avail_chart_url": "/media/charts/avail_borrowed_pie.png" if os.path.exists(avail_borrowed_chart) else None,
        "avail_labels": avail_labels,
        "avail_values": avail_values,

        "borrowed_month_chart_url": "/media/charts/borrowed_per_month.png" if borrowed_month_chart and os.path.exists(borrowed_month_chart) else None,
        "borrowed_month_labels": borrowed_month_labels,
        "borrowed_month_values": borrowed_month_values,
    }

    return render(request, "dashboard/dashboard.html", context)

