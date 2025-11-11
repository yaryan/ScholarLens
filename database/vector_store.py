"""
FAISS Vector Store Manager

This module provides vector storage and semantic search capabilities
using Facebook AI Similarity Search (FAISS).

Optimized for 16GB RAM Windows system.
"""

import faiss
import numpy as np
import pickle
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """
    FAISS-based vector store for semantic search.

    Features:
    - Efficient similarity search
    - Persistent storage
    - Batch operations
    - Memory-optimized for 16GB RAM
    """

    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2',
                 dimension: int = 384,
                 index_path: Optional[str] = None,
                 metadata_path: Optional[str] = None):
        """
        Initialize FAISS vector store.

        Args:
            embedding_model: HuggingFace sentence transformer model
            dimension: Embedding dimension
            index_path: Path to saved FAISS index
            metadata_path: Path to saved metadata
        """
        self.embedding_model_name = embedding_model
        self.dimension = dimension
        self.index = None
        self.id_map = {}  # Maps vector index to document metadata
        self.next_id = 0

        # Set paths
        self.index_path = Path(index_path) if index_path else Path('./data/faiss_index/index.faiss')
        self.metadata_path = Path(metadata_path) if metadata_path else Path('./data/faiss_index/metadata.pkl')

        # Create directories
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize model
        try:
            logger.info(f"Loading embedding model: {embedding_model}")
            self.model = SentenceTransformer(embedding_model)
            logger.info(f"✓ Model loaded: {embedding_model}")
        except Exception as e:
            logger.error(f"✗ Failed to load model: {e}")
            raise

        # Try to load existing index
        if self.index_path.exists() and self.metadata_path.exists():
            self.load()
        else:
            logger.info("No existing index found, will create new one")

    def create_index(self, index_type: str = 'flat', nlist: int = 100):
        """
        Create FAISS index.

        Args:
            index_type: 'flat' (exact, slower) or 'ivf' (approximate, faster)
            nlist: Number of clusters for IVF (ignored for flat)
        """
        if index_type == 'flat':
            # Exact search using L2 distance
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"✓ Created Flat index (dimension={self.dimension})")

        elif index_type == 'ivf':
            # Approximate search for larger datasets
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            logger.info(f"✓ Created IVF index (dimension={self.dimension}, nlist={nlist})")
            logger.info("⚠ IVF index requires training before adding vectors")

        else:
            raise ValueError(f"Unknown index type: {index_type}")

    def train_index(self, training_texts: List[str]):
        """
        Train IVF index (only needed for IVF index type).

        Args:
            training_texts: Texts to use for training
        """
        if not isinstance(self.index, faiss.IndexIVFFlat):
            logger.info("Index does not require training")
            return

        if self.index.is_trained:
            logger.info("Index is already trained")
            return

        logger.info(f"Training index with {len(training_texts)} samples...")

        # Generate embeddings for training
        embeddings = self.model.encode(
            training_texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=32
        )

        # Normalize
        faiss.normalize_L2(embeddings)

        # Train
        self.index.train(embeddings)
        logger.info("✓ Index training complete")

    def add_documents(self, texts: List[str], metadata_list: List[Dict],
                      batch_size: int = 32) -> int:
        """
        Add documents to the vector store.

        Args:
            texts: List of text strings
            metadata_list: List of metadata dicts for each text
            batch_size: Batch size for encoding (memory optimization)

        Returns:
            Number of documents added
        """
        if not texts:
            logger.warning("No texts provided")
            return 0

        if len(texts) != len(metadata_list):
            raise ValueError("texts and metadata_list must have same length")

        # Create index if not exists
        if self.index is None:
            self.create_index(index_type='flat')

        logger.info(f"Adding {len(texts)} documents...")

        # Generate embeddings in batches to manage memory
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            batch_embeddings = self.model.encode(
                batch_texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=batch_size
            )

            all_embeddings.append(batch_embeddings)

        # Concatenate all batches
        embeddings = np.vstack(all_embeddings)

        # Normalize embeddings (recommended for cosine similarity)
        faiss.normalize_L2(embeddings)

        # Add to index
        self.index.add(embeddings)

        # Store metadata
        for i, metadata in enumerate(metadata_list):
            self.id_map[self.next_id + i] = metadata

        self.next_id += len(texts)

        logger.info(f"✓ Added {len(texts)} documents. Total: {self.index.ntotal}")
        return len(texts)

    def search(self, query_text: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for most similar documents.

        Args:
            query_text: Query string
            top_k: Number of results to return

        Returns:
            List of tuples (metadata, similarity_score)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []

        # Generate query embedding
        query_embedding = self.model.encode(
            [query_text],
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # Normalize
        faiss.normalize_L2(query_embedding)

        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        # Retrieve metadata
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self.id_map and idx != -1:  # -1 means no result
                # Convert L2 distance to similarity score (0-1, higher is better)
                similarity = 1 / (1 + dist)
                results.append((self.id_map[idx], float(similarity)))

        logger.info(f"✓ Found {len(results)} results for query")
        return results

    def batch_search(self, queries: List[str], top_k: int = 5) -> List[List[Tuple[Dict, float]]]:
        """
        Batch search for multiple queries.

        Args:
            queries: List of query strings
            top_k: Number of results per query

        Returns:
            List of result lists (one per query)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return [[] for _ in queries]

        logger.info(f"Searching {len(queries)} queries...")

        # Generate query embeddings
        query_embeddings = self.model.encode(
            queries,
            convert_to_numpy=True,
            show_progress_bar=True,
            batch_size=32
        )

        # Normalize
        faiss.normalize_L2(query_embeddings)

        # Batch search
        distances, indices = self.index.search(query_embeddings, min(top_k, self.index.ntotal))

        # Process results
        all_results = []
        for dist_row, idx_row in zip(distances, indices):
            query_results = []
            for dist, idx in zip(dist_row, idx_row):
                if idx in self.id_map and idx != -1:
                    similarity = 1 / (1 + dist)
                    query_results.append((self.id_map[idx], float(similarity)))
            all_results.append(query_results)

        logger.info(f"✓ Batch search complete")
        return all_results

    def save(self):
        """Save index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))

            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'id_map': self.id_map,
                    'next_id': self.next_id,
                    'embedding_model': self.embedding_model_name,
                    'dimension': self.dimension
                }, f)

            logger.info(f"✓ Saved index to: {self.index_path}")
            logger.info(f"✓ Saved metadata to: {self.metadata_path}")

        except Exception as e:
            logger.error(f"✗ Error saving: {e}")
            raise

    def load(self):
        """Load index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))

            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_map = data['id_map']
                self.next_id = data['next_id']

                # Verify model compatibility
                if data['embedding_model'] != self.embedding_model_name:
                    logger.warning(
                        f"Model mismatch: saved={data['embedding_model']}, current={self.embedding_model_name}")

            logger.info(f"✓ Loaded index with {self.index.ntotal} vectors")
            logger.info(f"✓ Loaded {len(self.id_map)} metadata entries")

        except Exception as e:
            logger.error(f"✗ Error loading: {e}")
            raise

    def delete_by_ids(self, ids_to_delete: List[int]):
        """
        Delete documents by their internal IDs.

        Note: FAISS doesn't support deletion directly, so this recreates the index.
        """
        logger.info(f"Deleting {len(ids_to_delete)} documents...")

        # Get all current vectors and metadata
        all_embeddings = []
        new_id_map = {}
        new_id = 0

        for idx in range(self.next_id):
            if idx not in ids_to_delete and idx in self.id_map:
                # Reconstruct vector (this is expensive)
                vector = self.index.reconstruct(idx)
                all_embeddings.append(vector)
                new_id_map[new_id] = self.id_map[idx]
                new_id += 1

        # Create new index
        self.create_index()

        if all_embeddings:
            embeddings_array = np.array(all_embeddings)
            self.index.add(embeddings_array)

        self.id_map = new_id_map
        self.next_id = new_id

        logger.info(f"✓ Deleted {len(ids_to_delete)} documents. Remaining: {self.index.ntotal}")

    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'embedding_model': self.embedding_model_name,
            'index_type': type(self.index).__name__ if self.index else None,
            'metadata_entries': len(self.id_map)
        }

    def clear(self):
        """Clear all vectors and metadata"""
        self.create_index()
        self.id_map = {}
        self.next_id = 0
        logger.info("✓ Vector store cleared")


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FAISS VECTOR STORE DEMONSTRATION")
    print("=" * 70)

    # Initialize vector store
    vector_store = FAISSVectorStore()

    # Sample documents
    texts = [
        "Transformers have revolutionized natural language processing through attention mechanisms.",
        "Convolutional neural networks are highly effective for computer vision tasks like image classification.",
        "Reinforcement learning enables agents to learn optimal policies through interaction with environments.",
        "Graph neural networks can process data with graph-structured relationships effectively.",
        "BERT uses bidirectional transformers for pre-training language representations."
    ]

    metadata = [
        {'doc_id': 1, 'title': 'Attention is All You Need', 'topic': 'nlp'},
        {'doc_id': 2, 'title': 'ImageNet Classification', 'topic': 'cv'},
        {'doc_id': 3, 'title': 'Deep Q-Networks', 'topic': 'rl'},
        {'doc_id': 4, 'title': 'Graph Convolutional Networks', 'topic': 'graph'},
        {'doc_id': 5, 'title': 'BERT Pre-training', 'topic': 'nlp'}
    ]

    # Add documents
    print("\nAdding documents...")
    print("-" * 70)
    vector_store.add_documents(texts, metadata)

    # Search
    print("\nSearching...")
    print("-" * 70)
    query = "How do transformers work in NLP?"
    results = vector_store.search(query, top_k=3)

    print(f"Query: '{query}'")
    print(f"\nTop {len(results)} results:")
    for i, (meta, score) in enumerate(results, 1):
        print(f"{i}. {meta['title']} (similarity: {score:.4f})")
        print(f"   Topic: {meta['topic']}")

    # Get statistics
    print("\nStatistics:")
    print("-" * 70)
    stats = vector_store.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Save
    print("\nSaving...")
    print("-" * 70)
    vector_store.save()

    print("\n" + "=" * 70)
    print("✓ FAISS DEMONSTRATION COMPLETE")
    print("=" * 70)
