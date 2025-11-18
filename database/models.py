"""
SQLAlchemy ORM Models for Research Knowledge Navigator

This module defines all database models using SQLAlchemy ORM
for type-safe database interactions.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean,
    ForeignKey, ARRAY, DECIMAL, JSON, CheckConstraint, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Paper(Base):
    """Research paper model"""
    __tablename__ = 'papers'

    paper_id = Column(Integer, primary_key=True)
    arxiv_id = Column(String(50), unique=True)
    pubmed_id = Column(String(50), unique=True)
    doi = Column(String(255))
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    full_text = Column(Text)
    published_date = Column(Date)
    updated_date = Column(Date)
    primary_category = Column(String(100))
    categories = Column(ARRAY(Text))
    pdf_path = Column(Text)
    text_extracted = Column(Boolean, default=False)
    extraction_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paper_authors = relationship('PaperAuthor', back_populates='paper', cascade='all, delete-orphan')
    paper_methods = relationship('PaperMethod', back_populates='paper', cascade='all, delete-orphan')
    paper_datasets = relationship('PaperDataset', back_populates='paper', cascade='all, delete-orphan')
    text_chunks = relationship('TextChunk', back_populates='paper', cascade='all, delete-orphan')
    statistics = relationship('PaperStatistic', back_populates='paper', uselist=False, cascade='all, delete-orphan')

    # Citations (both ways)
    citations_citing = relationship('Citation', foreign_keys='Citation.citing_paper_id', back_populates='citing_paper')
    citations_cited = relationship('Citation', foreign_keys='Citation.cited_paper_id', back_populates='cited_paper')

    def __repr__(self):
        return f"<Paper(paper_id={self.paper_id}, title='{self.title[:50]}...')>"


class Author(Base):
    """Author model"""
    __tablename__ = 'authors'

    author_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    orcid = Column(String(50))
    h_index = Column(Integer)
    affiliation_history = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paper_authors = relationship('PaperAuthor', back_populates='author')
    author_institutions = relationship('AuthorInstitution', back_populates='author')

    __table_args__ = (
        UniqueConstraint('name', 'orcid', name='unique_author'),
    )

    def __repr__(self):
        return f"<Author(author_id={self.author_id}, name='{self.name}')>"


class Institution(Base):
    """Institution model"""
    __tablename__ = 'institutions'

    institution_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    country = Column(String(100))
    city = Column(String(100))
    institution_type = Column(String(50))
    website = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author_institutions = relationship('AuthorInstitution', back_populates='institution')

    def __repr__(self):
        return f"<Institution(institution_id={self.institution_id}, name='{self.name}')>"


class Method(Base):
    """Research method/technique model"""
    __tablename__ = 'methods'

    method_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100))
    aliases = Column(ARRAY(Text))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper_methods = relationship('PaperMethod', back_populates='method')

    def __repr__(self):
        return f"<Method(method_id={self.method_id}, name='{self.name}')>"


class Dataset(Base):
    """Research dataset model"""
    __tablename__ = 'datasets'

    dataset_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    domain = Column(String(100))
    url = Column(Text)
    size_info = Column(String(100))
    license = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper_datasets = relationship('PaperDataset', back_populates='dataset')

    def __repr__(self):
        return f"<Dataset(dataset_id={self.dataset_id}, name='{self.name}')>"


class PaperAuthor(Base):
    """Paper-Author relationship"""
    __tablename__ = 'paper_authors'

    paper_author_id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('authors.author_id', ondelete='CASCADE'), nullable=False)
    author_position = Column(Integer)
    is_corresponding = Column(Boolean, default=False)
    contribution_role = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship('Paper', back_populates='paper_authors')
    author = relationship('Author', back_populates='paper_authors')

    __table_args__ = (
        UniqueConstraint('paper_id', 'author_id', name='unique_paper_author'),
    )

    def __repr__(self):
        return f"<PaperAuthor(paper_id={self.paper_id}, author_id={self.author_id})>"


class AuthorInstitution(Base):
    """Author-Institution affiliation"""
    __tablename__ = 'author_institutions'

    affiliation_id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.author_id', ondelete='CASCADE'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.institution_id', ondelete='CASCADE'), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    position = Column(String(100))
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author = relationship('Author', back_populates='author_institutions')
    institution = relationship('Institution', back_populates='author_institutions')

    def __repr__(self):
        return f"<AuthorInstitution(author_id={self.author_id}, institution_id={self.institution_id})>"


class PaperMethod(Base):
    """Paper-Method relationship"""
    __tablename__ = 'paper_methods'

    paper_method_id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    method_id = Column(Integer, ForeignKey('methods.method_id', ondelete='CASCADE'), nullable=False)
    mention_count = Column(Integer, default=1)
    context = Column(Text)
    is_primary_method = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship('Paper', back_populates='paper_methods')
    method = relationship('Method', back_populates='paper_methods')

    __table_args__ = (
        UniqueConstraint('paper_id', 'method_id', name='unique_paper_method'),
    )

    def __repr__(self):
        return f"<PaperMethod(paper_id={self.paper_id}, method_id={self.method_id})>"


class PaperDataset(Base):
    """Paper-Dataset relationship"""
    __tablename__ = 'paper_datasets'

    paper_dataset_id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    dataset_id = Column(Integer, ForeignKey('datasets.dataset_id', ondelete='CASCADE'), nullable=False)
    usage_type = Column(String(50))
    performance_metric = Column(String(100))
    performance_value = Column(DECIMAL(10, 4))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship('Paper', back_populates='paper_datasets')
    dataset = relationship('Dataset', back_populates='paper_datasets')

    __table_args__ = (
        UniqueConstraint('paper_id', 'dataset_id', 'usage_type', name='unique_paper_dataset'),
    )

    def __repr__(self):
        return f"<PaperDataset(paper_id={self.paper_id}, dataset_id={self.dataset_id})>"


class Citation(Base):
    """Citation relationship between papers"""
    __tablename__ = 'citations'

    citation_id = Column(Integer, primary_key=True)
    citing_paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    cited_paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    context = Column(Text)
    citation_intent = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citing_paper = relationship('Paper', foreign_keys=[citing_paper_id], back_populates='citations_citing')
    cited_paper = relationship('Paper', foreign_keys=[cited_paper_id], back_populates='citations_cited')

    __table_args__ = (
        UniqueConstraint('citing_paper_id', 'cited_paper_id', name='unique_citation'),
        CheckConstraint('citing_paper_id != cited_paper_id', name='no_self_citation'),
    )

    def __repr__(self):
        return f"<Citation(citing={self.citing_paper_id}, cited={self.cited_paper_id})>"


class TextChunk(Base):
    """Text chunk for RAG"""
    __tablename__ = 'text_chunks'

    chunk_id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    section = Column(String(100))
    num_tokens = Column(Integer)
    embedding_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship('Paper', back_populates='text_chunks')

    __table_args__ = (
        UniqueConstraint('paper_id', 'chunk_index', name='unique_chunk'),
    )

    def __repr__(self):
        return f"<TextChunk(chunk_id={self.chunk_id}, paper_id={self.paper_id})>"


class PaperStatistic(Base):
    """Paper statistics for analytics"""
    __tablename__ = 'paper_statistics'

    stat_id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False, unique=True)
    citation_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    last_cited_date = Column(Date)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    paper = relationship('Paper', back_populates='statistics')

    def __repr__(self):
        return f"<PaperStatistic(paper_id={self.paper_id}, citations={self.citation_count})>"


class UserWorkspace(Base):
    """User workspace model"""
    __tablename__ = 'user_workspaces'

    workspace_id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    workspace_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace_papers = relationship('WorkspacePaper', back_populates='workspace', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('user_id', 'workspace_name', name='unique_user_workspace'),
    )

    def __repr__(self):
        return f"<UserWorkspace(workspace_id={self.workspace_id}, name='{self.workspace_name}')>"


class WorkspacePaper(Base):
    """Papers saved in workspaces"""
    __tablename__ = 'workspace_papers'

    workspace_paper_id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey('user_workspaces.workspace_id', ondelete='CASCADE'), nullable=False)
    paper_id = Column(Integer, ForeignKey('papers.paper_id', ondelete='CASCADE'), nullable=False)
    notes = Column(Text)
    tags = Column(ARRAY(Text))
    rating = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workspace = relationship('UserWorkspace', back_populates='workspace_papers')
    paper = relationship('Paper')

    __table_args__ = (
        UniqueConstraint('workspace_id', 'paper_id', name='unique_workspace_paper'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )

    def __repr__(self):
        return f"<WorkspacePaper(workspace_id={self.workspace_id}, paper_id={self.paper_id})>"
