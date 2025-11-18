"""
Test entity extraction

Usage:
    python tests\test_entity_extraction.py
"""

import sys

sys.path.append('.')

from nlp.entity_extractor import EntityExtractor


def test_entity_extraction():
    """Test entity extraction functionality"""
    print("\n" + "=" * 70)
    print("TESTING ENTITY EXTRACTION")
    print("=" * 70)

    try:
        # Initialize
        print("\n[1/4] Initializing extractor...")
        extractor = EntityExtractor()
        print("✓ Extractor initialized")

        # Test text
        print("\n[2/4] Testing entity extraction...")
        test_text = """
        The paper by John Smith from Stanford University describes a CNN architecture
        trained on ImageNet using BERT embeddings. The model achieves 95% accuracy.
        """

        entities = extractor.extract_entities(test_text)

        # Verify results
        assert len(entities['persons']) > 0, "No persons extracted"
        assert len(entities['institutions']) > 0, "No institutions extracted"
        assert len(entities['methods']) > 0, "No methods extracted"
        assert len(entities['datasets']) > 0, "No datasets extracted"

        print("✓ Entity extraction successful")
        print(f"  Found {len(entities['persons'])} persons")
        print(f"  Found {len(entities['institutions'])} institutions")
        print(f"  Found {len(entities['methods'])} methods")
        print(f"  Found {len(entities['datasets'])} datasets")

        # Test batch extraction
        print("\n[3/4] Testing batch extraction...")
        texts = [test_text] * 5
        batch_results = extractor.batch_extract(texts, batch_size=2)

        assert len(batch_results) == 5, "Batch extraction failed"
        print(f"✓ Batch extracted from {len(batch_results)} texts")

        # Test statistics
        print("\n[4/4] Testing statistics...")
        stats = extractor.get_statistics(entities)
        assert stats['total'] > 0, "No entities in statistics"
        print(f"✓ Statistics generated: {stats['total']} total entities")

        print("\n" + "=" * 70)
        print("✓ ALL ENTITY EXTRACTION TESTS PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_entity_extraction()
    sys.exit(0 if success else 1)
