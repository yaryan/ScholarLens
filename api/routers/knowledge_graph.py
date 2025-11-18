"""
Knowledge Graph API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db_manager
from api.schemas.graph_schemas import (
    AuthorNetworkResponse, CollaborationGraphResponse, GraphPathRequest, GraphPathResponse, CitationNetworkResponse
)
from database.db_manager import DatabaseManager

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])

@router.get("/authors/{author_id}/network", response_model=AuthorNetworkResponse)
async def author_network(
    author_id: int, db: DatabaseManager = Depends(get_db_manager)
):
    """
    Get author collaboration network from Neo4j.
    """
    try:
        network = db.get_author_network(author_id)
        return AuthorNetworkResponse(
            author_id=author_id,
            author_name=network['author']['name'],
            collaborators=network['collaborators'],
            papers=[p['paper_id'] for p in network['papers']],
            total_collaborations=len(network['collaborators'])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaborations", response_model=CollaborationGraphResponse)
async def collaboration_graph(
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Return collaboration graph (nodes/edges/statistics).
    """
    # For demo, just return nodes/edges counts
    try:
        stats = db.neo4j.get_graph_statistics()
        # TODO: Build real graph nodes/edges
        return CollaborationGraphResponse(
            nodes=[],
            edges=[],
            statistics=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
