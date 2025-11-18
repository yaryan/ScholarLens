"""
End-to-End Pipeline Runner

This script provides a unified interface for running the complete pipeline
with progress tracking and error recovery.

Usage:
    python scripts\pipeline_runner.py --mode full --query "deep learning" --num 20
    python scripts\pipeline_runner.py --mode kg-only --input existing_papers
    python scripts\pipeline_runner.py --mode embeddings-only
"""

import sys

sys.path.append('.')

import argparse
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import logging

from scripts.populate_database import DatabasePopulator
from database.db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Unified pipeline runner with multiple modes.

    Modes:
    - full: Complete pipeline (download, process, KG, embeddings)
    - kg-only: Build knowledge graph from existing papers
    - embeddings-only: Create embeddings from existing papers
    - download-only: Just download papers
    """

    def __init__(self):
        """Initialize pipeline runner"""
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)

        logger.info("Pipeline Runner initialized")

    def run_full_pipeline(self, query: str = None, category: str = None,
                          num_papers: int = 10) -> Dict:
        """
        Run complete pipeline.

        Args:
            query: Search query
            category: arXiv category
            num_papers: Number of papers

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("RUNNING FULL PIPELINE")
        logger.info("=" * 70)

        populator = DatabasePopulator()

        try:
            stats = populator.populate_from_arxiv(
                query=query,
                category=category,
                num_papers=num_papers,
                download_pdfs=True,
                process_pdfs=True
            )

            # Save results
            self._save_results(stats, 'full_pipeline')

            return stats

        finally:
            populator.close()

    def run_kg_only(self) -> Dict:
        """
        Build knowledge graph from existing papers in database.

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("BUILDING KNOWLEDGE GRAPH FROM EXISTING PAPERS")
        logger.info("=" * 70)

        from nlp.knowledge_graph_builder import KnowledgeGraphBuilder
        from database.postgres_db import PostgresDatabase

        pg_db = PostgresDatabase()
        kg_builder = KnowledgeGraphBuilder()

        try:
            # Get all papers from PostgreSQL and convert to dictionaries
            papers_data = []

            with pg_db.get_session() as session:
                from database.models import Paper, Author, PaperAuthor
                from sqlalchemy import select

                papers = session.query(Paper).all()

                logger.info(f"Found {len(papers)} papers in database")

                if not papers:
                    logger.warning("No papers found in database")
                    return {'processed': 0}

                # Extract all data within session context
                for paper in papers:
                    # Get authors for this paper
                    stmt = select(Author).join(PaperAuthor).where(PaperAuthor.paper_id == paper.paper_id)
                    authors = session.execute(stmt).scalars().all()

                    # Create paper data dictionary with all needed fields
                    paper_data = {
                        'paper_id': paper.paper_id,
                        'title': paper.title,
                        'abstract': paper.abstract,
                        'full_text': paper.full_text,
                        'published_date': str(paper.published_date) if paper.published_date else None,
                        'categories': paper.categories if paper.categories else [],
                        'arxiv_id': paper.arxiv_id,
                        'authors': [author.name for author in authors]
                    }

                    papers_data.append(paper_data)

            # Now process papers outside the session
            logger.info(f"Processing {len(papers_data)} papers for knowledge graph...")

            processed = 0
            failed = 0

            for paper_data in papers_data:
                try:
                    kg_builder.process_paper(paper_data)
                    processed += 1
                    logger.info(f"✓ Processed paper {paper_data['paper_id']}: {paper_data['title'][:50]}...")

                except Exception as e:
                    logger.error(f"✗ Error processing paper {paper_data['paper_id']}: {e}")
                    failed += 1

            stats = {
                'total_papers': len(papers_data),
                'processed': processed,
                'failed': failed
            }

            logger.info(f"\n✓ Knowledge graph built: {processed}/{len(papers_data)} papers")

            self._save_results(stats, 'kg_only')

            return stats

        finally:
            pg_db.close()
            kg_builder.close()

    def run_embeddings_only(self, batch_size: int = 10) -> Dict:
        """
        Create embeddings from existing papers in database.

        Args:
            batch_size: Batch size for processing

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("CREATING EMBEDDINGS FROM EXISTING PAPERS")
        logger.info("=" * 70)

        from nlp.embedding_pipeline import EmbeddingPipeline
        from database.postgres_db import PostgresDatabase

        pg_db = PostgresDatabase()
        embedding_pipeline = EmbeddingPipeline()

        try:
            # Get all papers and extract data within session
            embedding_papers = []

            with pg_db.get_session() as session:
                from database.models import Paper
                papers = session.query(Paper).all()

                logger.info(f"Found {len(papers)} papers in database")

                if not papers:
                    logger.warning("No papers found in database")
                    return {'processed': 0}

                # Extract all data within session context
                for paper in papers:
                    text = f"{paper.title}\n\n{paper.abstract or ''}"
                    if paper.full_text:
                        text += f"\n\n{paper.full_text[:10000]}"

                    embedding_papers.append({
                        'paper_id': paper.paper_id,
                        'text': text,
                        'metadata': {
                            'title': paper.title,
                            'arxiv_id': paper.arxiv_id
                        }
                    })

            # Now create embeddings outside session
            logger.info(f"Creating embeddings for {len(embedding_papers)} papers...")
            stats = embedding_pipeline.batch_process_papers(embedding_papers, batch_size=batch_size)

            logger.info(f"\n✓ Embeddings created: {stats['total_chunks']} chunks")

            self._save_results(stats, 'embeddings_only')

            return stats

        finally:
            pg_db.close()

    def run_download_only(self, query: str = None, category: str = None,
                          num_papers: int = 10) -> Dict:
        """
        Download papers only (no processing).

        Args:
            query: Search query
            category: arXiv category
            num_papers: Number of papers

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOADING PAPERS ONLY")
        logger.info("=" * 70)

        populator = DatabasePopulator()

        try:
            stats = populator.populate_from_arxiv(
                query=query,
                category=category,
                num_papers=num_papers,
                download_pdfs=True,
                process_pdfs=False
            )

            self._save_results(stats, 'download_only')

            return stats

        finally:
            populator.close()

    def get_system_status(self) -> Dict:
        """
        Get current status of the system.

        Returns:
            Status dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("SYSTEM STATUS CHECK")
        logger.info("=" * 70)

        with DatabaseManager() as db_manager:
            stats = db_manager.get_complete_statistics()

        # Display PostgreSQL stats
        logger.info("\nPostgreSQL:")
        pg_stats = stats.get('postgresql', {})
        if pg_stats:
            for key, value in pg_stats.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("  No PostgreSQL statistics available")

        # Display Neo4j stats
        logger.info("\nNeo4j:")
        neo_stats = stats.get('neo4j', {})
        if neo_stats:
            for key, value in neo_stats.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("  No Neo4j statistics available")

        # Display FAISS stats
        logger.info("\nFAISS Vector Store:")
        faiss_stats = stats.get('vector_store', {})
        if faiss_stats:
            for key, value in faiss_stats.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("  No FAISS statistics available")

        logger.info("\n" + "=" * 70)

        return stats

    def _save_results(self, stats: Dict, mode: str):
        """Save pipeline results to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.results_dir / f'{mode}_{timestamp}.json'

        result = {
            'mode': mode,
            'timestamp': timestamp,
            'statistics': stats
        }

        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"\n✓ Results saved to: {filename}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run research paper processing pipeline')

    parser.add_argument('--mode', type=str, required=True,
                        choices=['full', 'kg-only', 'embeddings-only', 'download-only', 'status'],
                        help='Pipeline mode')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--category', type=str, help='arXiv category')
    parser.add_argument('--num', type=int, default=10, help='Number of papers')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')

    args = parser.parse_args()

    runner = PipelineRunner()

    try:
        if args.mode == 'full':
            if not args.query and not args.category:
                parser.error("Full mode requires --query or --category")
            stats = runner.run_full_pipeline(args.query, args.category, args.num)

        elif args.mode == 'kg-only':
            stats = runner.run_kg_only()

        elif args.mode == 'embeddings-only':
            stats = runner.run_embeddings_only(args.batch_size)

        elif args.mode == 'download-only':
            if not args.query and not args.category:
                parser.error("Download mode requires --query or --category")
            stats = runner.run_download_only(args.query, args.category, args.num)

        elif args.mode == 'status':
            stats = runner.get_system_status()

        print("\n" + "=" * 70)
        print("✓ PIPELINE COMPLETE")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
