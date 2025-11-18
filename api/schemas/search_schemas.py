"""
Search-related Pydantic schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class SearchType(str, Enum):
    """Search type enum"""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    FULLTEXT = "fulltext"


class SemanticSearchRequest(BaseModel):
    """Semantic search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "transformer neural networks for NLP",
                "top_k": 10
            }
        }


class KeywordSearchRequest(BaseModel):
    """Keyword search request"""
    query: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResult(BaseModel):
    """Single search result"""
    paper_id: int
    title: str
    abstract: Optional[str] = None
    authors: List[str] = []
    published_date: Optional[str] = None
    similarity_score: Optional[float] = None
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Search response with results"""
    results: List[SearchResult]
    total: int
    query: str
    search_type: str
    processing_time_ms: float


class AutocompleteRequest(BaseModel):
    """Autocomplete request"""
    query: str = Field(..., min_length=2, max_length=100)
    field: str = Field(default="title", description="Field to autocomplete: title, author, method")
    limit: int = Field(default=10, ge=1, le=20)


class AutocompleteResponse(BaseModel):
    """Autocomplete suggestions"""
    suggestions: List[str]
    count: int
