"""
Embedding generation for RAG retrieval.
Uses a small local sentence-transformers model so retrieval works without
per-query API calls; embeddings are computed once and persisted via pgvector.
"""

from typing import List
import streamlit as st

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts. Empty/whitespace-only strings embed to an all-zero vector."""
    model = get_embedding_model()
    cleaned = [t if t and t.strip() else " " for t in texts]
    vectors = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]
