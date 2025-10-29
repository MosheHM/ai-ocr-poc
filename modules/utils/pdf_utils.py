"""PDF utility functions."""
from typing import List
import io
from pypdf import PdfReader, PdfWriter



def split_pdf_to_pages(pdf_path: str) -> List[bytes]:
    """Split a PDF file into individual page bytes.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of bytes, each containing a single page PDF
    """
    if PdfReader is None or PdfWriter is None:

        with open(pdf_path, 'rb') as f:
            return [f.read()]
    
    pages = []
    
    try:
        reader = PdfReader(pdf_path)
        
        for page_num in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            
            page_bytes = io.BytesIO()
            writer.write(page_bytes)
            page_bytes.seek(0)
            
            pages.append(page_bytes.read())
        
        return pages
        
    except Exception as e:
        print(f"Warning: Could not split PDF into pages: {e}")
        with open(pdf_path, 'rb') as f:
            return [f.read()]


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Number of pages
    """
    if PdfReader is None:
        return 1
    
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        return 1
