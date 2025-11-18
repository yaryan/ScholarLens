"""
Embedding Pipeline for Semantic Search

This module creates vector embeddings from paper text and stores them in FAISS.

Features:
- Text chunking with overlap
- Batch embedding generation
- FAISS index management
- Memory-optimized for 16GB RAM
"""

from database.vector_store import FAISSVectorStore
from processing.text_preprocessor import TextPreprocessor
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Create and manage embeddings for semantic search.

    Features:
    - Automatic text chunking
    - Batch embedding generation
    - Metadata tracking
    - Memory-efficient processing
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize embedding pipeline.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
        """
        logger.info("Initializing Embedding Pipeline...")

        try:
            self.vector_store = FAISSVectorStore()
            logger.info("✓ Vector store ready")
        except Exception as e:
            logger.error(f"✗ Vector store failed: {e}")
            raise

        try:
            self.text_preprocessor = TextPreprocessor()
            logger.info("✓ Text preprocessor ready")
        except Exception as e:
            logger.error(f"✗ Text preprocessor failed: {e}")
            raise

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        logger.info(f"✓ Embedding Pipeline initialized (chunk_size={chunk_size}, overlap={chunk_overlap})")

    def process_paper(self, paper_id: int, paper_text: str,
                      metadata: Dict = None) -> int:
        """
        Process a single paper and create embeddings.

        Args:
            paper_id: Paper ID
            paper_text: Full paper text (title + abstract + body)
            metadata: Additional metadata to store

        Returns:
            Number of chunks created
        """
        logger.info(f"Creating embeddings for paper {paper_id}...")

        try:
            # Preprocess text for embeddings (light normalization)
            preprocessed = self.text_preprocessor.preprocess_for_embeddings(paper_text)

            # Chunk text
            chunks = self.text_preprocessor.chunk_text(
                preprocessed,
                chunk_size=self.chunk_size,
                overlap=self.chunk_overlap,
                by_sentences=True  # Preserve sentence boundaries
            )

            if not chunks:
                logger.warning(f"No chunks created for paper {paper_id}")
                return 0

            # Prepare texts and metadata for FAISS
            chunk_texts = [chunk['text'] for chunk in chunks]
            chunk_metadata = []

            for chunk in chunks:
                meta = {
                    'paper_id': paper_id,
                    'chunk_id': chunk['chunk_id'],
                    'chunk_text': chunk['text'][:200],  # Store preview
                    'num_tokens': chunk['num_tokens']
                }

                # Add custom metadata if provided
                if metadata:
                    meta.update(metadata)

                chunk_metadata.append(meta)

            # Add to vector store
            self.vector_store.add_documents(chunk_texts, chunk_metadata, batch_size=32)

            logger.info(f"✓ Created {len(chunks)} embeddings for paper {paper_id}")
            return len(chunks)

        except Exception as e:
            logger.error(f"✗ Error processing paper {paper_id}: {e}")
            return 0

    def batch_process_papers(self, papers: List[Dict], batch_size: int = 5) -> Dict:
        """
        Process multiple papers in batches.
        Memory-optimized for 16GB RAM.

        Args:
            papers: List of paper dictionaries with 'paper_id' and 'text'
            batch_size: Process papers in batches

        Returns:
            Statistics dictionary
        """
        total = len(papers)
        total_chunks = 0
        successful = 0
        failed = 0

        logger.info(f"Processing {total} papers for embeddings in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = papers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total - 1) // batch_size + 1

            logger.info(f"\nBatch {batch_num}/{total_batches}")

            for paper in batch:
                paper_id = paper['paper_id']
                paper_text = paper.get('text', '')
                metadata = paper.get('metadata', {})

                num_chunks = self.process_paper(paper_id, paper_text, metadata)

                if num_chunks > 0:
                    successful += 1
                    total_chunks += num_chunks
                else:
                    failed += 1

            logger.info(f"Batch {batch_num} complete: {successful} papers processed")

        # Save vector store
        self.vector_store.save()

        stats = {
            'total_papers': total,
            'successful': successful,
            'failed': failed,
            'total_chunks': total_chunks,
            'avg_chunks_per_paper': total_chunks / successful if successful > 0 else 0
        }

        logger.info(f"\n✓ Batch embedding complete")
        logger.info(f"  Papers processed: {successful}/{total}")
        logger.info(f"  Total chunks: {total_chunks}")
        logger.info(f"  Avg chunks/paper: {stats['avg_chunks_per_paper']:.1f}")

        return stats

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for similar text chunks.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of similar chunks with metadata
        """
        results = self.vector_store.search(query, top_k=top_k)
        return [
            {
                'paper_id': metadata['paper_id'],
                'chunk_text': metadata['chunk_text'],
                'similarity': score
            }
            for metadata, score in results
        ]

    def get_statistics(self) -> Dict:
        """Get embedding pipeline statistics"""
        return self.vector_store.get_statistics()


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("EMBEDDING PIPELINE DEMONSTRATION")
    print("=" * 70)

    pipeline = EmbeddingPipeline()

    # Sample papers
    sample_papers = [
        {
            'paper_id': 1,
            'text': 'This paper introduces a novel CNN architecture for image classification. '
                    'We evaluate on ImageNet and achieve state-of-the-art results.',
            'metadata': {'title': 'CNN Paper', 'year': 2025}
        },
        {
            'paper_id': 2,
            'text': 'Transformers have revolutionized NLP. We propose a new attention mechanism '
                    'that improves efficiency and performance on multiple benchmarks.',
            'metadata': {'title': 'Transformer Paper', 'year': 2025}
        }
    ]

    # Process papers
    print("\nProcessing sample papers...")
    stats = pipeline.batch_process_papers(sample_papers, batch_size=2)

    print("\n\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Search
    print("\n\nSearching for similar content...")
    query = "image classification neural networks"
    results = pipeline.search_similar(query, top_k=3)

    print(f"\nQuery: '{query}'")
    print(f"\nTop {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Paper ID: {result['paper_id']}")
        print(f"   Similarity: {result['similarity']:.4f}")
        print(f"   Text: {result['chunk_text']}...")

    print("\n" + "=" * 70)
    print("✓ EMBEDDING PIPELINE COMPLETE")
    print("=" * 70)
