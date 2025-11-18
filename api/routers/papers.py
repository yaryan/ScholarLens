"""
Papers API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from api.dependencies import get_db_manager
from api.schemas.paper_schemas import (
    PaperResponse, PaperSummary, PaginatedPapersResponse
)
from database.db_manager import DatabaseManager
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/papers", tags=["Papers"])


@router.get("/", response_model=PaginatedPapersResponse, summary="List Papers")
async def list_papers(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        category: Optional[str] = Query(None, description="Filter by category"),
        year: Optional[int] = Query(None, description="Filter by year"),
        db: DatabaseManager = Depends(get_db_manager)
) -> PaginatedPapersResponse:
    """
    Get paginated list of papers with optional filters.

    Parameters:
    - **page**: Page number (starts at 1)
    - **page_size**: Number of papers per page
    - **category**: Filter by arXiv category (e.g., 'cs.AI')
    - **year**: Filter by publication year

    Returns:
        Paginated list of papers
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Build query
        with db.postgres.get_session() as session:
            from database.models import Paper, Author, PaperAuthor
            from sqlalchemy import select, func, extract

            # Base query
            query = select(Paper)

            # Apply filters
            if category:
                query = query.where(Paper.primary_category == category)

            if year:
                query = query.where(extract('year', Paper.published_date) == year)

            # Get total count
            count_query = select(func.count()).select_from(Paper)
            if category:
                count_query = count_query.where(Paper.primary_category == category)
            if year:
                count_query = count_query.where(extract('year', Paper.published_date) == year)

            total = session.execute(count_query).scalar()

            # Get paginated results
            query = query.order_by(Paper.published_date.desc()).offset(offset).limit(page_size)
            papers = session.execute(query).scalars().all()

            # Convert to summaries with authors
            paper_summaries = []
            for paper in papers:
                # Get authors
                author_query = select(Author).join(PaperAuthor).where(PaperAuthor.paper_id == paper.paper_id)
                authors = session.execute(author_query).scalars().all()

                paper_summaries.append(PaperSummary(
                    paper_id=paper.paper_id,
                    title=paper.title,
                    abstract=paper.abstract[:500] if paper.abstract else None,
                    authors=[a.name for a in authors],
                    published_date=paper.published_date,
                    primary_category=paper.primary_category,
                    citation_count=0  # TODO: Add from paper_statistics table
                ))

        total_pages = (total + page_size - 1) // page_size

        return PaginatedPapersResponse(
            papers=paper_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error listing papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}", response_model=PaperResponse, summary="Get Paper Details")
async def get_paper(
        paper_id: int,
        db: DatabaseManager = Depends(get_db_manager)
) -> PaperResponse:
    """
    Get detailed information about a specific paper.

    Parameters:
    - **paper_id**: Unique paper identifier

    Returns:
        Detailed paper information with authors, methods, datasets
    """
    try:
        with db.postgres.get_session() as session:
            from database.models import Paper, Author, PaperAuthor, Method, PaperMethod, Dataset, PaperDataset
            from sqlalchemy import select

            # Get paper
            paper = session.execute(
                select(Paper).where(Paper.paper_id == paper_id)
            ).scalar_one_or_none()

            if not paper:
                raise HTTPException(status_code=404, detail="Paper not found")

            # Get authors
            authors = session.execute(
                select(Author).join(PaperAuthor).where(PaperAuthor.paper_id == paper_id)
            ).scalars().all()

            # Get methods
            methods = session.execute(
                select(Method).join(PaperMethod).where(PaperMethod.paper_id == paper_id)
            ).scalars().all()

            # Get datasets
            datasets = session.execute(
                select(Dataset).join(PaperDataset).where(PaperDataset.paper_id == paper_id)
            ).scalars().all()

            # Build response
            from api.schemas.paper_schemas import AuthorResponse

            return PaperResponse(
                paper_id=paper.paper_id,
                title=paper.title,
                abstract=paper.abstract,
                arxiv_id=paper.arxiv_id,
                published_date=paper.published_date,
                primary_category=paper.primary_category,
                categories=paper.categories or [],
                authors=[AuthorResponse(
                    author_id=a.author_id,
                    name=a.name,
                    email=a.email,
                    orcid=a.orcid
                ) for a in authors],
                methods=[m.name for m in methods],
                datasets=[d.name for d in datasets],
                created_at=paper.created_at,
                updated_at=paper.updated_at,
                citation_count=0  # TODO: Add from statistics
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
