# Research Knowledge Navigator - Complete Setup Guide

**Version:** 1.0  
**Platform:** Windows 10/11 (16GB RAM)  
**Author:** Research Knowledge Navigator Team  
**Last Updated:** November 2025

---

##  Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Phase 1: Environment Setup](#phase-1-environment-setup)
4. [Phase 2: Data Collection](#phase-2-data-collection)
5. [Phase 3: Database Infrastructure](#phase-3-database-infrastructure)
6. [Phase 4: NLP Pipeline & Knowledge Graph](#phase-4-nlp-pipeline--knowledge-graph)
7. [Phase 5: Backend API](#phase-5-backend-api)
8. [Quick Start Guide](#quick-start-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The **Scholarlens** is an AI-powered research intelligence platform that:
-  Collects and processes research papers from arXiv
-  Builds knowledge graphs using Neo4j
-  Enables semantic search with FAISS embeddings
-  Provides RESTful API for data access
-  Visualizes research trends and author collaborations

**Technology Stack:**
- **Backend:** Python 3.8+, FastAPI
- **Databases:** PostgreSQL, Neo4j, FAISS
- **NLP:** spaCy, sentence-transformers
- **Frontend:** React with TypeScript
- **Deployment:** Docker, Docker Compose

---

## System Requirements

### Hardware
- **RAM:** 16GB minimum
- **Storage:** 50GB free space
- **CPU:** Multi-core processor (4+ cores recommended)

### Software
- **OS:** Windows 10/11
- **Python:** 3.8 or 3.9 (3.10+ not recommended)
- **Node.js:** v18+ (for frontend)
- **Docker Desktop:** Latest version
- **Git:** Latest version

---

## Phase 1: Environment Setup

### Step 1.1: Install Prerequisites

#### Python 3.8/3.9
```powershell
# Check Python version
python --version

# Should show Python 3.8.x or 3.9.x
```

**Download Python 3.8:** https://www.python.org/downloads/release/python-3810/

#### Docker Desktop
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install and restart computer
3. Verify installation:
```powershell
docker --version
docker-compose --version
```

#### Git
```powershell
# Verify Git installation
git --version
```

### Step 1.2: Create Project Structure

```powershell
# Create project directory
cd D:\MS Acad\EDS\Project
New-Item -Path "ScholarLens-v2" -ItemType Directory
cd ScholarLens-v2

# Initialize Git repository
git init
```

### Step 1.3: Setup Python Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 1.4: Install Core Dependencies

Create `requirements.txt`:

```txt
# Core libraries
requests==2.31.0
arxiv==1.4.8
feedparser==6.0.10

# PDF Processing
PyPDF2==3.0.1
pdfplumber==0.10.3

# Text Processing
nltk==3.8.1
spacy==3.7.2

# Database drivers
psycopg2-binary==2.9.9
SQLAlchemy==2.0.23
neo4j==5.14.1

# Vector embeddings
faiss-cpu==1.7.4
sentence-transformers==2.2.2

# Environment
python-dotenv==1.0.0

# Testing
pytest==7.4.3
```

**Install:**
```powershell
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_md
```

### Step 1.5: Create Environment File

Create `.env` file:

```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=research_papers_db
POSTGRES_USER=research_user
POSTGRES_PASSWORD=research_password_2024
POSTGRES_URI=postgresql://research_user:research_password_2024@localhost:5432/research_papers_db

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=research_password_2024

# Application Settings
APP_NAME=Research Knowledge Navigator
DEBUG_MODE=True
LOG_LEVEL=INFO

# Data Directories
DATA_DIR=./data
PDF_DIR=./data/pdfs
FAISS_INDEX_DIR=./data/faiss_index

# NLP Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

---

## Phase 2: Data Collection

### Step 2.1: Create Directory Structure

```powershell
New-Item -Path "data_sources" -ItemType Directory
New-Item -Path "processing" -ItemType Directory
New-Item -Path "data\pdfs" -ItemType Directory -Force
```

### Step 2.2: Test arXiv Client

Create `data_sources/arxiv_client.py` (use provided implementation)

**Test:**
```powershell
python -c "from data_sources.arxiv_client import ArxivClient; client = ArxivClient(); papers = client.search_papers('machine learning', max_results=5); print(f'Found {len(papers)} papers')"
```

### Step 2.3: Download Sample Papers

```powershell
python scripts/download_sample_papers.py --query "neural networks" --num 10
```

---

## Phase 3: Database Infrastructure

### Step 3.1: Start Docker Containers

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: research_navigator_postgres
    environment:
      POSTGRES_DB: research_papers_db
      POSTGRES_USER: research_user
      POSTGRES_PASSWORD: research_password_2024
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  neo4j:
    image: neo4j:5.13.0
    container_name: research_navigator_neo4j
    environment:
      NEO4J_AUTH: neo4j/research_password_2024
      NEO4J_PLUGINS: '["apoc"]'
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
```

**Start containers:**
```powershell
docker-compose up -d

# Verify
docker ps
```

### Step 3.2: Initialize Databases

**Create PostgreSQL schema:**
```powershell
docker exec -i research_navigator_postgres psql -U research_user -d research_papers_db < database\postgres_schema.sql
```

**Initialize all databases:**
```powershell
python scripts\init_databases.py
```

**Expected output:**
```
✓ PostgreSQL initialized
✓ Neo4j initialized
✓ FAISS initialized
```

### Step 3.3: Run Database Tests

```powershell
python tests\test_databases.py
```

**Expected:**
```
PostgreSQL: ✓ PASSED
Neo4j: ✓ PASSED
FAISS: ✓ PASSED
Unified Manager: ✓ PASSED

✓ ALL TESTS PASSED
```

---

## Phase 4: NLP Pipeline & Knowledge Graph

### Step 4.1: Create NLP Modules

```powershell
New-Item -Path "nlp" -ItemType Directory
```

Create these files:
- `nlp/entity_extractor.py`
- `nlp/knowledge_graph_builder.py`
- `nlp/embedding_pipeline.py`

### Step 4.2: Populate Database

**Download and process papers:**
```powershell
python scripts\pipeline_runner.py --mode full --query "machine learning" --num 20
```

This will:
1. Download 20 papers from arXiv
2. Parse PDFs
3. Extract entities (authors, methods, datasets)
4. Build knowledge graph in Neo4j
5. Create embeddings in FAISS

### Step 4.3: Alternative Processing Modes

**Build knowledge graph only:**
```powershell
python scripts\pipeline_runner.py --mode kg-only
```

**Create embeddings only:**
```powershell
python scripts\pipeline_runner.py --mode embeddings-only
```

**Check system status:**
```powershell
python scripts\pipeline_runner.py --mode status
```

### Step 4.4: Verify Phase 4

```powershell
python scripts\verify_phase4.py
```

**Expected:**
```
✓ Entity extraction working
✓ Database has papers
✓ Knowledge graph populated
✓ Embeddings created
✓ Semantic search working

✓ PHASE 4 FULLY OPERATIONAL
```

---

## Phase 5: Backend API

### Step 5.1: Install API Dependencies

Create `requirements_api.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
pytest-asyncio==0.21.1
```

**Install:**
```powershell
pip install -r requirements_api.txt
```

### Step 5.2: Create API Structure

```powershell
New-Item -Path "api" -ItemType Directory
New-Item -Path "api\routers" -ItemType Directory
New-Item -Path "api\schemas" -ItemType Directory
```

### Step 5.3: Start API Server

```powershell
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify:**
- Open browser: http://localhost:8000/docs
- Interactive API documentation (Swagger UI)

### Step 5.4: Test API Endpoints

```powershell
# Test health check
curl http://localhost:8000/health

# Test papers list
curl http://localhost:8000/api/papers/

# Test semantic search
curl -X POST http://localhost:8000/api/search/semantic -H "Content-Type: application/json" -d "{\"query\":\"neural networks\",\"top_k\":5}"
```

### Step 5.5: Run API Tests

```powershell
pytest tests\test_api.py -v
```

**Expected:**
```
test_health PASSED
test_system_status PASSED
test_list_papers PASSED
test_root PASSED

4 passed
```

---

## Quick Start Guide

### Starting the System

**1. Start Docker containers:**
```powershell
cd D:\MS Acad\EDS\Project\ScholarLens-v2
docker-compose up -d
```

**2. Activate Python environment:**
```powershell
.\venv\Scripts\Activate.ps1
```

**3. Start Backend API:**
```powershell
uvicorn api.main:app --reload
```

**4. (Optional) Start Frontend:**
```powershell
cd ..\ScholarLens-Frontend
npm start
```

### Accessing the System

| Component | URL | Credentials |
|-----------|-----|-------------|
| API Documentation | http://localhost:8000/docs | N/A |
| Neo4j Browser | http://localhost:7474 | neo4j / research_password_2024 |
| Frontend | http://localhost:3000 | N/A |

### Stopping the System

```powershell
# Stop API (Ctrl+C in terminal)

# Stop Docker containers
docker-compose down
```

---

## Troubleshooting

### Issue: Docker containers not starting

**Solution:**
```powershell
# Check Docker Desktop is running
docker ps

# Restart containers
docker-compose restart

# Check logs
docker logs research_navigator_postgres
docker logs research_navigator_neo4j
```

### Issue: PostgreSQL connection failed

**Solution:**
```powershell
# Verify container is running
docker ps | findstr postgres

# Test connection
docker exec -it research_navigator_postgres psql -U research_user -d research_papers_db -c "SELECT version();"

# Check .env file has correct credentials
```

### Issue: Neo4j password error

**Solution:**
```powershell
# Reset Neo4j password
docker exec -it research_navigator_neo4j cypher-shell -u neo4j -p neo4j
# Then: ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'research_password_2024';
```

### Issue: Python module not found

**Solution:**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### Issue: FAISS not loading

**Solution:**
```powershell
# Reinstall FAISS
pip uninstall faiss-cpu
pip install faiss-cpu==1.7.4

# Verify
python -c "import faiss; print('FAISS version:', faiss.__version__)"
```

### Issue: API CORS errors

**Solution:**
- Verify `api/config.py` includes frontend URL in `ALLOWED_ORIGINS`
- Should include: `http://localhost:3000`
- Restart API server after changes

### Issue: Out of memory during processing

**Solution:**
```powershell
# Process fewer papers at once
python scripts\pipeline_runner.py --mode full --query "your query" --num 5

# Or use batch processing
python scripts\pipeline_runner.py --mode embeddings-only --batch-size 3
```

---

## Project Structure

```
ScholarLens-v2/
├── api/                    # FastAPI backend
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic models
│   ├── main.py            # API entry point
│   └── config.py          # Configuration
├── data_sources/          # Data collection
│   ├── arxiv_client.py    # arXiv API client
│   └── pubmed_client.py   # PubMed client
├── processing/            # Text processing
│   ├── pdf_parser.py      # PDF extraction
│   └── text_preprocessor.py
├── database/              # Database layer
│   ├── postgres_db.py     # PostgreSQL interface
│   ├── neo4j_schema.py    # Neo4j interface
│   ├── vector_store.py    # FAISS interface
│   └── db_manager.py      # Unified manager
├── nlp/                   # NLP pipeline
│   ├── entity_extractor.py
│   ├── knowledge_graph_builder.py
│   └── embedding_pipeline.py
├── scripts/               # Utility scripts
│   ├── init_databases.py
│   ├── pipeline_runner.py
│   └── verify_phase4.py
├── tests/                 # Test suite
│   ├── test_databases.py
│   └── test_api.py
├── data/                  # Data storage
│   ├── pdfs/             # Downloaded papers
│   └── faiss_index/      # Vector index
├── .env                   # Environment variables
├── docker-compose.yml     # Docker configuration
└── requirements.txt       # Python dependencies
```

---

## Common Commands Reference

### Database Operations
```powershell
# Initialize databases
python scripts\init_databases.py

# Check database status
python scripts\pipeline_runner.py --mode status

# View Neo4j data
# Open http://localhost:7474 and run:
MATCH (n) RETURN n LIMIT 25
```

### Data Processing
```powershell
# Full pipeline (download + process)
python scripts\pipeline_runner.py --mode full --query "your topic" --num 10

# Build knowledge graph from existing papers
python scripts\pipeline_runner.py --mode kg-only

# Create embeddings from existing papers
python scripts\pipeline_runner.py --mode embeddings-only
```

### API Operations
```powershell
# Start API server
uvicorn api.main:app --reload

# Run API tests
pytest tests\test_api.py -v

# Test specific endpoint
curl http://localhost:8000/api/papers/
```

### Docker Operations
```powershell
# Start all containers
docker-compose up -d

# Stop all containers
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart postgres
```

---

## Performance Optimization (16GB RAM)

### Memory-Efficient Settings

**1. Limit batch sizes:**
```python
# In pipeline_runner.py
batch_size = 5  # Process 5 papers at a time
```

**2. Reduce embedding batch size:**
```python
# In embedding_pipeline.py
embedding_pipeline.batch_process_papers(papers, batch_size=3)
```

**3. Limit FAISS search results:**
```python
# Keep top_k low
results = vector_store.search(query, top_k=10)
```

### Docker Resource Limits

Add to `docker-compose.yml`:
```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 4G
  neo4j:
    deploy:
      resources:
        limits:
          memory: 4G
```

---

## Next Steps

After completing Phases 1-5, you can:

1. **Phase 6:** Build React frontend for visualization
2. **Phase 7:** Deploy to cloud (AWS, Azure, or Google Cloud)
3. **Add authentication:** User login and access control
4. **Advanced analytics:** Research trend analysis and predictions
5. **Citation network:** Build and visualize citation graphs
6. **Collaboration detection:** Find research communities

---

## Support & Resources

- **spaCy Documentation:** https://spacy.io/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Neo4j Documentation:** https://neo4j.com/docs/
- **FAISS Documentation:** https://github.com/facebookresearch/faiss

---

## License

This project is for educational purposes.

---

**Last Updated:** 7 November 2025  
**Version:** 1.0  
**Status:** Backend done