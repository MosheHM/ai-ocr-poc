"""PDF utility functions."""
from typing import List
import io
import logging
from pypdf import PdfReader, PdfWriter


logger = logging.getLogger(__name__)


def combine_pdf_pages(pdf_path: str, page_numbers: List[int]) -> bytes:
    """Combine multiple pages from a PDF into a single PDF.

    Args:
        pdf_path: Path to the PDF file
        page_numbers: List of page numbers to combine (1-indexed)

    Returns:
        Bytes of the combined PDF
    """
    if PdfReader is None or PdfWriter is None:
        with open(pdf_path, 'rb') as f:
            return f.read()

    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page_num in page_numbers:
            # Convert to 0-indexed
            page_index = page_num - 1
            if 0 <= page_index < len(reader.pages):
                writer.add_page(reader.pages[page_index])

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return output.read()

    except Exception as e:
        logger.warning(f"Could not combine PDF pages: {e}")
        with open(pdf_path, 'rb') as f:
            return f.read()


def extract_pdf_pages(pdf_path: str, start_page: int, end_page: int) -> bytes:
    """Extract a range of pages from a PDF into a new PDF.

    Args:
        pdf_path: Path to the PDF file
        start_page: Start page number (1-indexed)
        end_page: End page number (1-indexed, inclusive)

    Returns:
        Bytes of the extracted PDF
    """
    page_numbers = list(range(start_page, end_page + 1))
    return combine_pdf_pages(pdf_path, page_numbers)

