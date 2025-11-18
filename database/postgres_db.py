"""
PostgreSQL Database Manager

This module provides a high-level interface for PostgreSQL operations
using SQLAlchemy ORM.
"""

from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

from database.models import (
    Base, Paper, Author, Institution, Method, Dataset,
    PaperAuthor, AuthorInstitution, PaperMethod, PaperDataset,
    Citation, TextChunk, PaperStatistic
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresDatabase:
    """
    PostgreSQL database manager with connection pooling and ORM support.

    Optimized for 16GB RAM Windows system.
    """

    def __init__(self, uri: Optional[str] = None):
        """
        Initialize PostgreSQL connection.

        Args:
            uri: Database connection URI (defaults to env variable)
        """
        self.uri = uri or os.getenv('POSTGRES_URI')

        if not self.uri:
            raise ValueError("POSTGRES_URI not found in environment variables")

        # Create engine with connection pooling (optimized for 16GB RAM)
        self.engine = create_engine(
            self.uri,
            poolclass=QueuePool,
            pool_size=5,  # Reduced for 16GB RAM
            max_overflow=10,  # Reduced for 16GB RAM
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections every hour
            echo=False  # Set to True for SQL logging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False
        )

        logger.info("PostgreSQL connection initialized")

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy session

        Example:
            with db.get_session() as session:
                papers = session.query(Paper).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables from models"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✓ All tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("All tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping tables: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result

    def fetch_all(self, query: str, params: Optional[Dict] = None) -> List:
        """
        Fetch all results from a query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows
        """
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()

    # ========== PAPER OPERATIONS ==========

    def add_paper(self, paper_data: Dict) -> Paper:
        """
        Add a new paper to the database.

        Args:
            paper_data: Dictionary with paper information

        Returns:
            Created Paper object
        """
        with self.get_session() as session:
            paper = Paper(**paper_data)
            session.add(paper)
            session.flush()  # Get paper_id before commit
            logger.info(f"✓ Added paper: {paper.title[:50]}...")
            return paper

    def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
        """Get paper by ID"""
        with self.get_session() as session:
            return session.query(Paper).filter(Paper.paper_id == paper_id).first()

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        """Get paper by arXiv ID"""
        with self.get_session() as session:
            return session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()

    def search_papers(self, query: str, limit: int = 10) -> List[Paper]:
        """
        Full-text search in papers with multiple search methods.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching papers
        """
        with self.get_session() as session:
            # Try multiple search strategies

            # Strategy 1: Exact phrase search using plainto_tsquery (most forgiving)
            try:
                search_query = func.plainto_tsquery('english', query)
                results = session.query(Paper).filter(
                    func.to_tsvector('english',
                                     Paper.title + ' ' + func.coalesce(Paper.abstract, '')
                                     ).op('@@')(search_query)
                ).limit(limit).all()

                if results:
                    return results
            except:
                pass

            # Strategy 2: Simple LIKE search as fallback
            results = session.query(Paper).filter(
                (Paper.title.ilike(f'%{query}%')) |
                (Paper.abstract.ilike(f'%{query}%'))
            ).limit(limit).all()

            return results

    # ========== AUTHOR OPERATIONS ==========

    def add_author(self, name: str, **kwargs) -> Author:
        """
        Add or get existing author.

        Args:
            name: Author name
            **kwargs: Additional author attributes

        Returns:
            Author object
        """
        with self.get_session() as session:
            # Check if author exists
            author = session.query(Author).filter(Author.name == name).first()

            if not author:
                author = Author(name=name, **kwargs)
                session.add(author)
                session.flush()
                logger.info(f"✓ Added author: {name}")

            return author

    def get_author_papers(self, author_id: int) -> List[Paper]:
        """Get all papers by an author"""
        with self.get_session() as session:
            return session.query(Paper).join(PaperAuthor).filter(
                PaperAuthor.author_id == author_id
            ).all()

    # ========== METHOD OPERATIONS ==========

    def add_method(self, name: str, **kwargs) -> Method:
        """Add or get existing method"""
        with self.get_session() as session:
            method = session.query(Method).filter(Method.name == name).first()

            if not method:
                method = Method(name=name, **kwargs)
                session.add(method)
                session.flush()
                logger.info(f"✓ Added method: {name}")

            return method

    # ========== RELATIONSHIP OPERATIONS ==========

    def link_paper_author(self, paper_id: int, author_id: int, position: int = None):
        """Link paper to author"""
        with self.get_session() as session:
            link = PaperAuthor(
                paper_id=paper_id,
                author_id=author_id,
                author_position=position
            )
            session.add(link)
            logger.info(f"✓ Linked paper {paper_id} to author {author_id}")

    def link_paper_method(self, paper_id: int, method_id: int, **kwargs):
        """Link paper to method"""
        with self.get_session() as session:
            link = PaperMethod(
                paper_id=paper_id,
                method_id=method_id,
                **kwargs
            )
            session.add(link)
            logger.info(f"✓ Linked paper {paper_id} to method {method_id}")

    # ========== ANALYTICS OPERATIONS ==========

    def get_paper_count(self) -> int:
        """Get total paper count"""
        with self.get_session() as session:
            return session.query(func.count(Paper.paper_id)).scalar()

    def get_author_count(self) -> int:
        """Get total author count"""
        with self.get_session() as session:
            return session.query(func.count(Author.author_id)).scalar()

    def get_top_authors(self, limit: int = 10) -> List[Dict]:
        """
        Get authors with most papers.

        Args:
            limit: Number of results

        Returns:
            List of author dictionaries with paper counts
        """
        with self.get_session() as session:
            results = session.query(
                Author.author_id,
                Author.name,
                func.count(PaperAuthor.paper_id).label('paper_count')
            ).join(PaperAuthor).group_by(
                Author.author_id
            ).order_by(
                func.count(PaperAuthor.paper_id).desc()
            ).limit(limit).all()

            return [
                {'author_id': r[0], 'name': r[1], 'paper_count': r[2]}
                for r in results
            ]

    def get_database_statistics(self) -> Dict:
        """Get overall database statistics"""
        with self.get_session() as session:
            stats = {
                'total_papers': session.query(func.count(Paper.paper_id)).scalar(),
                'total_authors': session.query(func.count(Author.author_id)).scalar(),
                'total_methods': session.query(func.count(Method.method_id)).scalar(),
                'total_datasets': session.query(func.count(Dataset.dataset_id)).scalar(),
                'total_citations': session.query(func.count(Citation.citation_id)).scalar(),
                'total_institutions': session.query(func.count(Institution.institution_id)).scalar()
            }

            return stats

    def close(self):
        """Close database connection"""
        self.engine.dispose()
        logger.info("PostgreSQL connection closed")


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = PostgresDatabase()

    # Get statistics
    stats = db.get_database_statistics()

    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)

    for key, value in stats.items():
        print(f"{key}: {value}")

    # Test adding a paper
    paper_data = {
        'arxiv_id': '1706.03762',
        'title': 'Attention Is All You Need',
        'abstract': 'The dominant sequence transduction models...',
        'published_date': '2017-06-12',
        'primary_category': 'cs.CL'
    }

    try:
        paper = db.add_paper(paper_data)
        print(f"\n✓ Test paper added: {paper.paper_id}")
    except Exception as e:
        print(f"\n⚠ Paper may already exist: {e}")

    print("\n" + "=" * 70)
