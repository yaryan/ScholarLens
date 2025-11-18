"""
Comprehensive database testing script

Tests PostgreSQL, Neo4j, and FAISS functionality.

Usage:
    python tests\test_databases.py
"""

import sys

sys.path.append('.')

from database.postgres_db import PostgresDatabase
from database.neo4j_schema import Neo4jDatabase
from database.vector_store import FAISSVectorStore
from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_postgres():
    """Test PostgreSQL operations"""
    print("\n" + "=" * 70)
    print("TEST 1: PostgreSQL")
    print("=" * 70)

    try:
        db = PostgresDatabase()

        # Test 1.1: Connection
        print("\n[1.1] Testing connection...")
        stats = db.get_database_statistics()
        print(f"✓ Connected. Total papers: {stats['total_papers']}")

        # Test 1.2: Add paper
        print("\n[1.2] Testing paper insertion...")
        test_paper = {
            'arxiv_id': 'test_1234',
            'title': 'Test Paper for Database Testing',
            'abstract': 'This is a test paper.',
            'published_date': '2025-10-29',
            'primary_category': 'cs.AI'
        }

        try:
            paper = db.add_paper(test_paper)
            print(f"✓ Paper added: ID={paper.paper_id}")
        except Exception as e:
            print(f"⚠ Paper may already exist: {e}")

        # Test 1.3: Search
        print("\n[1.3] Testing search...")
        results = db.search_papers("deep learning", limit=3)
        print(f"✓ Found {len(results)} papers")

        db.close()
        print("\n✓ PostgreSQL tests passed")
        return True

    except Exception as e:
        print(f"\n✗ PostgreSQL test failed: {e}")
        return False


def test_neo4j():
    """Test Neo4j operations"""
    print("\n" + "=" * 70)
    print("TEST 2: Neo4j")
    print("=" * 70)

    try:
        db = Neo4jDatabase()

        # Test 2.1: Connection
        print("\n[2.1] Testing connection...")
        stats = db.get_graph_statistics()
        print(f"✓ Connected. Total papers: {stats.get('papers', 0)}")

        # Test 2.2: Create nodes
        print("\n[2.2] Testing node creation...")
        paper_node = db.create_paper_node(
            paper_id=9999,
            title="Test Paper for Neo4j",
            abstract="Testing Neo4j operations",
            published_date="2025-10-29"
        )
        print(f"✓ Paper node created")

        author_node = db.create_author_node(
            author_id=9999,
            name="Test Author"
        )
        print(f"✓ Author node created")

        # Test 2.3: Create relationship
        print("\n[2.3] Testing relationship creation...")
        db.create_authored_relationship(9999, 9999)
        print(f"✓ Relationship created")

        # Test 2.4: Query
        print("\n[2.4] Testing queries...")
        papers = db.get_author_papers(9999)
        print(f"✓ Found {len(papers)} papers for test author")

        db.close()
        print("\n✓ Neo4j tests passed")
        return True

    except Exception as e:
        print(f"\n✗ Neo4j test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_faiss():
    """Test FAISS vector store"""
    print("\n" + "=" * 70)
    print("TEST 3: FAISS Vector Store")
    print("=" * 70)

    try:
        vector_store = FAISSVectorStore()

        # Test 3.1: Index status
        print("\n[3.1] Testing index status...")
        stats = vector_store.get_statistics()
        print(f"✓ Index loaded. Total vectors: {stats['total_vectors']}")

        # Test 3.2: Add documents
        print("\n[3.2] Testing document addition...")
        test_texts = [
            "This is a test document about machine learning",
            "Another test document about neural networks"
        ]
        test_metadata = [
            {'doc_id': 'test_1', 'source': 'test'},
            {'doc_id': 'test_2', 'source': 'test'}
        ]

        initial_count = vector_store.index.ntotal if vector_store.index else 0
        vector_store.add_documents(test_texts, test_metadata)
        final_count = vector_store.index.ntotal

        print(f"✓ Added {final_count - initial_count} documents")

        # Test 3.3: Search
        print("\n[3.3] Testing search...")
        results = vector_store.search("machine learning", top_k=2)
        print(f"✓ Found {len(results)} results")

        if results:
            print(f"  Top result similarity: {results[0][1]:.4f}")

        # Save
        vector_store.save()

        print("\n✓ FAISS tests passed")
        return True

    except Exception as e:
        print(f"\n✗ FAISS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_manager():
    """Test unified database manager"""
    print("\n" + "=" * 70)
    print("TEST 4: Unified Database Manager")
    print("=" * 70)

    try:
        with DatabaseManager() as db_manager:
            # Test 4.1: Initialization
            print("\n[4.1] Testing initialization...")
            print("✓ All databases connected")

            # Test 4.2: Statistics
            print("\n[4.2] Testing statistics...")
            stats = db_manager.get_complete_statistics()

            print("  PostgreSQL papers:", stats['postgres'].get('total_papers', 0))
            print("  Neo4j papers:", stats['neo4j'].get('papers', 0))
            print("  FAISS vectors:", stats['vector_store'].get('total_vectors', 0))

            print("✓ Statistics retrieved")

        print("\n✓ Unified Manager tests passed")
        return True

    except Exception as e:
        print(f"\n✗ Unified Manager test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE DATABASE TESTING")
    print("=" * 70)

    print("\nRunning tests...")

    results = {
        'PostgreSQL': test_postgres(),
        'Neo4j': test_neo4j(),
        'FAISS': test_faiss(),
        'Unified Manager': test_unified_manager()
    }

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{test_name}: {status}")

    if all(results.values()):
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED")

    print("=" * 70)


if __name__ == "__main__":
    main()
