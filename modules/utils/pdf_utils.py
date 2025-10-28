"""PDF utility functions."""
from typing import List
import io
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        # Fallback: will handle in code
        PdfReader = None
        PdfWriter = None


def split_pdf_to_pages(pdf_path: str) -> List[bytes]:
    """Split a PDF file into individual page bytes.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of bytes, each containing a single page PDF
    """
    if PdfReader is None or PdfWriter is None:
        # If PDF libraries not available, return single page
        # This allows the code to work with single-page PDFs
        with open(pdf_path, 'rb') as f:
            return [f.read()]
    
    pages = []
    
    try:
        # Read the PDF
        reader = PdfReader(pdf_path)
        
        # Extract each page as a separate PDF
        for page_num in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            
            # Write to bytes
            page_bytes = io.BytesIO()
            writer.write(page_bytes)
            page_bytes.seek(0)
            
            pages.append(page_bytes.read())
        
        return pages
        
    except Exception as e:
        # Fallback: if splitting fails, return whole PDF as single page
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
