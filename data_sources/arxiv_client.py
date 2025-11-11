"""
arXiv API Client for Research Knowledge Navigator

This module provides a client for interacting with the arXiv API to search,
download, and manage research papers.

Author: Research Knowledge Navigator Team
Date: October 2025
"""

import arxiv
import feedparser
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArxivClient:
    """
    Client for interacting with arXiv API.

    Attributes:
        max_results (int): Maximum number of results per query
        download_dir (str): Directory for storing downloaded PDFs
        client (arxiv.Client): arXiv API client instance
    """

    def __init__(self, max_results: int = 100, download_dir: str = './data/pdfs'):
        """
        Initialize arXiv client.

        Args:
            max_results: Maximum number of results to fetch
            download_dir: Directory to store downloaded PDFs
        """
        self.max_results = max_results
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Create client with retry logic
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,  # Be nice to the API
            num_retries=3
        )

        logger.info(f"ArxivClient initialized with max_results={max_results}")

    def search_papers(
            self,
            query: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            category: Optional[str] = None,
            max_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search arXiv papers with flexible query options.

        Args:
            query: Search query string (e.g., "deep learning")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            category: arXiv category (e.g., "cs.AI", "cs.LG")
            max_results: Override default max_results

        Returns:
            List of paper metadata dictionaries

        Example:
            >>> client = ArxivClient()
            >>> papers = client.search_papers(
            ...     query="attention mechanism",
            ...     category="cs.CL",
            ...     start_date="2024-01-01",
            ...     max_results=50
            ... )
        """
        # Build query string
        query_parts = []

        # Add main search query
        if query:
            query_parts.append(f"all:{query}")

        # Add category filter
        if category:
            query_parts.append(f"cat:{category}")

        # Add date range (note: arXiv date filtering is limited)
        if start_date and end_date:
            # Convert to arXiv date format (YYYYMMDD)
            start = start_date.replace('-', '')
            end = end_date.replace('-', '')
            query_parts.append(f"submittedDate:[{start} TO {end}]")

        # Combine query parts
        full_query = " AND ".join(query_parts) if query_parts else "all:*"

        logger.info(f"Searching arXiv with query: {full_query}")

        # Create search object
        search = arxiv.Search(
            query=full_query,
            max_results=max_results or self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        # Fetch results
        papers = []
        try:
            for result in self.client.results(search):
                paper_data = self._parse_result(result)
                papers.append(paper_data)

            logger.info(f"Found {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            raise

    def _parse_result(self, result: arxiv.Result) -> Dict:
        """
        Parse arXiv result object into dictionary.

        Args:
            result: arxiv.Result object

        Returns:
            Dictionary with paper metadata
        """
        return {
            'arxiv_id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': [author.name for author in result.authors],
            'abstract': result.summary,
            'published': result.published.strftime('%Y-%m-%d'),
            'updated': result.updated.strftime('%Y-%m-%d'),
            'categories': result.categories,
            'primary_category': result.primary_category,
            'pdf_url': result.pdf_url,
            'doi': result.doi,
            'journal_ref': result.journal_ref,
            'comment': result.comment
        }

    def download_paper(
            self,
            paper: Dict,
            filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Download PDF for a given paper.

        Args:
            paper: Paper metadata dictionary
            filename: Custom filename (optional)

        Returns:
            Path to downloaded PDF or None if failed
        """
        arxiv_id = paper['arxiv_id']

        # Generate filename
        if filename is None:
            safe_id = arxiv_id.replace('/', '_').replace(':', '_')
            filename = f"{safe_id}.pdf"

        filepath = self.download_dir / filename

        # Skip if already downloaded
        if filepath.exists():
            logger.info(f"PDF already exists: {filename}")
            return str(filepath)

        try:
            # Create search with specific ID
            search = arxiv.Search(id_list=[arxiv_id])
            paper_obj = next(self.client.results(search))

            # Download PDF
            paper_obj.download_pdf(filename=str(filepath))

            logger.info(f"Downloaded: {filename}")
            time.sleep(3)  # Be nice to the server

            return str(filepath)

        except Exception as e:
            logger.error(f"Error downloading {arxiv_id}: {e}")
            return None

    def batch_download(
            self,
            papers: List[Dict],
            max_downloads: Optional[int] = None
    ) -> List[Dict]:
        """
        Download multiple papers with progress tracking.

        Args:
            papers: List of paper metadata dictionaries
            max_downloads: Maximum number of papers to download

        Returns:
            List of papers with download status
        """
        if max_downloads:
            papers = papers[:max_downloads]

        total = len(papers)
        successful = 0
        failed = 0

        logger.info(f"Starting batch download of {total} papers")

        for idx, paper in enumerate(papers, 1):
            logger.info(f"Downloading {idx}/{total}: {paper['title'][:50]}...")

            filepath = self.download_paper(paper)

            if filepath:
                paper['pdf_path'] = filepath
                paper['download_status'] = 'success'
                successful += 1
            else:
                paper['pdf_path'] = None
                paper['download_status'] = 'failed'
                failed += 1

        logger.info(f"Batch download complete: {successful} successful, {failed} failed")

        return papers

    def search_by_category(
            self,
            category: str,
            num_papers: int = 50,
            date_range_days: int = 30
    ) -> List[Dict]:
        """
        Search recent papers in a specific category.

        Args:
            category: arXiv category (e.g., "cs.AI", "cs.CL", "cs.LG")
            num_papers: Number of papers to fetch
            date_range_days: How many days back to search

        Returns:
            List of paper metadata
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)

        return self.search_papers(
            query="",
            category=category,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            max_results=num_papers
        )

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch a specific paper by arXiv ID.

        Args:
            arxiv_id: arXiv identifier (e.g., "2103.15348")

        Returns:
            Paper metadata dictionary or None
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            return self._parse_result(result)
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    # Initialize client
    client = ArxivClient(max_results=10)

    # Example 1: Search by keyword
    print("\n" + "=" * 70)
    print("Example 1: Searching for papers on 'transformer neural networks'")
    print("=" * 70)

    papers = client.search_papers(
        query="transformer neural networks",
        category="cs.LG",
        max_results=5
    )

    for idx, paper in enumerate(papers, 1):
        print(f"\n{idx}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'][:3])}")
        print(f"   Published: {paper['published']}")
        print(f"   arXiv ID: {paper['arxiv_id']}")

    # Example 2: Download a single paper
    if papers:
        print("\n" + "=" * 70)
        print("Example 2: Downloading first paper")
        print("=" * 70)

        first_paper = papers[0]
        filepath = client.download_paper(first_paper)

        if filepath:
            print(f"✓ Successfully downloaded to: {filepath}")
        else:
            print("✗ Download failed")

    # Example 3: Get paper by specific ID
    print("\n" + "=" * 70)
    print("Example 3: Fetching specific paper (Attention Is All You Need)")
    print("=" * 70)

    specific_paper = client.get_paper_by_id("1706.03762")
    if specific_paper:
        print(f"Title: {specific_paper['title']}")
        print(f"Authors: {', '.join(specific_paper['authors'])}")
        print(f"Published: {specific_paper['published']}")
