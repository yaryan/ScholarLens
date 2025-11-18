"""
Test script for PDF parser

Run with: python tests/test_pdf_parser.py
"""

import sys

sys.path.append('.')

from processing.pdf_parser import PDFParser
from pathlib import Path


def test_pdf_parsing():
    """Test PDF parsing functionality"""
    print("Test: PDF Parsing")
    print("-" * 50)

    # Find a PDF
    pdf_dir = Path('./data/pdfs')
    pdf_files = list(pdf_dir.glob('*.pdf'))

    if not pdf_files:
        print("✗ No PDFs found. Download papers first.")
        return False

    pdf_path = pdf_files[0]
    print(f"Testing with: {pdf_path.name}\n")

    # Create parser
    parser = PDFParser(str(pdf_path))

    # Extract text
    text = parser.extract_text()
    assert len(text) > 0, "No text extracted"
    print(f"✓ Extracted {len(text)} characters")

    # Clean text
    cleaned = parser.clean_text()
    print(f"✓ Cleaned text: {len(cleaned)} characters")

    # Extract sections
    sections = parser.extract_sections()
    print(f"✓ Found {len(sections)} sections")

    # Get stats
    stats = parser.get_statistics()
    print(f"✓ Statistics: {stats['total_words']} words, {stats['total_pages']} pages")

    print("\n✓ Test passed\n")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING PDF PARSER")
    print("=" * 70 + "\n")

    try:
        test_pdf_parsing()

        print("=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
