-- ================================================================
-- Research Knowledge Navigator - PostgreSQL Schema
-- Version: 1.0
-- Date: October 2025
-- Optimized for research paper metadata storage
-- ================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ================================================================
-- CORE TABLES
-- ================================================================

-- Papers: Core metadata for research papers
CREATE TABLE IF NOT EXISTS papers (
    paper_id SERIAL PRIMARY KEY,
    arxiv_id VARCHAR(50) UNIQUE,
    pubmed_id VARCHAR(50) UNIQUE,
    doi VARCHAR(255),
    title TEXT NOT NULL,
    abstract TEXT,
    full_text TEXT,
    published_date DATE,
    updated_date DATE,
    primary_category VARCHAR(100),
    categories TEXT[],  -- Array of categories
    pdf_path TEXT,
    text_extracted BOOLEAN DEFAULT FALSE,
    extraction_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_has_id CHECK (arxiv_id IS NOT NULL OR pubmed_id IS NOT NULL OR doi IS NOT NULL)
);

-- Authors: Individual researchers
CREATE TABLE IF NOT EXISTS authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    orcid VARCHAR(50),
    h_index INTEGER,
    affiliation_history JSONB,  -- Store historical affiliations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    CONSTRAINT unique_author UNIQUE NULLS NOT DISTINCT (name, orcid)
);

-- Institutions: Research organizations
CREATE TABLE IF NOT EXISTS institutions (
    institution_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100),
    city VARCHAR(100),
    institution_type VARCHAR(50),  -- university, research_lab, company
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Methods/Techniques mentioned in papers
CREATE TABLE IF NOT EXISTS methods (
    method_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100),  -- ml, nlp, cv, statistics
    aliases TEXT[],  -- Alternative names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Datasets mentioned in papers
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    domain VARCHAR(100),  -- vision, nlp, audio, etc.
    url TEXT,
    size_info VARCHAR(100),
    license VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- RELATIONSHIP TABLES (Many-to-Many)
-- ================================================================

-- Paper-Author relationship
CREATE TABLE IF NOT EXISTS paper_authors (
    paper_author_id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
    author_position INTEGER,  -- Order in author list
    is_corresponding BOOLEAN DEFAULT FALSE,
    contribution_role VARCHAR(100),  -- conceptualization, methodology, writing, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    CONSTRAINT unique_paper_author UNIQUE (paper_id, author_id)
);

-- Author-Institution affiliation
CREATE TABLE IF NOT EXISTS author_institutions (
    affiliation_id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
    institution_id INTEGER NOT NULL REFERENCES institutions(institution_id) ON DELETE CASCADE,
    start_date DATE,
    end_date DATE,
    position VARCHAR(100),  -- professor, postdoc, phd_student
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Check constraint
    CONSTRAINT check_date_order CHECK (end_date IS NULL OR end_date >= start_date)
);

-- Paper-Method relationship
CREATE TABLE IF NOT EXISTS paper_methods (
    paper_method_id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    method_id INTEGER NOT NULL REFERENCES methods(method_id) ON DELETE CASCADE,
    mention_count INTEGER DEFAULT 1,
    context TEXT,  -- Where it was mentioned
    is_primary_method BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_paper_method UNIQUE (paper_id, method_id)
);

-- Paper-Dataset relationship
CREATE TABLE IF NOT EXISTS paper_datasets (
    paper_dataset_id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    dataset_id INTEGER NOT NULL REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    usage_type VARCHAR(50),  -- training, testing, validation, benchmark
    performance_metric VARCHAR(100),
    performance_value DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_paper_dataset UNIQUE (paper_id, dataset_id, usage_type)
);

-- Citations between papers
CREATE TABLE IF NOT EXISTS citations (
    citation_id SERIAL PRIMARY KEY,
    citing_paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    cited_paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    context TEXT,  -- Sentence where citation appears
    citation_intent VARCHAR(50),  -- background, methodology, comparison
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    CONSTRAINT unique_citation UNIQUE (citing_paper_id, cited_paper_id),
    -- Cannot cite itself
    CONSTRAINT no_self_citation CHECK (citing_paper_id != cited_paper_id)
);

-- ================================================================
-- TEXT PROCESSING TABLES
-- ================================================================

-- Text chunks for RAG
CREATE TABLE IF NOT EXISTS text_chunks (
    chunk_id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    section VARCHAR(100),  -- abstract, introduction, methods, etc.
    num_tokens INTEGER,
    embedding_id INTEGER,  -- Reference to vector store
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    CONSTRAINT unique_chunk UNIQUE (paper_id, chunk_index)
);

-- ================================================================
-- USER WORKSPACE TABLES (For personalization)
-- ================================================================

-- User workspaces
CREATE TABLE IF NOT EXISTS user_workspaces (
    workspace_id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,  -- External user ID
    workspace_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_workspace UNIQUE (user_id, workspace_name)
);

