"""
Knowledge graph-related Pydantic schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class NodeBase(BaseModel):
    """Base node schema"""
    id: int
    type: str
    label: str
    properties: Optional[Dict[str, Any]] = {}


class RelationshipBase(BaseModel):
    """Base relationship schema"""
    id: Optional[int] = None
    type: str
    source: int
    target: int
    properties: Optional[Dict[str, Any]] = {}


class AuthorNetworkResponse(BaseModel):
    """Author collaboration network response"""
    author_id: int
    author_name: str
    collaborators: List[Dict[str, Any]]
    papers: List[int]
    total_collaborations: int


class CollaborationGraphResponse(BaseModel):
    """Full collaboration graph"""
    nodes: List[NodeBase]
    edges: List[RelationshipBase]
    statistics: Dict[str, int]


class GraphPathRequest(BaseModel):
    """Request to find path between entities"""
    start_id: int = Field(..., description="Starting node ID")
    end_id: int = Field(..., description="Ending node ID")
    max_depth: int = Field(default=5, ge=1, le=10, description="Maximum path depth")
    relationship_types: Optional[List[str]] = None


class GraphPathResponse(BaseModel):
    """Path in knowledge graph"""
    paths: List[List[Dict[str, Any]]]
    shortest_path_length: Optional[int] = None
    total_paths: int


class CitationNetworkResponse(BaseModel):
    """Citation network for a paper"""
    paper_id: int
    paper_title: str
    citing_papers: List[Dict[str, Any]]
    cited_papers: List[Dict[str, Any]]
    citation_count: int
    reference_count: int
