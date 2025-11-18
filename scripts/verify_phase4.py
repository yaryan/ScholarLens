"""
Phase 4 Verification Script

Usage:
    python scripts\verify_phase4.py
"""

import sys
sys.path.append('.')

from database.db_manager import DatabaseManager
from nlp.entity_extractor import EntityExtractor
from nlp.embedding_pipeline import EmbeddingPipeline


def verify_phase4():
    """Verify Phase 4 components"""
    print("\n" + "="*70)
    print("PHASE 4 VERIFICATION")
    print("="*70)

    results = {}

    # Test 1: Entity Extraction
    print("\n[1/4] Testing entity extraction...")
    try:
        extractor = EntityExtractor()
        test_text = "This paper by John Smith from MIT uses Convolutional Neural Networks and BERT on ImageNet dataset."

        entities = extractor.extract_entities(test_text)

        has_persons = len(entities.get('persons', [])) > 0
        has_methods = len(entities.get('methods', [])) > 0
        has_datasets = len(entities.get('datasets', [])) > 0
        has_institutions = len(entities.get('institutions', [])) > 0

        if has_persons and has_methods and has_datasets:
            print("✓ Entity extraction working")
            print(f"  Found: {len(entities['persons'])} persons, {len(entities['methods'])} methods, {len(entities['datasets'])} datasets")
            results['entity_extraction'] = True
        else:
            print("⚠ Entity extraction incomplete")
            print(f"  Persons: {has_persons}, Methods: {has_methods}, Datasets: {has_datasets}")
            results['entity_extraction'] = False

    except Exception as e:
        print(f"✗ Entity extraction failed: {e}")
        results['entity_extraction'] = False

    # Test 2: Database populated
    print("\n[2/4] Checking database...")
    try:
        with DatabaseManager() as db:
            stats = db.get_complete_statistics()

            pg_papers = stats.get('postgresql', {}).get('total_papers', 0)
            neo_papers = stats.get('neo4j', {}).get('papers', 0)
            faiss_vectors = stats.get('vector_store', {}).get('total_vectors', 0)

            has_papers = pg_papers > 0
            has_kg = neo_papers > 0
            has_embeddings = faiss_vectors > 0

            if has_papers:
                print(f"✓ PostgreSQL has {pg_papers} papers")
            else:
                print("⚠ No papers in PostgreSQL")

            if has_kg:
                print(f"✓ Neo4j has {neo_papers} papers")
            else:
                print("⚠ No papers in Neo4j (run kg-only)")

            if has_embeddings:
                print(f"✓ FAISS has {faiss_vectors} embeddings")
            else:
                print("⚠ No embeddings (run embeddings-only)")

            results['database'] = has_papers
            results['knowledge_graph'] = has_kg
            results['embeddings'] = has_embeddings

    except Exception as e:
        print(f"✗ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        results['database'] = False
        results['knowledge_graph'] = False
        results['embeddings'] = False

    # Test 3: Semantic search
    print("\n[3/4] Testing semantic search...")
    try:
        pipeline = EmbeddingPipeline()
        stats = pipeline.get_statistics()

        if stats['total_vectors'] > 0:
            # Use the correct search method that returns proper format
            from database.vector_store import FAISSVectorStore
            vs = FAISSVectorStore()
            results_list = vs.search("neural networks", top_k=1)

            if results_list:
                print(f"✓ Semantic search working ({len(results_list)} results)")
                print(f"  Top result similarity: {results_list[0][1]:.3f}")
                results['search'] = True
            else:
                print("⚠ Search returned no results")
                results['search'] = False
        else:
            print("⚠ No vectors for search (run embeddings-only)")
            results['search'] = False

    except Exception as e:
        print(f"✗ Search failed: {e}")
        import traceback
        traceback.print_exc()
        results['search'] = False

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    for component, status in results.items():
        status_str = "✓ PASSED" if status else "⚠ NOT READY"
        print(f"{component}: {status_str}")

    # Determine readiness
    core_working = (
        results.get('entity_extraction', False) and
        results.get('database', False)
    )

    full_system = all(results.values())

    print("\n" + "="*70)

    if full_system:
        print("✓ PHASE 4 FULLY OPERATIONAL")
        print("\nYour Research Knowledge Navigator is ready!")
        print("\nNext steps:")
        print("  1. Phase 5: Build Backend API (FastAPI)")
        print("  2. Phase 6: Build Frontend (React)")
        print("  3. Deploy and use!")

    elif core_working:
        print("✓ PHASE 4 CORE COMPONENTS WORKING")
        print("\nTo complete setup, run:")

        if not results.get('knowledge_graph', False):
            print("  python scripts\\pipeline_runner.py --mode kg-only")

        if not results.get('embeddings', False):
            print("  python scripts\\pipeline_runner.py --mode embeddings-only")

    else:
        print("⚠ PHASE 4 NOT READY")
        print("\nRun the full pipeline:")
        print("  python scripts\\pipeline_runner.py --mode full --query \"machine learning\" --num 10")

    print("="*70)

    return full_system


if __name__ == "__main__":
    success = verify_phase4()
    sys.exit(0 if success else 1)
