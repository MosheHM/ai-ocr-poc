"""Script to split a PDF into separate documents by type."""
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

from modules import split_and_extract_documents


def main():
    """Main entry point for document splitting."""
    parser = argparse.ArgumentParser(
        description='Split a PDF into separate documents by type'
    )
    parser.add_argument(
        'pdf_path',
        help='Path to the PDF file to split'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: samples/split_output)',
        default=None
    )
    parser.add_argument(
        '--model',
        help='Gemini model to use (default: gemini-2.5-flash)',
        default='gemini-2.5-flash'
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(__file__).parent / 'split_output'

    if not os.getenv('GEMINI_API_KEY'):
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    print(f"Processing: {pdf_path}")
    print(f"Output to: {output_dir}")
    print()

    result = split_and_extract_documents(
        str(pdf_path),
        str(output_dir),
        model=args.model
    )

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total documents found: {result['total_documents']}")
    print()

    for doc in result['documents']:
        doc_type = doc.get('DOC_TYPE', 'UNKNOWN')
        start = doc.get('START_PAGE_NO', '?')
        end = doc.get('END_PAGE_NO', '?')
        filename = doc.get('FILE_NAME', 'unknown')

        print(f"  {doc_type} (pages {start}-{end})")
        print(f"    -> {filename}")
 
        if doc_type == 'INVOICE':
            if 'INVOICE_NO' in doc:
                print(f"       Invoice #: {doc['INVOICE_NO']}")
            if 'INVOICE_AMOUNT' in doc:
                print(f"       Amount: {doc['INVOICE_AMOUNT']}")
        elif doc_type in ['OBL', 'HAWB', 'PACKING_LIST']:
            if 'CUSTOMER_NAME' in doc:
                print(f"       Customer: {doc['CUSTOMER_NAME']}")
        print()

    results_file = output_dir / f"{pdf_path.stem}_extraction_results.json"
    print(f"Full results saved to: {results_file}")


if __name__ == "__main__":
    main()
