"""
Batch download papers from arXiv

Usage:
    python scripts/download_papers.py --query "machine learning" --num 20
    python scripts/download_papers.py --category cs.AI --num 50
    python scripts/download_papers.py --ids 1706.03762 2103.14030
"""

import sys

sys.path.append('.')

from data_sources.arxiv_client import ArxivClient
import argparse
import json
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main download function"""
    parser = argparse.ArgumentParser(description='Download papers from arXiv')

    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--category', type=str, help='arXiv category (e.g., cs.AI)')
    parser.add_argument('--num', type=int, default=10, help='Number of papers to download')
    parser.add_argument('--ids', nargs='+', help='Specific arXiv IDs to download')
    parser.add_argument('--output-dir', type=str, default='./data/pdfs', help='Output directory')
    parser.add_argument('--save-metadata', action='store_true', help='Save metadata JSON')

    args = parser.parse_args()

    # Initialize client
    client = ArxivClient(download_dir=args.output_dir)

    papers = []

    # Download specific IDs
    if args.ids:
        logger.info(f"Fetching {len(args.ids)} specific papers...")
        for arxiv_id in args.ids:
            paper = client.get_paper_by_id(arxiv_id)
            if paper:
                papers.append(paper)

    # Search by query or category
    elif args.query or args.category:
        logger.info(f"Searching for papers...")
        papers = client.search_papers(
            query=args.query or "",
            category=args.category,
            max_results=args.num
        )

    else:
        logger.error("Must provide --query, --category, or --ids")
        return

    if not papers:
        logger.warning("No papers found")
        return

    # Download papers
    logger.info(f"Starting download of {len(papers)} papers...")
    papers_with_paths = client.batch_download(papers)

    # Save metadata if requested
    if args.save_metadata:
        metadata_path = Path(args.output_dir) / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(papers_with_paths, f, indent=2)
        logger.info(f"Saved metadata to: {metadata_path}")

    # Summary
    successful = sum(1 for p in papers_with_paths if p.get('download_status') == 'success')
    logger.info(f"Download complete: {successful}/{len(papers)} successful")


if __name__ == "__main__":
    main()
