# scraper/preview_generator.py
import requests
import os
import time
from django.conf import settings

OPENLIBRARY_ISBN_URL = "https://openlibrary.org/isbn/{isbn}.json"
OPENLIBRARY_WORK_URL = "https://openlibrary.org{work_key}.json"
COVERS_BASE = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

OPENAI_API_KEY = os.environ.get("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")  # set this in env when deploying
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")  # change if needed

def fetch_openlibrary_by_isbn(isbn):
    try:
        r = requests.get(OPENLIBRARY_ISBN_URL.format(isbn=isbn), timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def fetch_openlibrary_work(work_key):
    try:
        r = requests.get(OPENLIBRARY_WORK_URL.format(work_key=work_key), timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

def openlibrary_cover_from_data(data):
    # data may have 'covers' list of ids
    covers = data.get("covers") or []
    if covers:
        return COVERS_BASE.format(cover_id=covers[0])
    return None

def call_openai_generate_preview(title, authors, short_context=""):
    """
    Minimal OpenAI call wrapper. Expects OPENAI_API_KEY set.
    Returns dict: {summary, tags(list), reading_level, recommendations}
    """
    # Use requests to call OpenAI REST API (so no extra lib requirement)
    if not OPENAI_API_KEY:
        return None

    prompt = f"""
You are a helpful book-summary generator. Given the title and authors and optional context, produce:
1) A short engaging summary in 3-4 sentences suitable for a preview card.
2) A short list of 6 tags/genres (comma-separated).
3) A one-line reading level (e.g., "Adult - General", "YA", "Short non-fiction").
4) 2 short recommendations (titles) for someone who liked this book.

Input:
Title: {title}
Authors: {', '.join(authors) if isinstance(authors, (list,tuple)) else authors}
Context: {short_context}

Output JSON strictly (no extra text) with keys: summary, tags, reading_level, recommendations.
"""
    body = {
        "model": "gpt-4o-mini",  # adjust if different model available
        "messages": [{"role":"user","content": prompt}],
        "max_tokens": 400,
        "temperature": 0.8,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        txt = data["choices"][0]["message"]["content"].strip()
        # Expect JSON — try to parse
        import json
        try:
            parsed = json.loads(txt)
            # ensure keys exist
            return {
                "summary": parsed.get("summary") or "",
                "tags": parsed.get("tags") or [],
                "reading_level": parsed.get("reading_level") or "",
                "recommendations": parsed.get("recommendations") or "",
            }
        except Exception:
            # fallback: try to extract lines
            return {"summary": txt, "tags": [], "reading_level": "", "recommendations": ""}
    except Exception:
        return None
