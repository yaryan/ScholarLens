"""
Complete Phase 3 verification

Usage:
    python scripts\verify_phase3.py
"""

import sys

sys.path.append('.')

import docker
from database.db_manager import DatabaseManager


def check_docker_containers():
    """Verify Docker containers are running"""
    print("\n[1/4] Checking Docker containers...")
    print("-" * 70)

    try:
        client = docker.from_env()
        containers = client.containers.list()

        postgres_running = any('postgres' in c.name.lower() for c in containers)
        neo4j_running = any('neo4j' in c.name.lower() for c in containers)

        if postgres_running:
            print("✓ PostgreSQL container running")
        else:
            print("✗ PostgreSQL container not found")

        if neo4j_running:
            print("✓ Neo4j container running")
        else:
            print("✗ Neo4j container not found")

        return postgres_running and neo4j_running

    except Exception as e:
        print(f"✗ Error checking containers: {e}")
        print("  Make sure Docker Desktop is running")
        return False


def check_database_connections():
    """Verify database connections"""
    print("\n[2/4] Checking database connections...")
    print("-" * 70)

    try:
        with DatabaseManager() as db:
            print("✓ All database connections successful")
            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def check_database_schemas():
    """Verify database schemas"""
    print("\n[3/4] Checking database schemas...")
    print("-" * 70)

    try:
        with DatabaseManager() as db:
            # Check PostgreSQL
            pg_stats = db.postgres.get_database_statistics()
            print(f"✓ PostgreSQL schema verified")

            # Check Neo4j
            neo_stats = db.neo4j.get_graph_statistics()
            print(f"✓ Neo4j schema verified")

            # Check FAISS
            faiss_stats = db.vector_store.get_statistics()
            print(f"✓ FAISS vector store verified")

            return True
    except Exception as e:
        print(f"✗ Schema check failed: {e}")
        return False


def check_operations():
    """Test basic operations"""
    print("\n[4/4] Testing basic operations...")
    print("-" * 70)

    try:
        with DatabaseManager() as db:
            # Test PostgreSQL query
            stats = db.postgres.get_database_statistics()
            print(f"✓ PostgreSQL query works ({stats['total_papers']} papers)")

            # Test Neo4j query
            graph_stats = db.neo4j.get_graph_statistics()
            print(f"✓ Neo4j query works ({graph_stats.get('papers', 0)} nodes)")

            # Test FAISS
            faiss_stats = db.vector_store.get_statistics()
            print(f"✓ FAISS works ({faiss_stats['total_vectors']} vectors)")

            return True
    except Exception as e:
        print(f"✗ Operations test failed: {e}")
        return False


def main():
    """Main verification"""
    print("\n" + "=" * 70)
    print("PHASE 3 COMPLETE VERIFICATION")
    print("=" * 70)

    results = {
        'Docker Containers': check_docker_containers(),
        'Database Connections': check_database_connections(),
        'Database Schemas': check_database_schemas(),
        'Basic Operations': check_operations()
    }

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for check_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{check_name}: {status}")

    if all(results.values()):
        print("\n✓ PHASE 3 COMPLETE - ALL CHECKS PASSED")
        print("\nYour database layer is fully operational!")
        print("\nNext steps:")
        print("  1. Populate with data: python scripts\\populate_sample_data.py")
        print("  2. Proceed to Phase 4: NLP Pipeline")
    else:
        print("\n✗ SOME CHECKS FAILED")
        print("\nTroubleshooting:")
        print("  1. Run: docker-compose up -d")
        print("  2. Run: python scripts\\init_databases.py")
        print("  3. Check .env file")

    print("=" * 70)


if __name__ == "__main__":
    main()
