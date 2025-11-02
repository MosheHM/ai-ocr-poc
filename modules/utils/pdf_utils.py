"""PDF utility functions."""
from typing import List, Optional, Dict, Any
import io
import json
import logging
from pathlib import Path
from pypdf import PdfReader, PdfWriter


logger = logging.getLogger(__name__)



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
        logger.warning(f"Could not split PDF into pages: {e}")
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


def find_ground_truth_txt(pdf_path: str) -> Optional[str]:
    """Find ground truth .txt file for a given PDF path.
    
    The .txt file should have the same base name as the PDF file.
    For example: invoice.PDF -> invoice.txt
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Path to the .txt file if it exists, None otherwise
    """
    pdf_file = Path(pdf_path)
    txt_file = pdf_file.with_suffix('.txt')
    
    if txt_file.exists():
        return str(txt_file)
    
    return None


def load_ground_truth_from_txt(txt_path: str) -> Optional[Dict[str, Any]]:
    """Load ground truth data from a .txt file (JSON format).
    
    The .txt file should contain JSON data, optionally wrapped in an 'OCC' object.
    
    Args:
        txt_path: Path to the .txt file
    
    Returns:
        Dictionary containing ground truth data, or None if file cannot be loaded
    """
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle OCC wrapper if present
        if 'OCC' in data:
            return data['OCC']
        
        return data
    
    except Exception as e:
        logger.warning(f"Could not load ground truth from {txt_path}: {e}")
        return None

