"""
Batch process PDFs to extract and clean text

Usage:
    python scripts/process_pdfs.py --input data/pdfs --output data/extracted_text
    python scripts/process_pdfs.py --input data/pdfs --clean --sections
"""

import sys

sys.path.append('.')

from processing.pdf_parser import PDFParser
from pathlib import Path
import argparse
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_pdf(
        pdf_path: Path,
        output_dir: Path,
        clean: bool = True,
        extract_sections: bool = False
) -> dict:
    """
    Process a single PDF file.

    Returns:
        Processing result dictionary
    """
    try:
        logger.info(f"Processing: {pdf_path.name}")

        # Create parser
        parser = PDFParser(str(pdf_path))

        # Extract text
        text = parser.extract_text()

        # Clean if requested
        if clean:
            text = parser.clean_text()

        # Extract sections if requested
        sections = {}
        if extract_sections:
            sections = parser.extract_sections()

        # Save text
        output_file = output_dir / f"{pdf_path.stem}.txt"
        parser.save_text(str(output_file))

        # Get statistics
        stats = parser.get_statistics()

        # Save sections if extracted
        if sections:
            sections_file = output_dir / f"{pdf_path.stem}_sections.json"
            with open(sections_file, 'w') as f:
                json.dump(sections, f, indent=2)

        return {
            'pdf': pdf_path.name,
            'status': 'success',
            'output_file': str(output_file),
            'statistics': stats,
            'sections_found': len(sections)
        }

    except Exception as e:
        logger.error(f"Error processing {pdf_path.name}: {e}")
        return {
            'pdf': pdf_path.name,
            'status': 'failed',
            'error': str(e)
        }


def main():
    """Main processing function"""
    parser = argparse.ArgumentParser(description='Batch process PDF files')

    parser.add_argument('--input', type=str, required=True, help='Input directory with PDFs')
    parser.add_argument('--output', type=str, required=True, help='Output directory for text')
    parser.add_argument('--clean', action='store_true', help='Clean extracted text')
    parser.add_argument('--sections', action='store_true', help='Extract sections')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--save-report', action='store_true', help='Save processing report')

    args = parser.parse_args()

    # Setup paths
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDFs
    pdf_files = list(input_dir.glob('*.pdf'))

    if not pdf_files:
        logger.error(f"No PDF files found in {input_dir}")
        return

    # Limit files if specified
    if args.max_files:
        pdf_files = pdf_files[:args.max_files]

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Process all PDFs
    results = []
    for pdf_path in pdf_files:
        result = process_single_pdf(
            pdf_path,
            output_dir,
            clean=args.clean,
            extract_sections=args.sections
        )
        results.append(result)

    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful

    logger.info(f"\nProcessing complete:")
    logger.info(f"  Successful: {successful}")
    logger.info(f"  Failed: {failed}")

    # Save report if requested
    if args.save_report:
        report_file = output_dir / 'processing_report.json'
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"  Report saved to: {report_file}")


if __name__ == "__main__":
    main()
