"""
Analytics endpoints.
"""

from fastapi import APIRouter, Depends
from api.dependencies import get_db_manager
from typing import Dict, Any

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/statistics", summary="Get database-wide statistics")
async def statistics(db = Depends(get_db_manager)) -> Dict[str, Any]:
    """
    Database statistics, including counts and trends.
    """
    stats = db.get_complete_statistics()
    return stats

@router.get("/trends", summary="Get research trends")
async def trends():
    """
    Dummy endpoint for now.
    """
    # TODO: Implement paper trend analysis
    return {"trends": ["transformers", "LLM", "diffusion models"]}
