"""
Search endpoints: semantic search, keyword search, autocomplete.
"""

from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_db_manager, get_embedding_pipeline
from api.schemas.search_schemas import (
    SemanticSearchRequest, SearchResponse, SearchResult, KeywordSearchRequest, AutocompleteRequest, AutocompleteResponse
)
from database.db_manager import DatabaseManager
from nlp.embedding_pipeline import EmbeddingPipeline
from time import perf_counter
import logging

router = APIRouter(prefix="/api/search", tags=["Search"])
logger = logging.getLogger(__name__)

@router.post("/semantic", response_model=SearchResponse, summary="Semantic Paper Search")
async def semantic_search(
    req: SemanticSearchRequest,
    db: DatabaseManager = Depends(get_db_manager),
    embeddings: EmbeddingPipeline = Depends(get_embedding_pipeline)
):
    """
    Perform semantic search over research papers using vector embeddings.
    """
    try:
        t0 = perf_counter()
        results = db.search_papers_semantic(req.query, top_k=req.top_k)
        search_results = [
            SearchResult(
                paper_id=paper['paper'].paper_id,
                title=paper['paper'].title,
                abstract=paper['paper'].abstract,
                authors=[a.name for a in paper['paper'].authors],
                published_date=str(paper['paper'].published_date),
                similarity_score=paper['similarity_score']
            )
            for paper in results
        ]
        t1 = perf_counter()
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=req.query,
            search_type="semantic",
            processing_time_ms=round((t1 - t0) * 1000, 2)
        )
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers", response_model=SearchResponse, summary="Keyword / Fulltext Paper Search")
async def keyword_search(
    req: KeywordSearchRequest = Depends(),
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Fulltext or keyword search for papers.
    """
    try:
        t0 = perf_counter()
        results = db.postgres.search_papers(req.query, limit=req.page_size)
        search_results = [
            SearchResult(
                paper_id=p.paper_id,
                title=p.title,
                abstract=p.abstract,
                authors=[],  # For demo; in prod fetch author names
                published_date=str(p.published_date),
                relevance_score=None
            )
            for p in results
        ]
        t1 = perf_counter()
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=req.query,
            search_type="keyword",
            processing_time_ms=round((t1 - t0) * 1000, 2)
        )
    except Exception as e:
        logger.error(f"Keyword search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/autocomplete", response_model=AutocompleteResponse, summary="Autocomplete Suggestions")
async def autocomplete(
    req: AutocompleteRequest,
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Autocomplete suggestions for titles, authors, or methods.
    """
    try:
        # For now just demo for title; implement others as needed
        suggestions = db.postgres.autocomplete_titles(req.query, limit=req.limit)
        return AutocompleteResponse(
            suggestions=suggestions,
            count=len(suggestions)
        )
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
