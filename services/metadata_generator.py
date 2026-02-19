import json
from services.groq_client import call_llama
from services.embedding_service import generate_embedding_from_text
from django.utils import timezone


def generate_book_metadata(book):
    """
    Takes a Book instance and returns structured metadata (dict).
    Does NOT save anything. Just generates the metadata.
    """

    genres = ", ".join(g.name for g in book.genre.all()) or "Unknown"
    author = f"{book.author.first_name} {book.author.last_name}" if book.author else "Unknown"

    prompt = f"""
You are an expert library metadata engine. 
Given the following book information, generate enhanced metadata in clean JSON.

Follow these exact rules:
- Output ONLY valid JSON.
- Do not include any explanations.
- Always fill every field.
- Tags must be 3–5 items.
- Reading level must be one of: Beginner, Intermediate, Advanced.
- For similar books, return: [{{ "title": "...", "reason": "..." }}]
- Improved summary must be longer, polished, and detailed, but not more than 200 words.

JSON Schema:
{{
  "tags": ["tag1", "tag2", "tag3"],
  "improved_summary": "string",
  "reading_level": "Beginner | Intermediate | Advanced",
  "categories": ["category1", "category2"],
  "similar_books": [
    {{
      "title": "string",
      "reason": "string"
    }}
  ]
}}

### BOOK DATA
Title: {book.title}
Author: {author}
Genres: {genres}
Language: {book.language}
Summary: {book.summary}

Return only JSON:
"""

    ai_output = call_llama(prompt, max_tokens=500)

    try:
        metadata = json.loads(ai_output)
    except Exception as e:
        return {"error": str(e), "raw": ai_output}

    return metadata



def apply_metadata_to_preview(book, preview, metadata):
    """
    Saves metadata into the BookPreview + generates embeddings.
    This function is safe and runs only when called manually.
    """

    # Basic metadata
    preview.summary = metadata.get("improved_summary") or metadata.get("summary") or ""
    preview.tags = metadata.get("tags", [])
    preview.reading_level = metadata.get("reading_level", "")
    preview.recommendations = json.dumps(metadata.get("similar_books", []))

    # ------ EMBEDDING GENERATION (safe + inside function) ------
    try:
        embed_text = f"{book.title}\n\n{preview.summary}"
        embedding = generate_embedding_from_text(embed_text)

        preview.embedding = embedding
        preview.embedding_updated_at = timezone.now()

    except Exception as e:
        print("Embedding failed:", e)
        # do not overwrite old embedding
        preview.embedding = preview.embedding or None

    preview.save()
    return preview
