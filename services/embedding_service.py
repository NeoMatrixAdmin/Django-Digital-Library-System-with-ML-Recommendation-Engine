# services/embedding_service.py
import os
import math
import time
from pathlib import Path

# Reuse get_client() from services/groq_client
from services.groq_client import get_client

# Groq updated model (the only embedding model available now)
DEFAULT_EMBEDDING_MODEL = os.getenv("GROQ_EMBED_MODEL", "text-embedding-3-large")


def _try_get_embedding_from_response(resp):
    """
    Extract embedding vector from Groq's current embedding response format.
    Expected format:
    {
        "data": [
            {"embedding": [...] }
        ]
    }
    """
    # New Groq format — Simple & reliable
    try:
        return resp.data[0].embedding
    except Exception:
        pass

    # Mapping fallback
    try:
        if "data" in resp:
            return resp["data"][0].get("embedding")
    except Exception:
        pass

    return None


def generate_embedding_from_text(text, model=DEFAULT_EMBEDDING_MODEL):
    """
    Generates embeddings using Groq's new embedding endpoint.
    Returns a list[float].
    """
    client = get_client()

    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text provided for embedding")

    last_exc = None

    for attempt in range(3):
        try:
            # New valid call for Groq embeddings
            resp = client.embeddings.create(
                model=model,
                input=text
            )

            emb = _try_get_embedding_from_response(resp)
            if emb:
                return list(emb)

            last_exc = RuntimeError("Embedding extraction failed")

        except Exception as e:
            last_exc = e
            time.sleep(0.6 * (attempt + 1))

    raise last_exc


# ------------ COSINE SIMILARITY HELPERS ------------ #

def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _norm(a):
    return math.sqrt(sum(x * x for x in a))


def cosine_similarity(a, b):
    if not a or not b:
        return 0.0
    na = _norm(a)
    nb = _norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return _dot(a, b) / (na * nb)
