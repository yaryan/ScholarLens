"""
Unified Database Manager

This module provides a unified interface for all database operations
across PostgreSQL, Neo4j, and FAISS.
"""

from database.postgres_db import PostgresDatabase
from database.neo4j_schema import Neo4jDatabase
from database.vector_store import FAISSVectorStore
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Unified database manager for all database operations.

    Coordinates operations across:
    - PostgreSQL (structured metadata)
    - Neo4j (knowledge graph)
    - FAISS (vector embeddings)
    """

    def __init__(self):
        """Initialize all database connections"""
        logger.info("Initializing Database Manager...")

        try:
            self.postgres = PostgresDatabase()
            logger.info("✓ PostgreSQL connected")
        except Exception as e:
            logger.error(f"✗ PostgreSQL failed: {e}")
            self.postgres = None

        try:
            self.neo4j = Neo4jDatabase()
            logger.info("✓ Neo4j connected")
        except Exception as e:
            logger.error(f"✗ Neo4j failed: {e}")
            self.neo4j = None

        try:
            self.vector_store = FAISSVectorStore()
            logger.info("✓ FAISS vector store ready")
        except Exception as e:
            logger.error(f"✗ FAISS failed: {e}")
            self.vector_store = None

        logger.info("✓ Database Manager initialized")

    def close_all(self):
        """Close all database connections"""
        if self.postgres:
            self.postgres.close()
        if self.neo4j:
            self.neo4j.close()
        if self.vector_store:
            self.vector_store.save()

        logger.info("✓ All connections closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()

    # ========== UNIFIED OPERATIONS ==========

    def add_paper_complete(self, paper_data: Dict, authors: List[Dict],
                           methods: List[str] = None, datasets: List[str] = None) -> int:
        """
        Add a paper to all databases (PostgreSQL, Neo4j, and optionally FAISS).

        Args:
            paper_data: Paper metadata dictionary
            authors: List of author dictionaries
            methods: List of method names
            datasets: List of dataset names

        Returns:
            Paper ID
        """
        logger.info(f"Adding paper: {paper_data.get('title', 'Unknown')[:50]}...")

        # 1. Add to PostgreSQL
        paper = self.postgres.add_paper(paper_data)
        paper_id = paper.paper_id

        # 2. Add authors to PostgreSQL and link
        for idx, author_data in enumerate(authors):
            author = self.postgres.add_author(author_data['name'])
            self.postgres.link_paper_author(paper_id, author.author_id, position=idx)

        # 3. Add to Neo4j
        if self.neo4j:
            self.neo4j.create_paper_node(
                paper_id=paper_id,
                title=paper_data['title'],
                abstract=paper_data.get('abstract'),
                published_date=paper_data.get('published_date'),
                categories=paper_data.get('categories'),
                arxiv_id=paper_data.get('arxiv_id')
            )

            # Add authors and relationships in Neo4j
            for idx, author_data in enumerate(authors):
                author = self.postgres.add_author(author_data['name'])
                self.neo4j.create_author_node(author.author_id, author_data['name'])
                self.neo4j.create_authored_relationship(paper_id, author.author_id, position=idx)

            # Add methods if provided
            if methods:
                for method_name in methods:
                    method = self.postgres.add_method(method_name)
                    self.neo4j.create_method_node(method.method_id, method_name)
                    self.neo4j.create_uses_method_relationship(paper_id, method.method_id)

        logger.info(f"✓ Paper added completely: ID={paper_id}")
        return paper_id

    def search_papers_semantic(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Semantic search using FAISS vector store.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of paper dictionaries with similarity scores
        """
        if not self.vector_store:
            logger.warning("Vector store not available")
            return []

        # Search in vector store
        results = self.vector_store.search(query, top_k=top_k)

        # Enrich with PostgreSQL data
        enriched_results = []
        for metadata, score in results:
            paper_id = metadata.get('paper_id')
            if paper_id:
                paper = self.postgres.get_paper_by_id(paper_id)
                if paper:
                    enriched_results.append({
                        'paper': paper,
                        'similarity_score': score,
                        'chunk_text': metadata.get('chunk_text', '')
                    })

        return enriched_results

    def get_author_network(self, author_id: int) -> Dict:
        """
        Get complete author network from Neo4j.

        Args:
            author_id: Author ID

        Returns:
            Dictionary with papers, collaborators, institutions
        """
        if not self.neo4j:
            logger.warning("Neo4j not available")
            return {}

        return {
            'papers': self.neo4j.get_author_papers(author_id),
            'collaborators': self.neo4j.get_author_collaborators(author_id),
        }

    def get_complete_statistics(self) -> Dict:
        """Get statistics from all databases"""
        stats = {}

        # PostgreSQL stats
        if self.postgres:
            try:
                stats['postgresql'] = self.postgres.get_database_statistics()
            except Exception as e:
                logger.error(f"Error getting PostgreSQL stats: {e}")
                stats['postgresql'] = {}
        else:
            stats['postgresql'] = {}

        # Neo4j stats
        if self.neo4j:
            try:
                stats['neo4j'] = self.neo4j.get_graph_statistics()
            except Exception as e:
                logger.error(f"Error getting Neo4j stats: {e}")
                stats['neo4j'] = {}
        else:
            stats['neo4j'] = {}

        # FAISS stats
        if self.vector_store:
            try:
                stats['vector_store'] = self.vector_store.get_statistics()
            except Exception as e:
                logger.error(f"Error getting FAISS stats: {e}")
                stats['vector_store'] = {}
        else:
            stats['vector_store'] = {}

        return stats


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("UNIFIED DATABASE MANAGER DEMONSTRATION")
    print("=" * 70)

    with DatabaseManager() as db_manager:
        # Get complete statistics
        print("\nComplete Database Statistics:")
        print("-" * 70)

        stats = db_manager.get_complete_statistics()

        print("\nPostgreSQL:")
        for key, value in stats['postgres'].items():
            print(f"  {key}: {value}")

        print("\nNeo4j:")
        for key, value in stats['neo4j'].items():
            print(f"  {key}: {value}")

        print("\nFAISS Vector Store:")
        for key, value in stats['vector_store'].items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✓ DEMONSTRATION COMPLETE")
    print("=" * 70)
