"""
Semantic Embedding Engine
Uses Google Gemini embeddings when available, otherwise TF-IDF fallback.
"""
import os
import pickle
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
USE_GEMINI = False
if GOOGLE_API_KEY and genai is not None:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        USE_GEMINI = True
    except Exception as exc:
        warnings.warn(f"Gemini config failed: {exc}. Falling back to TF-IDF.", RuntimeWarning)


_embedding_cache: Dict[int, np.ndarray] = {}
_tfidf_vectorizer: Optional[Any] = None
_tfidf_matrix = None


def _hash_embedding(text: str, dimension: int = 512) -> np.ndarray:
    """Small deterministic fallback when sklearn is unavailable."""
    vec = np.zeros(dimension, dtype=np.float32)
    for token in (text or "empty profile").lower().split():
        vec[hash(token) % dimension] += 1.0
    norm = np.linalg.norm(vec) + 1e-8
    return vec / norm


def get_gemini_embedding(text: str, model: str = "text-embedding-004") -> np.ndarray:
    """Get an embedding from Gemini."""
    if not USE_GEMINI or genai is None:
        raise ValueError("Gemini not configured")

    cache_key = hash(text[:200])
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    try:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document",
        )
        embedding = np.array(result["embedding"], dtype=np.float32)
        _embedding_cache[cache_key] = embedding
        return embedding
    except Exception as exc:
        warnings.warn(f"Gemini embedding error: {exc}", RuntimeWarning)
        raise


def get_tfidf_embedding(text: str, fit: bool = False) -> np.ndarray:
    """Get a TF-IDF embedding. If fit=True, refit the vectorizer."""
    global _tfidf_vectorizer

    if TfidfVectorizer is None:
        return _hash_embedding(text)

    if _tfidf_vectorizer is None:
        _tfidf_vectorizer = TfidfVectorizer(
            max_features=512,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )

    if fit or not hasattr(_tfidf_vectorizer, "vocabulary_") or _tfidf_vectorizer.vocabulary_ is None:
        vec = _tfidf_vectorizer.fit_transform([text or "empty profile"])
    else:
        vec = _tfidf_vectorizer.transform([text or "empty profile"])

    return vec.toarray()[0].astype(np.float32)


def get_embedding(text: str, fit_tfidf: bool = False) -> np.ndarray:
    """Unified embedding function with automatic fallback."""
    if USE_GEMINI:
        try:
            return get_gemini_embedding(text)
        except Exception:
            warnings.warn("Falling back to TF-IDF due to Gemini error.", RuntimeWarning)

    return get_tfidf_embedding(text, fit=fit_tfidf)


def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    if emb1 is None or emb2 is None:
        return 0.0
    emb1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
    emb2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
    return float(np.dot(emb1, emb2))


def batch_get_embeddings(texts: List[str], use_gemini_first: bool = True) -> List[np.ndarray]:
    """Get embeddings for multiple texts efficiently."""
    embeddings = []
    for i, text in enumerate(texts):
        embeddings.append(get_embedding(text, fit_tfidf=(i == 0 and not USE_GEMINI)))
    return embeddings


def semantic_similarity(text1: str, text2: str) -> float:
    """Direct semantic similarity between two texts."""
    emb1 = get_embedding(text1 or "empty profile")
    emb2 = get_embedding(text2 or "empty profile")
    return compute_cosine_similarity(emb1, emb2)


if __name__ == "__main__":
    t1 = "Senior ML Engineer with Python TensorFlow AWS experience"
    t2 = "Machine Learning Engineer proficient in PyTorch and cloud technologies"
    sim = semantic_similarity(t1, t2)
    print(f"Semantic similarity: {sim:.4f}")
