"""
RAG Candidate Search using FAISS
Natural language semantic search over candidate embeddings.
"""
import faiss
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from embeddings.embedding_engine import get_embedding, compute_cosine_similarity, batch_get_embeddings
import os
import pickle

class CandidateVectorStore:
    """In-memory FAISS vector store for candidates."""
    
    def __init__(self, dimension: int = 768):  # Gemini default 768, TFIDF will be 512
        self.dimension = dimension
        self.index = None
        self.candidates: List[Dict[str, Any]] = []
        self.embeddings: List[np.ndarray] = []
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Initialize or rebuild FAISS index."""
        if len(self.embeddings) == 0:
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product = cosine after norm
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            # Add normalized embeddings
            embs = np.array([self._normalize(e) for e in self.embeddings]).astype('float32')
            self.index.add(embs)
    
    def _normalize(self, emb: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(emb) + 1e-8
        return emb / norm
    
    def add_candidates(self, candidates: List[Dict[str, Any]]):
        """Add or update candidates with their embeddings."""
        new_embs = []
        for cand in candidates:
            # Use raw_text or constructed text for embedding
            text_repr = self._candidate_to_text(cand)
            try:
                emb = get_embedding(text_repr)
                if len(emb) != self.dimension:
                    # Handle TF-IDF dim mismatch by padding or re-init
                    if self.dimension == 768 and len(emb) == 512:
                        # pad
                        emb = np.pad(emb, (0, 256), 'constant')
                    elif len(emb) < self.dimension:
                        emb = np.pad(emb, (0, self.dimension - len(emb)), 'constant')
                    else:
                        emb = emb[:self.dimension]
                
                self.embeddings.append(emb)
                new_embs.append(emb)
                self.candidates.append(cand)
            except Exception as e:
                print(f"Embedding error for {cand.get('name')}: {e}")
        
        if new_embs:
            self._rebuild_index()
    
    def _candidate_to_text(self, cand: Dict[str, Any]) -> str:
        """Create rich text representation for embedding."""
        parts = [
            cand.get("name", ""),
            " ".join(cand.get("skills", [])),
            f"{cand.get('experience_years', 0)} years experience",
            " ".join(cand.get("projects", [])),
            cand.get("education", "")
        ]
        return " . ".join([p for p in parts if p])
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search for candidates matching natural language query."""
        if not self.candidates or self.index is None or self.index.ntotal == 0:
            return []
        
        query_emb = get_embedding(query)
        if len(query_emb) != self.dimension:
            if self.dimension == 768 and len(query_emb) == 512:
                query_emb = np.pad(query_emb, (0, 256), 'constant')
            else:
                query_emb = np.resize(query_emb, self.dimension)
        
        query_emb = self._normalize(query_emb).astype('float32').reshape(1, -1)
        
        # Search
        scores, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.candidates):
                cand = self.candidates[idx].copy()
                cand["search_similarity"] = float(score)  # since IP after norm ~ cosine
                results.append(cand)
        
        return results
    
    def save(self, path: str):
        """Persist the store (embeddings + metadata)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'candidates': self.candidates,
                'embeddings': [e.tolist() for e in self.embeddings],
                'dimension': self.dimension
            }, f)
        print(f"Vector store saved to {path}")
    
    def load(self, path: str):
        """Load persisted store."""
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.candidates = data['candidates']
            self.embeddings = [np.array(e, dtype=np.float32) for e in data['embeddings']]
            self.dimension = data['dimension']
            self._rebuild_index()
            print(f"Vector store loaded from {path} with {len(self.candidates)} candidates")

# Global store instance (for Streamlit session)
vector_store = CandidateVectorStore()

if __name__ == "__main__":
    # Demo
    store = CandidateVectorStore()
    test_cands = [
        {"name": "John", "skills": ["Python", "TensorFlow", "NLP"], "experience_years": 4, "projects": ["LLM RAG"]},
        {"name": "Jane", "skills": ["Python", "Scikit-learn"], "experience_years": 2, "projects": ["Churn Prediction"]}
    ]
    store.add_candidates(test_cands)
    results = store.search("candidates with NLP and LLM experience", top_k=2)
    for r in results:
        print(r["name"], r.get("search_similarity"))
