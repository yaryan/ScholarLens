"""
Test script for arXiv client

Run with: python tests/test_arxiv_client.py
"""

import sys

sys.path.append('.')

from data_sources.arxiv_client import ArxivClient
import os


def test_search():
    """Test basic search functionality"""
    print("Test 1: Basic Search")
    print("-" * 50)

    client = ArxivClient(max_results=3)
    papers = client.search_papers(query="machine learning", max_results=3)

    assert len(papers) > 0, "No papers found"
    assert 'title' in papers[0], "Paper missing title"
    assert 'arxiv_id' in papers[0], "Paper missing arxiv_id"

    print(f"✓ Found {len(papers)} papers")
    print(f"✓ First paper: {papers[0]['title'][:50]}...")
    print("✓ Test passed\n")

    return papers


def test_download():
    """Test PDF download"""
    print("Test 2: PDF Download")
    print("-" * 50)

    client = ArxivClient()

    # Use a well-known paper
    paper = client.get_paper_by_id("1706.03762")  # Attention Is All You Need

    if paper:
        filepath = client.download_paper(paper)

        if filepath and os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ Downloaded: {filepath}")
            print(f"✓ File size: {file_size:,} bytes")
            print("✓ Test passed\n")
            return True

    print("✗ Test failed\n")
    return False


def test_category_search():
    """Test category-based search"""
    print("Test 3: Category Search")
    print("-" * 50)

    client = ArxivClient()
    papers = client.search_by_category("cs.AI", num_papers=5, date_range_days=7)

    assert len(papers) > 0, "No papers found in category"

    print(f"✓ Found {len(papers)} papers in cs.AI category")
    print("✓ Test passed\n")

    return papers


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING ARXIV CLIENT")
    print("=" * 70 + "\n")

    try:
        # Run tests
        papers = test_search()
        test_download()
        test_category_search()

        print("=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
