"""Tests for PDF utility functions."""
import pytest
import io
from pathlib import Path
from pypdf import PdfReader

from modules.utils.pdf_utils import combine_pdf_pages, extract_pdf_pages


@pytest.mark.unit
class TestCombinePdfPages:
    """Tests for combine_pdf_pages function."""

    def test_combine_single_page(self, sample_pdf_file):
        """Test combining a single page."""
        result = combine_pdf_pages(str(sample_pdf_file), [1])
        
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify it's a valid PDF
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_combine_multiple_pages(self, multi_page_pdf_file):
        """Test combining multiple pages."""
        result = combine_pdf_pages(str(multi_page_pdf_file), [1, 3, 5])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3

    def test_combine_all_pages(self, multi_page_pdf_file):
        """Test combining all pages from a PDF."""
        result = combine_pdf_pages(str(multi_page_pdf_file), [1, 2, 3, 4, 5])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 5

    def test_combine_pages_out_of_order(self, multi_page_pdf_file):
        """Test combining pages in non-sequential order."""
        result = combine_pdf_pages(str(multi_page_pdf_file), [5, 2, 4, 1, 3])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 5

    def test_combine_skips_invalid_page_numbers(self, multi_page_pdf_file):
        """Test that invalid page numbers are skipped."""
        # Multi-page fixture has 5 pages, requesting pages 1, 100 should only get page 1
        result = combine_pdf_pages(str(multi_page_pdf_file), [1, 100])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_combine_handles_page_zero(self, multi_page_pdf_file):
        """Test that page 0 (invalid in 1-indexed) is skipped."""
        result = combine_pdf_pages(str(multi_page_pdf_file), [0, 1, 2])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2  # Only pages 1 and 2

    def test_combine_negative_pages_skipped(self, multi_page_pdf_file):
        """Test that negative page numbers are skipped."""
        result = combine_pdf_pages(str(multi_page_pdf_file), [-1, 1])
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_combine_empty_list_returns_empty_pdf(self, sample_pdf_file):
        """Test combining with empty page list returns a PDF with no pages."""
        result = combine_pdf_pages(str(sample_pdf_file), [])
        
        # Should still be valid PDF bytes, but with no pages
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 0


@pytest.mark.unit
class TestExtractPdfPages:
    """Tests for extract_pdf_pages function."""

    def test_extract_single_page(self, multi_page_pdf_file):
        """Test extracting a single page."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 3, 3)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_extract_page_range(self, multi_page_pdf_file):
        """Test extracting a range of pages."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 2, 4)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 3  # Pages 2, 3, 4

    def test_extract_first_pages(self, multi_page_pdf_file):
        """Test extracting first N pages."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 1, 2)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2

    def test_extract_last_pages(self, multi_page_pdf_file):
        """Test extracting last pages."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 4, 5)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 2

    def test_extract_all_pages(self, multi_page_pdf_file):
        """Test extracting all pages."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 1, 5)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 5

    def test_extract_from_single_page_pdf(self, sample_pdf_file):
        """Test extracting from a single-page PDF."""
        result = extract_pdf_pages(str(sample_pdf_file), 1, 1)
        
        reader = PdfReader(io.BytesIO(result))
        assert len(reader.pages) == 1

    def test_extract_creates_valid_pdf(self, multi_page_pdf_file):
        """Test that extracted PDF is valid and readable."""
        result = extract_pdf_pages(str(multi_page_pdf_file), 2, 3)
        
        # Should be able to write and read back
        output = io.BytesIO(result)
        reader = PdfReader(output)
        
        assert reader is not None
        assert len(reader.pages) == 2
