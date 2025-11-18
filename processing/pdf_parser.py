"""
PDF Parser for Research Papers

This module provides robust PDF parsing with multiple extraction methods,
text cleaning, and section identification.

Supports: pdfplumber, PyPDF2, and fallback mechanisms
"""

import pdfplumber
from PyPDF2 import PdfReader
import re
import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """
    Robust PDF parser for research papers.

    Features:
    - Multiple extraction methods (pdfplumber, PyPDF2)
    - Automatic fallback
    - Text cleaning and normalization
    - Section detection
    - Table extraction
    """

    def __init__(self, pdf_path: str):
        """
        Initialize PDF parser.

        Args:
            pdf_path: Path to PDF file

        Raises:
            FileNotFoundError: If PDF doesn't exist
        """
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self.text = ""
        self.metadata = {}
        self.tables = []
        self.sections = {}

        logger.info(f"PDFParser initialized for: {self.pdf_path.name}")

    def extract_with_pdfplumber(self) -> Optional[str]:
        """
        Extract text using pdfplumber (best for complex layouts).

        Returns:
            Extracted text or None if failed
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Extract metadata
                self.metadata = {
                    'pages': len(pdf.pages),
                    'creator': pdf.metadata.get('Creator', ''),
                    'producer': pdf.metadata.get('Producer', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'title': pdf.metadata.get('Title', '')
                }

                # Extract text from all pages
                full_text = []

                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()

                    if page_text:
                        full_text.append(f"--- Page {page_num} ---\n{page_text}")

                    # Extract tables if present
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            self.tables.append({
                                'page': page_num,
                                'data': table
                            })

                self.text = "\n\n".join(full_text)

                logger.info(f"✓ pdfplumber: Extracted {len(self.text)} characters")
                return self.text

        except Exception as e:
            logger.warning(f"✗ pdfplumber failed: {e}")
            return None

    def extract_with_pypdf2(self) -> Optional[str]:
        """
        Extract text using PyPDF2 (lightweight fallback).

        Returns:
            Extracted text or None if failed
        """
        try:
            reader = PdfReader(str(self.pdf_path))

            # Extract metadata
            self.metadata = {
                'pages': len(reader.pages),
                'author': reader.metadata.get('/Author', ''),
                'title': reader.metadata.get('/Title', ''),
                'subject': reader.metadata.get('/Subject', ''),
                'creator': reader.metadata.get('/Creator', '')
            }

            # Extract text from all pages
            full_text = []

            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()

                if page_text:
                    full_text.append(page_text)

            self.text = "\n\n".join(full_text)

            logger.info(f"✓ PyPDF2: Extracted {len(self.text)} characters")
            return self.text

        except Exception as e:
            logger.warning(f"✗ PyPDF2 failed: {e}")
            return None

    def extract_text(self, preferred_method: str = 'pdfplumber') -> str:
        """
        Extract text with automatic fallback.

        Args:
            preferred_method: 'pdfplumber' or 'pypdf2'

        Returns:
            Extracted text

        Raises:
            Exception: If all methods fail
        """
        logger.info(f"Attempting extraction with {preferred_method}")

        # Try preferred method first
        if preferred_method == 'pdfplumber':
            text = self.extract_with_pdfplumber()
            if not text:
                logger.info("Falling back to PyPDF2...")
                text = self.extract_with_pypdf2()
        else:
            text = self.extract_with_pypdf2()
            if not text:
                logger.info("Falling back to pdfplumber...")
                text = self.extract_with_pdfplumber()

        if not text:
            raise Exception("All extraction methods failed")

        self.text = text
        return self.text

    def clean_text(self) -> str:
        """
        Clean extracted text by removing noise.

        Removes:
        - Excessive whitespace
        - Page numbers
        - Common headers/footers
        - arXiv identifiers

        Returns:
            Cleaned text
        """
        if not self.text:
            logger.warning("No text to clean")
            return ""

        text = self.text

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove isolated page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        # Remove arXiv identifiers
        text = re.sub(r'arXiv:\d+\.\d+v\d+', '', text, flags=re.IGNORECASE)

        # Remove common footer patterns
        text = re.sub(r'Preprint\.', '', text, flags=re.IGNORECASE)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Normalize line breaks (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace
        text = text.strip()

        self.text = text

        logger.info(f"✓ Cleaned text: {len(text)} characters")
        return self.text

    def extract_sections(self) -> Dict[str, str]:
        """
        Identify and extract major sections from the paper.

        Sections detected:
        - Abstract
        - Introduction
        - Related Work
        - Methodology/Methods
        - Results
        - Discussion
        - Conclusion
        - References

        Returns:
            Dictionary mapping section names to text
        """
        if not self.text:
            logger.warning("No text to extract sections from")
            return {}

        sections = {}
        text = self.text

        # Section patterns (ordered by typical appearance)
        section_patterns = [
            (r'\bAbstract\b', 'abstract'),
            (r'\b(?:1\.?\s*)?Introduction\b', 'introduction'),
            (r'\bRelated Work\b', 'related_work'),
            (r'\b(?:Methodology|Methods)\b', 'methods'),
            (r'\bExperiments?\b', 'experiments'),
            (r'\bResults?\b', 'results'),
            (r'\bDiscussion\b', 'discussion'),
            (r'\bConclusion\b', 'conclusion'),
            (r'\bReferences?\b', 'references')
        ]

        # Find all section markers
        section_markers = []
        for pattern, name in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                section_markers.append({
                    'name': name,
                    'start': match.start(),
                    'pattern': pattern
                })

        # Sort by position
        section_markers.sort(key=lambda x: x['start'])

        # Extract sections
        for i, marker in enumerate(section_markers):
            start = marker['start']

            # Find end (start of next section or end of text)
            if i < len(section_markers) - 1:
                end = section_markers[i + 1]['start']
            else:
                end = len(text)

            section_text = text[start:end].strip()
            sections[marker['name']] = section_text

        self.sections = sections

        logger.info(f"✓ Found {len(sections)} sections: {list(sections.keys())}")
        return sections

    def get_abstract(self) -> Optional[str]:
        """
        Extract just the abstract section.

        Returns:
            Abstract text or None
        """
        if not self.sections:
            self.extract_sections()

        return self.sections.get('abstract')

    def get_statistics(self) -> Dict:
        """
        Get statistics about the extracted text.

        Returns:
            Dictionary with text statistics
        """
        if not self.text:
            return {}

        words = self.text.split()

        return {
            'total_characters': len(self.text),
            'total_words': len(words),
            'total_pages': self.metadata.get('pages', 0),
            'sections_found': len(self.sections),
            'tables_found': len(self.tables),
            'avg_words_per_page': len(words) / max(self.metadata.get('pages', 1), 1)
        }

    def save_text(self, output_path: str) -> None:
        """
        Save extracted text to file.

        Args:
            output_path: Path to output text file
        """
        if not self.text:
            logger.warning("No text to save")
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.text)

        logger.info(f"✓ Saved text to: {output_path}")


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PDF PARSER DEMONSTRATION")
    print("=" * 70)

    # Find a PDF in the data/pdfs directory
    pdf_dir = Path('./data/pdfs')
    pdf_files = list(pdf_dir.glob('*.pdf'))

    if not pdf_files:
        print("\n✗ No PDF files found in ./data/pdfs/")
        print("  Please run the arXiv client first to download some papers.")
    else:
        # Parse the first PDF
        pdf_path = pdf_files[0]
        print(f"\nParsing: {pdf_path.name}\n")

        # Create parser
        parser = PDFParser(str(pdf_path))

        # Extract text
        text = parser.extract_text()

        # Clean text
        cleaned = parser.clean_text()

        # Extract sections
        sections = parser.extract_sections()

        # Get statistics
        stats = parser.get_statistics()

        # Display results
        print("\n" + "-" * 70)
        print("EXTRACTION RESULTS")
        print("-" * 70)

        print(f"\nMetadata:")
        for key, value in parser.metadata.items():
            print(f"  {key}: {value}")

        print(f"\nStatistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        print(f"\nSections found: {', '.join(sections.keys())}")

        # Show first 500 characters
        print(f"\nFirst 500 characters:")
        print("-" * 70)
        print(cleaned[:500] + "...")

        # Save to file
        output_path = f"./data/extracted_text/{pdf_path.stem}.txt"
        parser.save_text(output_path)

        print("\n" + "=" * 70)
        print("✓ PARSING COMPLETE")
        print("=" * 70)
