"""
Main API entry point for FastAPI.
"""

from fastapi import FastAPI
from api.config import settings
from api.routers import papers, search, knowledge_graph, analytics, health
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers.router)
app.include_router(search.router)
app.include_router(knowledge_graph.router)
app.include_router(analytics.router)
app.include_router(health.router)

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to the Research Knowledge Navigator API. Docs: /docs"}
