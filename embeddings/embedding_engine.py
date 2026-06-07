"""
Semantic Embedding Engine
Uses Google Gemini embeddings (preferred) or TF-IDF fallback for semantic similarity.
"""
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Try to load API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("✅ Gemini API configured for embeddings.")
        USE_GEMINI = True
    except Exception as e:
        print(f"Gemini config failed: {e}. Falling back to TF-IDF.")
        USE_GEMINI = False
else:
    print("⚠️ No GOOGLE_API_KEY found. Using TF-IDF embeddings (less semantic).")
    USE_GEMINI = False

# Cache for embeddings
_embedding_cache = {}

def get_gemini_embedding(text: str, model: str = "text-embedding-004") -> np.ndarray:
    """Get embedding using Gemini API."""
    if not USE_GEMINI:
        raise ValueError("Gemini not configured")
    
    # Simple cache
    cache_key = hash(text[:200])
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    try:
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document"  # or "semantic_similarity"
        )
        embedding = np.array(result['embedding'], dtype=np.float32)
        _embedding_cache[cache_key] = embedding
        return embedding
    except Exception as e:
        print(f"Gemini embedding error: {e}")
        raise

# TF-IDF fallback (global vectorizer fitted on demand)
_tfidf_vectorizer = None
_tfidf_matrix = None  # For batch

def get_tfidf_embedding(text: str, fit: bool = False) -> np.ndarray:
    """Get TF-IDF embedding. If fit=True, refit vectorizer."""
    global _tfidf_vectorizer
    
    if _tfidf_vectorizer is None:
        _tfidf_vectorizer = TfidfVectorizer(
            max_features=512,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
    
    if fit or not hasattr(_tfidf_vectorizer, 'vocabulary_') or _tfidf_vectorizer.vocabulary_ is None:
        # Ensure it's fitted before any transform
        vec = _tfidf_vectorizer.fit_transform([text])
    else:
        vec = _tfidf_vectorizer.transform([text])
    
    return vec.toarray()[0].astype(np.float32)

def get_embedding(text: str, fit_tfidf: bool = False) -> np.ndarray:
    """Unified embedding function."""
    if USE_GEMINI:
        try:
            return get_gemini_embedding(text)
        except Exception:
            print("Falling back to TF-IDF due to Gemini error...")
    
    return get_tfidf_embedding(text, fit=fit_tfidf)

def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    if emb1 is None or emb2 is None:
        return 0.0
    # Normalize
    emb1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
    emb2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
    return float(np.dot(emb1, emb2))

def batch_get_embeddings(texts: List[str], use_gemini_first: bool = True) -> List[np.ndarray]:
    """Get embeddings for multiple texts efficiently."""
    embeddings = []
    for i, text in enumerate(texts):
        if i == 0 and not USE_GEMINI:
            emb = get_embedding(text, fit_tfidf=True)
        else:
            emb = get_embedding(text)
        embeddings.append(emb)
    return embeddings

def semantic_similarity(text1: str, text2: str) -> float:
    """Direct semantic similarity between two texts."""
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    return compute_cosine_similarity(emb1, emb2)

if __name__ == "__main__":
    # Test
    t1 = "Senior ML Engineer with Python TensorFlow AWS experience"
    t2 = "Machine Learning Engineer proficient in PyTorch and cloud technologies"
    sim = semantic_similarity(t1, t2)
    print(f"Semantic similarity: {sim:.4f}")
    
    emb = get_embedding(t1)
    print(f"Embedding dim: {len(emb)} , type: {type(emb)}")
