"""
Paper-related Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class AuthorBase(BaseModel):
    """Base author schema"""
    author_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    orcid: Optional[str] = None


class AuthorResponse(AuthorBase):
    """Author response with statistics"""
    paper_count: Optional[int] = None
    h_index: Optional[int] = None

    class Config:
        from_attributes = True


class PaperBase(BaseModel):
    """Base paper schema"""
    title: str = Field(..., min_length=1, max_length=1000)
    abstract: Optional[str] = None
    arxiv_id: Optional[str] = None
    published_date: Optional[date] = None
    primary_category: Optional[str] = None
    categories: Optional[List[str]] = None


class PaperCreate(PaperBase):
    """Schema for creating a new paper"""
    authors: Optional[List[str]] = []
    full_text: Optional[str] = None


class PaperResponse(PaperBase):
    """Paper response with full details"""
    paper_id: int
    authors: List[AuthorResponse] = []
    methods: List[str] = []
    datasets: List[str] = []
    created_at: datetime
    updated_at: datetime
    citation_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PaperSummary(BaseModel):
    """Lightweight paper summary for list views"""
    paper_id: int
    title: str
    abstract: Optional[str] = Field(None, max_length=500)
    authors: List[str] = []
    published_date: Optional[date] = None
    primary_category: Optional[str] = None
    citation_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PaginatedPapersResponse(BaseModel):
    """Paginated papers response"""
    papers: List[PaperSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
