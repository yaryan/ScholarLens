"""
Database models for ScholarLens - AI-Powered Research Intelligence Platform
Uses SQLAlchemy ORM for PostgreSQL database management
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Table, Boolean, JSON, UniqueConstraint, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("WARNING: DATABASE_URL not set. Please create a .env file with:")
    print("DATABASE_URL=postgresql://username:password@localhost:5432/scholarlens")
    print("OPENAI_API_KEY=your-openai-api-key")
    DATABASE_URL = "sqlite:///scholarlens.db"
    print("Using SQLite as fallback database.")

IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Embedding vectors (RAG retrieval) require Postgres + pgvector. On SQLite,
# embeddings fall back to plain JSON and vector search is unavailable.
EMBEDDING_DIM = 384

if IS_POSTGRES:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 10}
    )
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    from pgvector.sqlalchemy import Vector
    EmbeddingColumn = Vector(EMBEDDING_DIM)
else:
    engine = create_engine(DATABASE_URL)
    EmbeddingColumn = JSON

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association tables for many-to-many relationships
paper_authors = Table(
    'paper_authors', Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('author_position', Integer, default=0)
)

paper_methods = Table(
    'paper_methods', Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('method_id', Integer, ForeignKey('methods.id', ondelete='CASCADE'), primary_key=True, index=True)
)

paper_datasets = Table(
    'paper_datasets', Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('dataset_id', Integer, ForeignKey('datasets.id', ondelete='CASCADE'), primary_key=True, index=True)
)

author_institutions = Table(
    'author_institutions', Base.metadata,
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('institution_id', Integer, ForeignKey('institutions.id', ondelete='CASCADE'), primary_key=True, index=True)
)

method_prerequisites = Table(
    'method_prerequisites', Base.metadata,
    Column('method_id', Integer, ForeignKey('methods.id', ondelete='CASCADE'), primary_key=True, index=True),
    Column('prerequisite_id', Integer, ForeignKey('methods.id', ondelete='CASCADE'), primary_key=True, index=True)
)


class Paper(Base):
    """Research paper model"""
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    abstract = Column(Text)
    content = Column(Text)
    source = Column(String(50))  # 'pdf', 'arxiv', 'pubmed'
    source_id = Column(String(100))  # arxiv id, pubmed id, etc.
    doi = Column(String(100))
    publication_date = Column(DateTime)
    year = Column(Integer, index=True)
    venue = Column(String(200))
    citation_count = Column(Integer, default=0)
    pdf_path = Column(String(500))
    embedding = Column(EmbeddingColumn)  # title+abstract embedding, for paper-level similarity
    topics = Column(JSON)  # Store extracted topics
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    authors = relationship('Author', secondary=paper_authors, back_populates='papers')
    methods = relationship('Method', secondary=paper_methods, back_populates='papers')
    datasets = relationship('Dataset', secondary=paper_datasets, back_populates='papers')
    chunks = relationship('PaperChunk', back_populates='paper', cascade='all, delete-orphan')
    notes = relationship('Note', back_populates='paper', cascade='all, delete-orphan')
    flashcards = relationship('Flashcard', back_populates='paper', cascade='all, delete-orphan')


class Author(Base):
    """Author model"""
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(200))
    orcid = Column(String(50))
    h_index = Column(Integer, default=0)
    total_citations = Column(Integer, default=0)
    research_interests = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    papers = relationship('Paper', secondary=paper_authors, back_populates='authors')
    institutions = relationship('Institution', secondary=author_institutions, back_populates='authors')
    
    __table_args__ = (UniqueConstraint('name', name='uq_author_name'),)


class Institution(Base):
    """Research institution model"""
    __tablename__ = 'institutions'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    country = Column(String(100))
    city = Column(String(100))
    type = Column(String(50))  # university, company, research_lab
    website = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    authors = relationship('Author', secondary=author_institutions, back_populates='institutions')
    
    __table_args__ = (UniqueConstraint('name', name='uq_institution_name'),)


class Method(Base):
    """Research method/technique model"""
    __tablename__ = 'methods'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100))  # e.g., 'deep_learning', 'nlp', 'computer_vision'
    first_appeared_year = Column(Integer)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    papers = relationship('Paper', secondary=paper_methods, back_populates='methods')
    prerequisites = relationship(
        'Method',
        secondary=method_prerequisites,
        primaryjoin=id == method_prerequisites.c.method_id,
        secondaryjoin=id == method_prerequisites.c.prerequisite_id,
        backref='dependent_methods'
    )
    
    __table_args__ = (UniqueConstraint('name', name='uq_method_name'),)


class Dataset(Base):
    """Dataset model"""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    domain = Column(String(100))
    size = Column(String(100))
    url = Column(String(500))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    papers = relationship('Paper', secondary=paper_datasets, back_populates='datasets')
    
    __table_args__ = (UniqueConstraint('name', name='uq_dataset_name'),)


class PaperChunk(Base):
    """Paper content chunks for RAG"""
    __tablename__ = 'paper_chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(100))  # abstract, introduction, methods, results, etc.
    embedding = Column(EmbeddingColumn)  # sentence-transformers embedding, for RAG retrieval
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship('Paper', back_populates='chunks')


class Note(Base):
    """User notes on papers"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    paper = relationship('Paper', back_populates='notes')


class Flashcard(Base):
    """Flashcards generated from papers"""
    __tablename__ = 'flashcards'
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(String(20), default='medium')
    times_reviewed = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship('Paper', back_populates='flashcards')


class SavedQuery(Base):
    """Saved user queries"""
    __tablename__ = 'saved_queries'
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReadingList(Base):
    """Reading list items"""
    __tablename__ = 'reading_list'
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id', ondelete='CASCADE'), nullable=False)
    priority = Column(Integer, default=0)
    status = Column(String(20), default='unread')  # unread, reading, completed
    added_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get a new database session"""
    return SessionLocal()
