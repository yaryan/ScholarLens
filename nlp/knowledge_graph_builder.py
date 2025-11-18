"""
Knowledge Graph Builder

This module builds the knowledge graph by:
1. Extracting entities from papers
2. Creating nodes in Neo4j and PostgreSQL
3. Creating relationships between entities

Optimized for Windows with 16GB RAM.
"""

from database.postgres_db import PostgresDatabase
from database.neo4j_schema import Neo4jDatabase
from nlp.entity_extractor import EntityExtractor
from typing import Dict, List, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    Build knowledge graph from research papers.

    Features:
    - Extract entities from papers
    - Create nodes in both PostgreSQL and Neo4j
    - Create relationships (AUTHORED, USES_METHOD, etc.)
    - Handle duplicates and conflicts
    """

    def __init__(self):
        """Initialize knowledge graph builder with database connections"""
        logger.info("Initializing Knowledge Graph Builder...")

        try:
            self.postgres_db = PostgresDatabase()
            logger.info("✓ PostgreSQL connected")
        except Exception as e:
            logger.error(f"✗ PostgreSQL failed: {e}")
            raise

        try:
            self.neo4j_db = Neo4jDatabase()
            logger.info("✓ Neo4j connected")
        except Exception as e:
            logger.error(f"✗ Neo4j failed: {e}")
            raise

        try:
            self.entity_extractor = EntityExtractor()
            logger.info("✓ Entity extractor ready")
        except Exception as e:
            logger.error(f"✗ Entity extractor failed: {e}")
            raise

        logger.info("✓ Knowledge Graph Builder initialized")

    def process_paper(self, paper_data: Dict) -> bool:
        """
        Process a single paper and build knowledge graph.

        Args:
            paper_data: Dictionary with paper metadata
                Required: paper_id, title, abstract
                Optional: full_text, authors, published_date

        Returns:
            True if successful
        """
        paper_id = paper_data.get('paper_id')
        title = paper_data.get('title', '')
        abstract = paper_data.get('abstract', '')
        full_text = paper_data.get('full_text', '')

        logger.info(f"Processing paper {paper_id}: {title[:50]}...")

        try:
            # Combine title, abstract, and full text for entity extraction
            combined_text = f"{title}\n\n{abstract}"
            if full_text:
                combined_text += f"\n\n{full_text[:10000]}"  # Limit for memory

            # Extract entities
            entities = self.entity_extractor.extract_entities(combined_text, paper_id)

            # Create paper node in Neo4j
            self.neo4j_db.create_paper_node(
                paper_id=paper_id,
                title=title,
                abstract=abstract,
                published_date=paper_data.get('published_date'),
                categories=paper_data.get('categories'),
                arxiv_id=paper_data.get('arxiv_id')
            )

            # Process authors
            authors = paper_data.get('authors', [])
            if not authors and entities['persons']:
                # Use extracted persons as authors if not provided
                authors = [p['text'] for p in entities['persons'][:10]]  # Limit to 10

            self._process_authors(paper_id, authors)

            # Process methods
            self._process_methods(paper_id, entities['methods'])

            # Process datasets
            self._process_datasets(paper_id, entities['datasets'])

            # Process institutions
            self._process_institutions(paper_id, entities['institutions'])

            logger.info(f"✓ Processed paper {paper_id}")
            return True

        except Exception as e:
            logger.error(f"✗ Error processing paper {paper_id}: {e}")
            return False

    def _process_authors(self, paper_id: int, authors: List[str]):
        """Process authors and create relationships"""
        if not authors:
            return

        author_ids = []

        for idx, author_name in enumerate(authors):
            # Get or create author in PostgreSQL and extract ID immediately
            with self.postgres_db.get_session() as session:
                from database.models import Author
                from sqlalchemy import select

                # Check if author exists
                stmt = select(Author).where(Author.name == author_name)
                author = session.execute(stmt).scalar_one_or_none()

                if not author:
                    author = Author(name=author_name)
                    session.add(author)
                    session.flush()
                    logger.info(f"✓ Added author: {author_name}")

                # Extract ID before session closes
                author_id = author.author_id

            author_ids.append(author_id)

            # Create author node in Neo4j
            self.neo4j_db.create_author_node(author_id, author_name)

            # Create AUTHORED relationship
            self.neo4j_db.create_authored_relationship(
                paper_id,
                author_id,
                position=idx + 1
            )

            # Link in PostgreSQL (with duplicate handling)
            try:
                self.postgres_db.link_paper_author(paper_id, author_id, position=idx + 1)
            except Exception as e:
                if "unique_paper_author" not in str(e).lower():
                    logger.error(f"Error linking author: {e}")

        # Create collaboration relationships
        if len(author_ids) > 1:
            for i in range(len(author_ids)):
                for j in range(i + 1, len(author_ids)):
                    try:
                        self.neo4j_db.create_collaborates_relationship(
                            author_ids[i],
                            author_ids[j],
                            paper_id
                        )
                    except Exception as e:
                        logger.debug(f"Could not create collaboration: {e}")

        logger.debug(f"Processed {len(authors)} authors for paper {paper_id}")

    def _process_methods(self, paper_id: int, methods: List[Dict]):
        """Process methods and create relationships"""
        if not methods:
            return

        for method_data in methods:
            method_name = method_data.get('normalized', method_data['text'])

            # Get or create method in PostgreSQL
            method = self.postgres_db.add_method(method_name)

            # Create method node in Neo4j
            self.neo4j_db.create_method_node(method.method_id, method_name)

            # Create USES_METHOD relationship
            self.neo4j_db.create_uses_method_relationship(
                paper_id,
                method.method_id
            )

            # Link in PostgreSQL
            self.postgres_db.link_paper_method(paper_id, method.method_id)

        logger.debug(f"Processed {len(methods)} methods for paper {paper_id}")

    def _process_datasets(self, paper_id: int, datasets: List[Dict]):
        """Process datasets and create relationships"""
        if not datasets:
            return

        for dataset_data in datasets:
            dataset_name = dataset_data.get('normalized', dataset_data['text'])

            # Get or create dataset in PostgreSQL
            with self.postgres_db.get_session() as session:
                from database.models import Dataset
                from sqlalchemy import select

                stmt = select(Dataset).where(Dataset.name == dataset_name)
                dataset = session.execute(stmt).scalar_one_or_none()

                if not dataset:
                    dataset = Dataset(name=dataset_name)
                    session.add(dataset)
                    session.flush()

                dataset_id = dataset.dataset_id

            # Create dataset node in Neo4j
            self.neo4j_db.create_dataset_node(dataset_id, dataset_name)

            # Create USES_DATASET relationship
            self.neo4j_db.create_uses_dataset_relationship(
                paper_id,
                dataset_id
            )

            # Link in PostgreSQL (with conflict handling)
            try:
                self.postgres_db.execute_query(
                    "INSERT INTO paper_datasets (paper_id, dataset_id) VALUES (:pid, :did) ON CONFLICT DO NOTHING",
                    {'pid': paper_id, 'did': dataset_id}
                )
            except Exception as e:
                logger.debug(f"Dataset link already exists: {e}")

        logger.debug(f"Processed {len(datasets)} datasets for paper {paper_id}")

    def _process_institutions(self, paper_id: int, institutions: List[Dict]):
        """Process institutions"""
        if not institutions:
            return

        for inst_data in institutions:
            inst_name = inst_data['text']

            # Get or create institution in PostgreSQL
            with self.postgres_db.get_session() as session:
                from database.models import Institution
                from sqlalchemy import select

                stmt = select(Institution).where(Institution.name == inst_name)
                institution = session.execute(stmt).scalar_one_or_none()

                if not institution:
                    institution = Institution(name=inst_name)
                    session.add(institution)
                    session.flush()

                institution_id = institution.institution_id

            # Create institution node in Neo4j
            self.neo4j_db.create_institution_node(institution_id, inst_name)

        logger.debug(f"Processed {len(institutions)} institutions for paper {paper_id}")


    def batch_process_papers(self, papers: List[Dict], batch_size: int = 10) -> Dict:
        """
        Process multiple papers in batches.
        Memory-optimized for 16GB RAM.

        Args:
            papers: List of paper dictionaries
            batch_size: Process papers in batches

        Returns:
            Statistics dictionary
        """
        total = len(papers)
        successful = 0
        failed = 0

        logger.info(f"Processing {total} papers in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = papers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total - 1) // batch_size + 1

            logger.info(f"\nBatch {batch_num}/{total_batches}")

            for paper in batch:
                if self.process_paper(paper):
                    successful += 1
                else:
                    failed += 1

            logger.info(f"Batch {batch_num} complete: {successful} success, {failed} failed")

        stats = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }

        logger.info(f"\n✓ Batch processing complete")
        logger.info(f"  Total: {total}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")

        return stats

    def get_statistics(self) -> Dict:
        """Get knowledge graph statistics"""
        pg_stats = self.postgres_db.get_database_statistics()
        neo_stats = self.neo4j_db.get_graph_statistics()

        return {
            'postgresql': pg_stats,
            'neo4j': neo_stats
        }

    def close(self):
        """Close database connections"""
        self.postgres_db.close()
        self.neo4j_db.close()
        logger.info("✓ Knowledge Graph Builder closed")


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("KNOWLEDGE GRAPH BUILDER DEMONSTRATION")
    print("=" * 70)

    builder = KnowledgeGraphBuilder()

    try:
        # Sample paper
        sample_paper = {
            'paper_id': 99999,
            'title': 'Sample Paper on Deep Learning',
            'abstract': 'This paper presents a CNN architecture trained on ImageNet.',
            'authors': ['John Smith', 'Jane Doe'],
            'published_date': '2025-10-29',
            'categories': ['cs.AI'],
            'arxiv_id': 'sample.99999'
        }

        # Process paper
        print("\nProcessing sample paper...")
        success = builder.process_paper(sample_paper)

        if success:
            print("✓ Sample paper processed successfully")

            # Get statistics
            print("\nKnowledge Graph Statistics:")
            stats = builder.get_statistics()

            print("\nPostgreSQL:")
            for key, value in stats['postgresql'].items():
                print(f"  {key}: {value}")

            print("\nNeo4j:")
            for key, value in stats['neo4j'].items():
                print(f"  {key}: {value}")

    finally:
        builder.close()

    print("\n" + "=" * 70)
    print("✓ DEMONSTRATION COMPLETE")
    print("=" * 70)
