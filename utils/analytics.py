"""
Analytics and SQL reporting utilities for ScholarLens
Provides 8+ analytical reports for research data analysis
"""

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime


def get_top_coauthorship_pairs(session: Session, limit: int = 10) -> List[Dict]:
    """
    Report 1: Top co-authorship pairs by publication count
    """
    query = text("""
        SELECT 
            a1.name as author1,
            a2.name as author2,
            COUNT(DISTINCT pa1.paper_id) as collaboration_count
        FROM paper_authors pa1
        JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id AND pa1.author_id < pa2.author_id
        JOIN authors a1 ON pa1.author_id = a1.id
        JOIN authors a2 ON pa2.author_id = a2.id
        GROUP BY a1.id, a2.id, a1.name, a2.name
        ORDER BY collaboration_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    return [{"author1": row[0], "author2": row[1], "count": row[2]} for row in result]


def get_trending_topics_over_time(session: Session) -> List[Dict]:
    """
    Report 2: Most cited or trending research topics over time
    """
    try:
        query = text("""
            SELECT 
                m.name as method,
                COALESCE(m.category, 'unknown') as category,
                p.year,
                COUNT(*) as paper_count
            FROM methods m
            JOIN paper_methods pm ON m.id = pm.method_id
            JOIN papers p ON pm.paper_id = p.id
            WHERE p.year IS NOT NULL
            GROUP BY m.id, m.name, m.category, p.year
            ORDER BY p.year DESC, paper_count DESC
        """)
        
        result = session.execute(query)
        return [{"method": row[0], "category": row[1], "year": row[2], "count": row[3]} for row in result]
    except Exception:
        return []


def get_papers_per_institution(session: Session, limit: int = 20) -> List[Dict]:
    """
    Report 3: Paper count per institution
    """
    query = text("""
        SELECT 
            i.name as institution,
            i.country,
            i.type,
            COUNT(DISTINCT pa.paper_id) as paper_count
        FROM institutions i
        JOIN author_institutions ai ON i.id = ai.institution_id
        JOIN authors a ON ai.author_id = a.id
        JOIN paper_authors pa ON a.id = pa.author_id
        GROUP BY i.id, i.name, i.country, i.type
        ORDER BY paper_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    return [{"institution": row[0], "country": row[1], "type": row[2], "count": row[3]} for row in result]


def get_research_growth_by_field(session: Session) -> List[Dict]:
    """
    Report 4: Growth rate of research in specific AI subfields
    """
    try:
        query = text("""
            SELECT 
                COALESCE(m.category, 'unknown') as category,
                p.year,
                COUNT(*) as paper_count
            FROM methods m
            JOIN paper_methods pm ON m.id = pm.method_id
            JOIN papers p ON pm.paper_id = p.id
            WHERE p.year IS NOT NULL
            GROUP BY m.category, p.year
            ORDER BY m.category, p.year
        """)
        
        result = session.execute(query)
        rows = [{"category": row[0], "year": row[1], "count": row[2]} for row in result]
        
        for i, row in enumerate(rows):
            if i > 0 and rows[i-1]['category'] == row['category']:
                row['growth'] = row['count'] - rows[i-1]['count']
            else:
                row['growth'] = 0
        
        return rows
    except Exception:
        return []


def get_top_authors_by_publication(session: Session, limit: int = 20) -> List[Dict]:
    """
    Report 5: Top authors by publication frequency
    """
    query = text("""
        SELECT 
            a.name,
            COUNT(DISTINCT pa.paper_id) as paper_count,
            a.h_index,
            a.total_citations
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        GROUP BY a.id, a.name, a.h_index, a.total_citations
        ORDER BY paper_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    return [{"name": row[0], "paper_count": row[1], "h_index": row[2], "citations": row[3]} for row in result]


def get_most_used_datasets(session: Session, limit: int = 20) -> List[Dict]:
    """
    Report 6: Datasets most frequently reused across papers
    """
    query = text("""
        SELECT 
            d.name,
            d.domain,
            COUNT(DISTINCT pd.paper_id) as usage_count,
            d.description
        FROM datasets d
        JOIN paper_datasets pd ON d.id = pd.dataset_id
        GROUP BY d.id, d.name, d.domain, d.description
        ORDER BY usage_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    return [{"name": row[0], "domain": row[1], "usage_count": row[2], "description": row[3]} for row in result]


def get_collaboration_network_density(session: Session) -> Dict:
    """
    Report 7: Collaboration network density metrics
    """
    author_count_query = text("SELECT COUNT(*) FROM authors")
    author_count = session.execute(author_count_query).scalar() or 0
    
    collab_query = text("""
        SELECT COUNT(DISTINCT 
            CASE WHEN pa1.author_id < pa2.author_id
            THEN pa1.author_id || '-' || pa2.author_id
            ELSE pa2.author_id || '-' || pa1.author_id
            END
        ) as collaboration_pairs
        FROM paper_authors pa1
        JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id AND pa1.author_id != pa2.author_id
    """)
    collab_count = session.execute(collab_query).scalar() or 0
    
    max_possible = (author_count * (author_count - 1)) / 2 if author_count > 1 else 1
    density = collab_count / max_possible if max_possible > 0 else 0
    
    avg_collabs_query = text("""
        SELECT AVG(collab_count) FROM (
            SELECT a.id, COUNT(DISTINCT pa2.author_id) as collab_count
            FROM authors a
            JOIN paper_authors pa1 ON a.id = pa1.author_id
            JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id AND pa1.author_id != pa2.author_id
            GROUP BY a.id
        ) subq
    """)
    avg_collaborators = session.execute(avg_collabs_query).scalar() or 0
    
    return {
        "total_authors": author_count,
        "unique_collaborations": collab_count,
        "network_density": round(density, 4),
        "avg_collaborators_per_author": round(float(avg_collaborators), 2) if avg_collaborators else 0
    }


def get_emerging_methods(session: Session, recent_years: int = 2) -> List[Dict]:
    """
    Report 8: Recent methods emerging in multiple domains
    """
    current_year = datetime.now().year
    
    query = text("""
        SELECT 
            m.name,
            m.category,
            COUNT(DISTINCT pm.paper_id) as paper_count,
            COUNT(DISTINCT m.category) as domain_count,
            MIN(p.year) as first_appeared
        FROM methods m
        JOIN paper_methods pm ON m.id = pm.method_id
        JOIN papers p ON pm.paper_id = p.id
        WHERE p.year >= :min_year
        GROUP BY m.id, m.name, m.category
        HAVING COUNT(DISTINCT pm.paper_id) >= 2
        ORDER BY paper_count DESC, first_appeared DESC
        LIMIT 20
    """)
    
    result = session.execute(query, {"min_year": current_year - recent_years})
    return [{"name": row[0], "category": row[1], "paper_count": row[2], 
             "domain_count": row[3], "first_appeared": row[4]} for row in result]


def get_dataset_method_cooccurrence(session: Session, limit: int = 20) -> List[Dict]:
    """
    Additional Report: Dataset-Method co-occurrence patterns
    """
    query = text("""
        SELECT 
            d.name as dataset,
            m.name as method,
            COUNT(DISTINCT p.id) as co_occurrence_count
        FROM datasets d
        JOIN paper_datasets pd ON d.id = pd.dataset_id
        JOIN papers p ON pd.paper_id = p.id
        JOIN paper_methods pm ON p.id = pm.paper_id
        JOIN methods m ON pm.method_id = m.id
        GROUP BY d.id, d.name, m.id, m.name
        ORDER BY co_occurrence_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {"limit": limit})
    return [{"dataset": row[0], "method": row[1], "count": row[2]} for row in result]


def get_yearly_publication_stats(session: Session) -> List[Dict]:
    """
    Get yearly publication statistics
    """
    query = text("""
        SELECT 
            year,
            COUNT(*) as paper_count
        FROM papers
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
    """)
    
    result = session.execute(query)
    return [{"year": row[0], "count": row[1]} for row in result]


def get_method_category_distribution(session: Session) -> List[Dict]:
    """
    Get distribution of methods by category
    """
    query = text("""
        SELECT 
            COALESCE(category, 'Other') as category,
            COUNT(*) as method_count,
            SUM(usage_count) as total_usage
        FROM methods
        GROUP BY category
        ORDER BY method_count DESC
    """)
    
    result = session.execute(query)
    return [{"category": row[0], "method_count": row[1], "total_usage": row[2] or 0} for row in result]


def get_summary_statistics(session: Session) -> Dict:
    """
    Get overall summary statistics
    """
    paper_count = session.execute(text("SELECT COUNT(*) FROM papers")).scalar() or 0
    author_count = session.execute(text("SELECT COUNT(*) FROM authors")).scalar() or 0
    method_count = session.execute(text("SELECT COUNT(*) FROM methods")).scalar() or 0
    dataset_count = session.execute(text("SELECT COUNT(*) FROM datasets")).scalar() or 0
    institution_count = session.execute(text("SELECT COUNT(*) FROM institutions")).scalar() or 0
    
    return {
        "total_papers": paper_count,
        "total_authors": author_count,
        "total_methods": method_count,
        "total_datasets": dataset_count,
        "total_institutions": institution_count
    }
