"""
API Configuration

Settings for the FastAPI application including CORS, database connections,
and environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # API Settings
    API_TITLE: str = "Research Knowledge Navigator API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = """
    RESTful API for the Research Knowledge Navigator system.

    Features:
    - 📄 Paper search and retrieval
    - 🔍 Semantic search using embeddings
    - 🕸️ Knowledge graph exploration
    - 📊 Analytics and statistics
    - 🤝 Author collaboration networks
    """

    # Server Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True  # Auto-reload during development

    # CORS Settings (for frontend)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # API docs
    ]

    # Database URLs (from .env)
    POSTGRES_URI: str = os.getenv(
        "POSTGRES_URI",
        "postgresql://research_user:research_password_2024@localhost:5432/research_papers_db"
    )
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "research_password_2024")

    # API Limits (for 16GB RAM system)
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    MAX_SEARCH_RESULTS: int = 50

    # Cache Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # ← ADD THIS LINE to ignore extra .env fields


# Global settings instance
settings = Settings()