-- Saved papers in workspaces
CREATE TABLE IF NOT EXISTS workspace_papers (
    workspace_paper_id SERIAL PRIMARY KEY,
    workspace_id INTEGER NOT NULL REFERENCES user_workspaces(workspace_id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
    notes TEXT,
    tags TEXT[],
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_workspace_paper UNIQUE (workspace_id, paper_id)
);

-- ================================================================
-- ANALYTICS TABLES
-- ================================================================

-- Paper statistics (for analytics)
CREATE TABLE IF NOT EXISTS paper_statistics (
    stat_id SERIAL PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE UNIQUE,
    citation_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    last_cited_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================

-- Papers table indexes
CREATE INDEX IF NOT EXISTS idx_papers_arxiv ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_pubmed ON papers(pubmed_id);
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(primary_category);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers USING GIN(categories);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_papers_title_fts ON papers USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_papers_abstract_fts ON papers USING gin(to_tsvector('english', COALESCE(abstract, '')));
CREATE INDEX IF NOT EXISTS idx_text_chunks_fts ON text_chunks USING gin(to_tsvector('english', chunk_text));

-- Fuzzy text search indexes (for typo tolerance)
CREATE INDEX IF NOT EXISTS idx_papers_title_trgm ON papers USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_authors_name_trgm ON authors USING gin(name gin_trgm_ops);

-- Authors table indexes
CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);
CREATE INDEX IF NOT EXISTS idx_authors_orcid ON authors(orcid);

-- Relationship table indexes
CREATE INDEX IF NOT EXISTS idx_paper_authors_paper ON paper_authors(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_authors_author ON paper_authors(author_id);
CREATE INDEX IF NOT EXISTS idx_paper_methods_paper ON paper_methods(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_methods_method ON paper_methods(method_id);
CREATE INDEX IF NOT EXISTS idx_paper_datasets_paper ON paper_datasets(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_datasets_dataset ON paper_datasets(dataset_id);

-- Citations indexes
CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_paper_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_paper_id);

-- Text chunks indexes
CREATE INDEX IF NOT EXISTS idx_text_chunks_paper ON text_chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_text_chunks_section ON text_chunks(section);

-- Methods and datasets indexes
CREATE INDEX IF NOT EXISTS idx_methods_name ON methods(name);
CREATE INDEX IF NOT EXISTS idx_methods_category ON methods(category);
CREATE INDEX IF NOT EXISTS idx_datasets_name ON datasets(name);
CREATE INDEX IF NOT EXISTS idx_datasets_domain ON datasets(domain);

-- ================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_authors_updated_at BEFORE UPDATE ON authors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON user_workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update paper statistics on citation
CREATE OR REPLACE FUNCTION update_paper_citation_count()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO paper_statistics (paper_id, citation_count, last_cited_date, updated_at)
    VALUES (NEW.cited_paper_id, 1, CURRENT_DATE, CURRENT_TIMESTAMP)
    ON CONFLICT (paper_id) DO UPDATE
    SET citation_count = paper_statistics.citation_count + 1,
        last_cited_date = CURRENT_DATE,
        updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply citation counter trigger
CREATE TRIGGER update_citation_count AFTER INSERT ON citations
    FOR EACH ROW EXECUTE FUNCTION update_paper_citation_count();

-- ================================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================================

-- View: Papers with author count and citation count
CREATE OR REPLACE VIEW papers_overview AS
SELECT
    p.paper_id,
    p.arxiv_id,
    p.title,
    p.published_date,
    p.primary_category,
    COUNT(DISTINCT pa.author_id) as author_count,
    COALESCE(ps.citation_count, 0) as citation_count,
    COALESCE(ps.view_count, 0) as view_count
FROM papers p
LEFT JOIN paper_authors pa ON p.paper_id = pa.paper_id
LEFT JOIN paper_statistics ps ON p.paper_id = ps.paper_id
GROUP BY p.paper_id, ps.citation_count, ps.view_count;

-- View: Author productivity
CREATE OR REPLACE VIEW author_productivity AS
SELECT
    a.author_id,
    a.name,
    COUNT(pa.paper_id) as paper_count,
    MIN(p.published_date) as first_publication,
    MAX(p.published_date) as latest_publication
FROM authors a
LEFT JOIN paper_authors pa ON a.author_id = pa.author_id
LEFT JOIN papers p ON pa.paper_id = p.paper_id
GROUP BY a.author_id;

-- View: Popular methods
CREATE OR REPLACE VIEW method_popularity AS
SELECT
    m.method_id,
    m.name,
    m.category,
    COUNT(pm.paper_id) as usage_count
FROM methods m
LEFT JOIN paper_methods pm ON m.method_id = pm.method_id
GROUP BY m.method_id
ORDER BY usage_count DESC;

-- ================================================================
-- INITIAL DATA (Optional seed data)
-- ================================================================

-- Insert common categories
INSERT INTO methods (name, category, description) VALUES
    ('Convolutional Neural Network', 'deep_learning', 'Neural network with convolutional layers for spatial data'),
    ('Transformer', 'deep_learning', 'Attention-based neural network architecture'),
    ('LSTM', 'deep_learning', 'Long Short-Term Memory recurrent neural network'),
    ('Random Forest', 'machine_learning', 'Ensemble of decision trees'),
    ('Support Vector Machine', 'machine_learning', 'Supervised learning model for classification'),
    ('BERT', 'nlp', 'Bidirectional Encoder Representations from Transformers'),
    ('GPT', 'nlp', 'Generative Pre-trained Transformer'),
    ('ResNet', 'computer_vision', 'Residual Neural Network for image classification')
ON CONFLICT (name) DO NOTHING;

-- Insert common datasets
INSERT INTO datasets (name, domain, description) VALUES
    ('ImageNet', 'computer_vision', 'Large-scale image database for visual object recognition'),
    ('MNIST', 'computer_vision', 'Database of handwritten digits'),
    ('CIFAR-10', 'computer_vision', '60000 32x32 color images in 10 classes'),
    ('COCO', 'computer_vision', 'Large-scale object detection, segmentation, and captioning dataset'),
    ('SQuAD', 'nlp', 'Stanford Question Answering Dataset'),
    ('GLUE', 'nlp', 'General Language Understanding Evaluation benchmark'),
    ('WikiText', 'nlp', 'Language modeling dataset extracted from Wikipedia')
ON CONFLICT (name) DO NOTHING;

-- ================================================================
-- GRANT PERMISSIONS (Adjust as needed)
-- ================================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO research_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO research_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO research_user;

-- ================================================================
-- END OF SCHEMA
-- ================================================================
