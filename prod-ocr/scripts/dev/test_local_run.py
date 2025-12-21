#!/usr/bin/env python3
"""Test script to run document splitter locally."""
import os
from pathlib import Path
from dotenv import load_dotenv
from modules.document_splitter import split_and_extract_documents

# Load environment variables from .env file
load_dotenv()

def main():
    # Find a sample PDF
    sample_dir = Path("../samples/combined-sampels")
    pdf_files = list(sample_dir.glob("*.PDF")) + list(sample_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in samples directory")
        return
    # Use the first PDF file
    pdf_path = Path("../samples/combined-sampels/84526616_ORG_arzlhvywte2zczalgoitew00000000.PDF")
    print(f"Processing: {pdf_path.name}")
    print(f"File size: {pdf_path.stat().st_size / 1024:.2f} KB\n")

    # Create output directory
    output_dir = Path("split_output")
    output_dir.mkdir(exist_ok=True)

    print("Starting document splitting and extraction...")
    print("-" * 50)

    try:
        # Process the PDF
        result = split_and_extract_documents(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir)
        )

        print("\n✓ Processing completed successfully!")
        print(f"\nFound {result['total_documents']} document(s):\n")

        for i, doc in enumerate(result['documents'], 1):
            doc_type = doc.get('DOC_TYPE', 'UNKNOWN')
            confidence = doc.get('DOC_TYPE_CONFIDENCE', 0)
            pages = doc.get('TOTAL_PAGES', 0)
            file_name = doc.get('FILE_NAME', 'N/A')
            pages_info = doc.get('PAGES_INFO', [])

            print(f"{i}. {doc_type}")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Pages: {pages}")
            print(f"   File: {file_name}")
            if pages_info:
                rotations = ", ".join([f"p{p['PAGE_NO']}:{p['ROTATION']}°" for p in pages_info])
                print(f"   Page Rotations: {rotations}")
            print()

        print(f"Output directory: {output_dir.absolute()}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
