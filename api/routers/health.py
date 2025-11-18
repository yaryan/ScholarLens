"""
Health check and system status endpoints.
"""

from fastapi import APIRouter, Depends
from api.dependencies import get_db_manager
from database.db_manager import DatabaseManager
from typing import Dict
import time

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", summary="Health Check")
async def health_check() -> Dict:
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "Research Knowledge Navigator API",
        "timestamp": time.time()
    }


@router.get("/status", summary="System Status")
async def system_status(db: DatabaseManager = Depends(get_db_manager)) -> Dict:
    """
    Detailed system status including database statistics.

    Returns:
        System status with database statistics
    """
    try:
        stats = db.get_complete_statistics()

        return {
            "status": "operational",
            "databases": {
                "postgresql": {
                    "connected": True,
                    "papers": stats.get('postgresql', {}).get('total_papers', 0),
                    "authors": stats.get('postgresql', {}).get('total_authors', 0)
                },
                "neo4j": {
                    "connected": True,
                    "nodes": stats.get('neo4j', {}).get('papers', 0)
                },
                "faiss": {
                    "connected": True,
                    "vectors": stats.get('vector_store', {}).get('total_vectors', 0)
                }
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": time.time()
        }
