"""
RAG retrieval for ScholarLens.
Embeddings are computed once (at upload time) with sentence-transformers and
persisted via pgvector, so retrieval is a single ORDER BY ... <=> query
instead of rebuilding an in-memory index every session.
"""

from typing import List, Dict, Optional

from models import Paper, PaperChunk, IS_POSTGRES
from utils.embeddings import embed_texts, embed_query


def embed_and_store_chunks(chunks: List[PaperChunk]) -> None:
    """Compute and assign embeddings for already-flushed PaperChunk rows."""
    if not IS_POSTGRES or not chunks:
        return
    vectors = embed_texts([c.content for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = vector


def embed_and_store_paper(paper: Paper) -> None:
    """Compute and assign a title+abstract embedding for paper-level similarity."""
    if not IS_POSTGRES:
        return
    text = f"{paper.title}\n\n{paper.abstract or ''}"
    paper.embedding = embed_texts([text])[0]


def search_chunks(session, query: str, top_k: int = 5, paper_id: Optional[int] = None) -> List[Dict]:
    """Nearest-neighbor search over paper_chunks by cosine distance."""
    if not IS_POSTGRES or not query.strip():
        return []

    query_vector = embed_query(query)
    distance = PaperChunk.embedding.cosine_distance(query_vector)

    q = (
        session.query(PaperChunk, Paper.title, distance.label('distance'))
        .join(Paper, Paper.id == PaperChunk.paper_id)
        .filter(PaperChunk.embedding.isnot(None))
    )
    if paper_id is not None:
        q = q.filter(PaperChunk.paper_id == paper_id)
    q = q.order_by(distance).limit(top_k)

    return [
        {
            'content': chunk.content,
            'paper_id': chunk.paper_id,
            'paper_title': title,
            'section': chunk.section,
            'score': float(1 - dist),
        }
        for chunk, title, dist in q.all()
    ]


def find_similar_papers(session, query: str, top_k: int = 5) -> List[Dict]:
    """Nearest-neighbor search over papers (title+abstract embedding) by cosine distance."""
    if not IS_POSTGRES or not query.strip():
        return []

    query_vector = embed_query(query)
    distance = Paper.embedding.cosine_distance(query_vector)

    q = (
        session.query(Paper, distance.label('distance'))
        .filter(Paper.embedding.isnot(None))
        .order_by(distance)
        .limit(top_k)
    )

    return [
        {
            'id': paper.id,
            'title': paper.title,
            'abstract': paper.abstract,
            'similarity_score': float(1 - dist),
        }
        for paper, dist in q.all()
    ]


def backfill_missing_embeddings(session, batch_size: int = 32) -> Dict:
    """Compute embeddings for any papers/chunks that predate the RAG migration."""
    counts = {'papers': 0, 'chunks': 0}
    if not IS_POSTGRES:
        return counts

    papers = session.query(Paper).filter(Paper.embedding.is_(None)).all()
    for paper in papers:
        embed_and_store_paper(paper)
    if papers:
        counts['papers'] = len(papers)
        session.commit()

    chunks = session.query(PaperChunk).filter(PaperChunk.embedding.is_(None)).all()
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embed_and_store_chunks(batch)
        session.commit()
        counts['chunks'] += len(batch)

    return counts
