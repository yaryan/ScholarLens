"""
Complete Phase 2 verification script

This script tests all Phase 2 components
"""

import sys
sys.path.append('.')

from data_sources.arxiv_client import ArxivClient
from processing.pdf_parser import PDFParser
from processing.text_preprocessor import TextPreprocessor
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_phase2():
    """Run all Phase 2 verifications"""

    print("\n" + "="*70)
    print("PHASE 2 COMPLETE VERIFICATION")
    print("="*70)

    # Test 1: arXiv Client
    print("\n[1/4] Testing arXiv Client...")
    try:
        client = ArxivClient(max_results=3)
        papers = client.search_papers("deep learning", max_results=3)
        assert len(papers) > 0
        print("✓ arXiv client working")
    except Exception as e:
        print(f"✗ arXiv client failed: {e}")
        return False

    # Test 2: PDF Download
    print("\n[2/4] Testing PDF Download...")
    try:
        if papers:
            filepath = client.download_paper(papers[0])
            assert filepath and Path(filepath).exists()
            print(f"✓ PDF download working")
    except Exception as e:
        print(f"✗ PDF download failed: {e}")
        return False

    # Test 3: PDF Parser
    print("\n[3/4] Testing PDF Parser...")
    try:
        pdf_files = list(Path('./data/pdfs').glob('*.pdf'))
        if pdf_files:
            parser = PDFParser(str(pdf_files[0]))
            text = parser.extract_text()
            cleaned = parser.clean_text()
            assert len(cleaned) > 0
            print("✓ PDF parser working")
        else:
            print("⚠ No PDFs to test")
    except Exception as e:
        print(f"✗ PDF parser failed: {e}")
        return False

    # Test 4: Text Preprocessor
    print("\n[4/4] Testing Text Preprocessor...")
    try:
        preprocessor = TextPreprocessor()
        sample_text = "This is a test. It has multiple sentences."
        chunks = preprocessor.chunk_text(sample_text, chunk_size=10)
        normalized = preprocessor.normalize_text(sample_text)
        assert len(chunks) > 0
        assert len(normalized) > 0
        print("✓ Text preprocessor working")
    except Exception as e:
        print(f"✗ Text preprocessor failed: {e}")
        return False

    # All tests passed
    print("\n" + "="*70)
    print("✓ PHASE 2 COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Download more papers: python scripts/download_papers.py")
    print("  2. Process PDFs: python scripts/process_pdfs.py")
    print("  3. Proceed to Phase 3: Database Design")
    print()

    return True


if __name__ == "__main__":
    verify_phase2()
