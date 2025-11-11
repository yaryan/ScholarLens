"""
Initialize all databases

This script sets up PostgreSQL, Neo4j, and FAISS for first use.

Usage:
    python scripts\init_databases.py
"""

import sys

sys.path.append('.')

from database.postgres_db import PostgresDatabase
from database.neo4j_schema import Neo4jDatabase
from database.vector_store import FAISSVectorStore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_postgres():
    """Initialize PostgreSQL database"""
    print("\n" + "=" * 70)
    print("[1/3] INITIALIZING POSTGRESQL")
    print("=" * 70)

    try:
        db = PostgresDatabase()

        # Tables are already created by schema.sql
        # Just verify connection
        stats = db.get_database_statistics()

        print("\n✓ PostgreSQL initialized successfully")
        print(f"  Total tables: 13")
        print(f"  Current papers: {stats['total_papers']}")
        print(f"  Current authors: {stats['total_authors']}")

        db.close()
        return True

    except Exception as e:
        print(f"\n✗ PostgreSQL initialization failed: {e}")
        return False


def initialize_neo4j():
    """Initialize Neo4j database"""
    print("\n" + "=" * 70)
    print("[2/3] INITIALIZING NEO4J")
    print("=" * 70)

    try:
        db = Neo4jDatabase()

        # Create constraints and indexes
        print("\nCreating constraints and indexes...")
        db.create_constraints_and_indexes()

        # Get statistics
        stats = db.get_graph_statistics()

        print("\n✓ Neo4j initialized successfully")
        print(f"  Total nodes:")
        print(f"    Papers: {stats.get('papers', 0)}")
        print(f"    Authors: {stats.get('authors', 0)}")
        print(f"    Methods: {stats.get('methods', 0)}")
        print(f"    Datasets: {stats.get('datasets', 0)}")
        print(f"  Total relationships:")
        print(f"    Citations: {stats.get('citations', 0)}")
        print(f"    Collaborations: {stats.get('collaborations', 0)}")

        db.close()
        return True

    except Exception as e:
        print(f"\n✗ Neo4j initialization failed: {e}")
        return False


def initialize_faiss():
    """Initialize FAISS vector store"""
    print("\n" + "=" * 70)
    print("[3/3] INITIALIZING FAISS VECTOR STORE")
    print("=" * 70)

    try:
        vector_store = FAISSVectorStore()

        # Create index if not exists
        if vector_store.index is None:
            vector_store.create_index(index_type='flat')
            print("✓ Created new FAISS index")
        else:
            print(f"✓ Loaded existing index with {vector_store.index.ntotal} vectors")

        # Get statistics
        stats = vector_store.get_statistics()

        print("\n✓ FAISS initialized successfully")
        print(f"  Embedding model: {stats['embedding_model']}")
        print(f"  Vector dimension: {stats['dimension']}")
        print(f"  Total vectors: {stats['total_vectors']}")

        # Save
        vector_store.save()

        return True

    except Exception as e:
        print(f"\n✗ FAISS initialization failed: {e}")
        return False


def main():
    """Main initialization function"""
    print("\n" + "=" * 70)
    print("DATABASE INITIALIZATION")
    print("=" * 70)
    print("\nThis script will initialize:")
    print("  1. PostgreSQL (structured metadata)")
    print("  2. Neo4j (knowledge graph)")
    print("  3. FAISS (vector embeddings)")

    input("\nPress Enter to continue...")

    # Initialize all databases
    results = {
        'PostgreSQL': initialize_postgres(),
        'Neo4j': initialize_neo4j(),
        'FAISS': initialize_faiss()
    }

    # Summary
    print("\n" + "=" * 70)
    print("INITIALIZATION SUMMARY")
    print("=" * 70)

    for db_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{db_name}: {status}")

    if all(results.values()):
        print("\n✓ ALL DATABASES INITIALIZED SUCCESSFULLY")
        print("\nNext steps:")
        print("  1. Download papers: python scripts\\download_papers.py")
        print("  2. Process PDFs: python scripts\\process_pdfs.py")
        print("  3. Populate database: python scripts\\populate_sample_data.py")
    else:
        print("\n✗ SOME DATABASES FAILED TO INITIALIZE")
        print("Check the error messages above and:")
        print("  1. Verify Docker containers are running: docker ps")
        print("  2. Check .env file has correct credentials")
        print("  3. Ensure ports 5432 and 7687 are not blocked")

    print("=" * 70)


if __name__ == "__main__":
    main()
