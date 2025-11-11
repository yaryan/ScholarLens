"""
Populate Database with Research Papers

This script orchestrates the complete pipeline:
1. Download papers from arXiv
2. Parse PDFs
3. Extract entities
4. Build knowledge graph
5. Create embeddings

Usage:
    python scripts\populate_database.py --query "machine learning" --num 20
    python scripts\populate_database.py --category cs.AI --num 50
"""

import sys
sys.path.append('.')

from typing import Dict, List  # ← ADD THIS LINE
from data_sources.arxiv_client import ArxivClient
from processing.pdf_parser import PDFParser
from database.postgres_db import PostgresDatabase
from nlp.knowledge_graph_builder import KnowledgeGraphBuilder
from nlp.embedding_pipeline import EmbeddingPipeline
import argparse
import logging
from pathlib import Path
from datetime import datetime


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/populate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabasePopulator:
    """
    Orchestrate the complete pipeline for populating the database.

    Memory-optimized for Windows 16GB RAM system.
    """

    def __init__(self):
        """Initialize all components"""
        logger.info("=" * 70)
        logger.info("INITIALIZING DATABASE POPULATOR")
        logger.info("=" * 70)

        self.arxiv_client = ArxivClient()
        self.postgres_db = PostgresDatabase()
        self.kg_builder = KnowledgeGraphBuilder()
        self.embedding_pipeline = EmbeddingPipeline()

        logger.info("✓ All components initialized")

    def populate_from_arxiv(self, query: str = None, category: str = None,
                            num_papers: int = 10, download_pdfs: bool = True,
                            process_pdfs: bool = True) -> Dict:
        """
        Complete pipeline: download, process, and populate.

        Args:
            query: Search query
            category: arXiv category
            num_papers: Number of papers to process
            download_pdfs: Whether to download PDFs
            process_pdfs: Whether to extract text from PDFs

        Returns:
            Statistics dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"STARTING POPULATION PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Query: {query}")
        logger.info(f"Category: {category}")
        logger.info(f"Papers to process: {num_papers}")

        stats = {
            'papers_fetched': 0,
            'papers_downloaded': 0,
            'papers_parsed': 0,
            'papers_in_db': 0,
            'kg_created': 0,
            'embeddings_created': 0
        }

        try:
            # Step 1: Search and fetch papers
            logger.info("\n[1/5] Fetching papers from arXiv...")
            papers = self.arxiv_client.search_papers(
                query=query or "",
                category=category,
                max_results=num_papers
            )
            stats['papers_fetched'] = len(papers)
            logger.info(f"✓ Fetched {len(papers)} papers")

            if not papers:
                logger.warning("No papers found. Exiting.")
                return stats

            # Step 2: Download PDFs (optional)
            if download_pdfs:
                logger.info("\n[2/5] Downloading PDFs...")
                papers = self.arxiv_client.batch_download(papers, max_downloads=num_papers)
                stats['papers_downloaded'] = sum(1 for p in papers if p.get('pdf_path'))
                logger.info(f"✓ Downloaded {stats['papers_downloaded']} PDFs")
            else:
                logger.info("\n[2/5] Skipping PDF download")

            # Step 3: Parse PDFs and extract text (optional)
            if process_pdfs and download_pdfs:
                logger.info("\n[3/5] Parsing PDFs and extracting text...")
                papers_with_text = self._parse_pdfs(papers)
                stats['papers_parsed'] = len(papers_with_text)
                logger.info(f"✓ Parsed {stats['papers_parsed']} PDFs")
            else:
                logger.info("\n[3/5] Using abstracts only (PDF parsing skipped)")
                papers_with_text = papers

            # Step 4: Add to PostgreSQL and build knowledge graph
            logger.info("\n[4/5] Adding to database and building knowledge graph...")
            processed_papers = self._add_to_database(papers_with_text)
            stats['papers_in_db'] = len(processed_papers)
            stats['kg_created'] = len(processed_papers)
            logger.info(f"✓ Added {stats['papers_in_db']} papers to database")

            # Step 5: Create embeddings
            logger.info("\n[5/5] Creating embeddings for semantic search...")
            embedding_stats = self._create_embeddings(processed_papers)
            stats['embeddings_created'] = embedding_stats['total_chunks']
            logger.info(f"✓ Created {stats['embeddings_created']} embeddings")

            # Final statistics
            logger.info("\n" + "=" * 70)
            logger.info("POPULATION COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Papers fetched: {stats['papers_fetched']}")
            logger.info(f"PDFs downloaded: {stats['papers_downloaded']}")
            logger.info(f"PDFs parsed: {stats['papers_parsed']}")
            logger.info(f"Papers in database: {stats['papers_in_db']}")
            logger.info(f"Knowledge graph nodes: {stats['kg_created']}")
            logger.info(f"Embeddings created: {stats['embeddings_created']}")
            logger.info("=" * 70)

            return stats

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return stats

    def _parse_pdfs(self, papers: List[Dict]) -> List[Dict]:
        """Parse PDFs and extract text"""
        papers_with_text = []

        for paper in papers:
            if not paper.get('pdf_path'):
                continue

            try:
                parser = PDFParser(paper['pdf_path'])
                text = parser.extract_text()
                cleaned = parser.clean_text()

                paper['full_text'] = cleaned
                paper['text_extracted'] = True
                papers_with_text.append(paper)

            except Exception as e:
                logger.warning(f"Could not parse {paper.get('arxiv_id')}: {e}")
                # Still include paper with just abstract
                paper['full_text'] = paper.get('abstract', '')
                paper['text_extracted'] = False
                papers_with_text.append(paper)

        return papers_with_text

    def _add_to_database(self, papers: List[Dict]) -> List[Dict]:
        """Add papers to PostgreSQL and Neo4j, build knowledge graph"""
        processed = []

        for paper in papers:
            try:
                # Check if paper already exists
                existing = self.postgres_db.get_paper_by_arxiv_id(paper['arxiv_id'])

                if existing:
                    logger.info(f"Paper {paper['arxiv_id']} already exists (ID: {existing.paper_id})")
                    paper['paper_id'] = existing.paper_id
                    processed.append(paper)
                    continue

                # Add to PostgreSQL
                paper_data = {
                    'arxiv_id': paper['arxiv_id'],
                    'title': paper['title'],
                    'abstract': paper['abstract'],
                    'full_text': paper.get('full_text'),
                    'published_date': paper['published'].split('T')[0] if 'T' in str(paper['published']) else str(
                        paper['published']),
                    'primary_category': paper['primary_category'],
                    'categories': paper.get('categories', []),
                    'pdf_path': paper.get('pdf_path'),
                    'text_extracted': paper.get('text_extracted', False)
                }

                db_paper = self.postgres_db.add_paper(paper_data)
                paper['paper_id'] = db_paper.paper_id

                # Build knowledge graph
                kg_paper_data = {
                    'paper_id': db_paper.paper_id,
                    'title': paper['title'],
                    'abstract': paper['abstract'],
                    'full_text': paper.get('full_text'),
                    'authors': paper.get('authors', []),
                    'published_date': paper_data['published_date'],
                    'categories': paper.get('categories'),
                    'arxiv_id': paper['arxiv_id']
                }

                self.kg_builder.process_paper(kg_paper_data)

                processed.append(paper)
                logger.info(f"✓ Added paper {db_paper.paper_id}: {paper['title'][:50]}...")

            except Exception as e:
                logger.error(f"Failed to add paper {paper.get('arxiv_id')}: {e}")

        return processed

    def _create_embeddings(self, papers: List[Dict]) -> Dict:
        """Create embeddings for papers"""
        embedding_papers = []

        for paper in papers:
            # Combine title, abstract, and full text
            text = f"{paper['title']}\n\n{paper.get('abstract', '')}"

            if paper.get('full_text'):
                text += f"\n\n{paper['full_text'][:10000]}"  # Limit for memory

            embedding_papers.append({
                'paper_id': paper['paper_id'],
                'text': text,
                'metadata': {
                    'title': paper['title'],
                    'arxiv_id': paper.get('arxiv_id'),
                    'year': paper.get('published', '').split('-')[0]
                }
            })

        return self.embedding_pipeline.batch_process_papers(embedding_papers, batch_size=5)

    def close(self):
        """Clean up resources"""
        self.postgres_db.close()
        self.kg_builder.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Populate database with research papers')

    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--category', type=str, help='arXiv category (e.g., cs.AI)')
    parser.add_argument('--num', type=int, default=10, help='Number of papers to process')
    parser.add_argument('--no-download', action='store_true', help='Skip PDF download')
    parser.add_argument('--no-parse', action='store_true', help='Skip PDF parsing')

    args = parser.parse_args()

    if not args.query and not args.category:
        parser.error("Must provide --query or --category")

    # Create logs directory
    Path('logs').mkdir(exist_ok=True)

    # Run populator
    populator = DatabasePopulator()

    try:
        stats = populator.populate_from_arxiv(
            query=args.query,
            category=args.category,
            num_papers=args.num,
            download_pdfs=not args.no_download,
            process_pdfs=not args.no_parse
        )

        print("\n✓ Population complete!")
        print(f"  Papers added: {stats['papers_in_db']}")
        print(f"  Embeddings: {stats['embeddings_created']}")

    finally:
        populator.close()


if __name__ == "__main__":
    main()
