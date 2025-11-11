"""
PubMed Central API Client

This module provides a client for searching and retrieving papers from
PubMed Central for biomedical research.
"""

from Bio import Entrez
import time
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedClient:
    """
    Client for interacting with PubMed Central API.

    Attributes:
        email (str): Email required by NCBI
        api_key (str): Optional API key for higher rate limits
    """

    def __init__(self, email: str, api_key: Optional[str] = None):
        """
        Initialize PubMed client.

        Args:
            email: Your email (required by NCBI)
            api_key: Optional API key from NCBI
        """
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key

        self.max_retries = 3
        self.delay = 0.5  # Delay between requests

        logger.info(f"PubMedClient initialized with email={email}")

    def search_papers(
            self,
            query: str,
            max_results: int = 100,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None
    ) -> List[str]:
        """
        Search PubMed Central for papers.

        Args:
            query: Search query
            max_results: Maximum number of results
            date_from: Start date (YYYY/MM/DD)
            date_to: End date (YYYY/MM/DD)

        Returns:
            List of PubMed IDs
        """
        # Build date filter
        if date_from and date_to:
            query = f"{query} AND {date_from}:{date_to}[pdat]"

        logger.info(f"Searching PubMed with query: {query}")

        for attempt in range(self.max_retries):
            try:
                handle = Entrez.esearch(
                    db="pmc",
                    term=query,
                    retmax=max_results,
                    sort="relevance"
                )
                results = Entrez.read(handle)
                handle.close()

                pmid_list = results["IdList"]
                logger.info(f"Found {len(pmid_list)} papers")

                return pmid_list

            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{self.max_retries}")
                else:
                    logger.error(f"Error searching PubMed: {e}")
                    raise

    def fetch_paper_metadata(self, pmid_list: List[str]) -> List[Dict]:
        """
        Fetch detailed metadata for PubMed IDs.

        Args:
            pmid_list: List of PubMed IDs

        Returns:
            List of paper metadata dictionaries
        """
        papers = []
        batch_size = 20

        for i in range(0, len(pmid_list), batch_size):
            batch = pmid_list[i:i + batch_size]
            ids = ",".join(batch)

            try:
                handle = Entrez.efetch(
                    db="pmc",
                    id=ids,
                    rettype="xml",
                    retmode="xml"
                )
                records = Entrez.read(handle)
                handle.close()

                for record in records:
                    paper_data = self._parse_record(record)
                    papers.append(paper_data)

                time.sleep(self.delay)

            except Exception as e:
                logger.error(f"Error fetching batch: {e}")

        logger.info(f"Fetched metadata for {len(papers)} papers")
        return papers

    def _parse_record(self, record: Dict) -> Dict:
        """Parse PubMed record into dictionary"""
        return {
            'pmid': record.get('PMID', ''),
            'title': record.get('ArticleTitle', ''),
            'authors': self._extract_authors(record),
            'abstract': record.get('Abstract', ''),
            'journal': record.get('Journal', ''),
            'pub_date': record.get('PubDate', '')
        }

    def _extract_authors(self, record: Dict) -> List[str]:
        """Extract author names from record"""
        authors = []
        author_list = record.get('AuthorList', [])

        for author in author_list:
            first_name = author.get('ForeName', '')
            last_name = author.get('LastName', '')
            name = f"{first_name} {last_name}".strip()
            if name:
                authors.append(name)

        return authors


# Example usage
if __name__ == "__main__":
    # Note: Replace with your email
    client = PubMedClient(email="your_email@example.com")

    # Search for papers
    pmids = client.search_papers("CRISPR gene editing", max_results=5)

    # Fetch metadata
    if pmids:
        papers = client.fetch_paper_metadata(pmids)

        for idx, paper in enumerate(papers, 1):
            print(f"\n{idx}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:3])}")
