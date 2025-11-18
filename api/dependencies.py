"""
API Dependencies

Dependency injection for database connections and common utilities.
"""

from database.db_manager import DatabaseManager
from nlp.embedding_pipeline import EmbeddingPipeline
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Singleton instances (memory optimization)
_db_manager = None
_embedding_pipeline = None


@lru_cache()
def get_settings():
    """
    Get application settings (cached).

    Returns:
        Settings instance
    """
    from api.config import settings
    return settings


def get_db_manager() -> DatabaseManager:
    """
    Get database manager instance (singleton for memory efficiency).

    Yields:
        DatabaseManager instance
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager()
        logger.info("✓ Database Manager initialized")

    return _db_manager


def get_embedding_pipeline() -> EmbeddingPipeline:
    """
    Get embedding pipeline instance (singleton).

    Returns:
        EmbeddingPipeline instance
    """
    global _embedding_pipeline

    if _embedding_pipeline is None:
        _embedding_pipeline = EmbeddingPipeline()
        logger.info("✓ Embedding Pipeline initialized")

    return _embedding_pipeline


def cleanup_resources():
    """
    Clean up resources on shutdown.
    """
    global _db_manager

    if _db_manager is not None:
        _db_manager.close_all()
        _db_manager = None
        logger.info("✓ Resources cleaned up")
