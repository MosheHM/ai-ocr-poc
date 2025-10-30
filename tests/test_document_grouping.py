"""Tests for document grouping functionality."""
import pytest
from modules.types import DocumentType, PageClassification
from modules.utils import group_pages_into_documents


class TestDocumentGrouping:
    """Tests for grouping pages into document instances."""
    
    def test_group_single_type(self):
        """Test grouping when all pages are the same type."""
        classifications = [
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
            PageClassification(page_number=2, document_type=DocumentType.INVOICE, confidence=0.93),
            PageClassification(page_number=3, document_type=DocumentType.INVOICE, confidence=0.97),
        ]
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 1
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].start_page == 1
        assert documents[0].end_page == 3
        assert documents[0].page_numbers == [1, 2, 3]
        assert documents[0].page_range == "1-3"
    
    def test_group_multiple_types(self):
        """Test grouping when pages have different types."""
        classifications = [
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
            PageClassification(page_number=2, document_type=DocumentType.INVOICE, confidence=0.93),
            PageClassification(page_number=3, document_type=DocumentType.PACKING_LIST, confidence=0.97),
            PageClassification(page_number=4, document_type=DocumentType.PACKING_LIST, confidence=0.96),
            PageClassification(page_number=5, document_type=DocumentType.PACKING_LIST, confidence=0.94),
        ]
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 2
        
        # First document: Invoice (pages 1-2)
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].start_page == 1
        assert documents[0].end_page == 2
        assert documents[0].page_numbers == [1, 2]
        assert documents[0].page_range == "1-2"
        
        # Second document: Packing List (pages 3-5)
        assert documents[1].document_type == DocumentType.PACKING_LIST
        assert documents[1].start_page == 3
        assert documents[1].end_page == 5
        assert documents[1].page_numbers == [3, 4, 5]
        assert documents[1].page_range == "3-5"
    
    def test_group_alternating_types(self):
        """Test grouping when types alternate."""
        classifications = [
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
            PageClassification(page_number=2, document_type=DocumentType.OBL, confidence=0.93),
            PageClassification(page_number=3, document_type=DocumentType.INVOICE, confidence=0.97),
        ]
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 3
        
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].page_numbers == [1]
        assert documents[0].page_range == "1"
        
        assert documents[1].document_type == DocumentType.OBL
        assert documents[1].page_numbers == [2]
        
        assert documents[2].document_type == DocumentType.INVOICE
        assert documents[2].page_numbers == [3]
    
    def test_group_single_page(self):
        """Test grouping with a single page."""
        classifications = [
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
        ]
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 1
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].start_page == 1
        assert documents[0].end_page == 1
        assert documents[0].page_numbers == [1]
        assert documents[0].page_range == "1"
    
    def test_group_empty_list(self):
        """Test grouping with empty list."""
        classifications = []
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 0
    
    def test_group_with_unknown_types(self):
        """Test grouping with unknown document types."""
        classifications = [
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
            PageClassification(page_number=2, document_type=DocumentType.UNKNOWN, confidence=0.5),
            PageClassification(page_number=3, document_type=DocumentType.UNKNOWN, confidence=0.4),
            PageClassification(page_number=4, document_type=DocumentType.PACKING_LIST, confidence=0.96),
        ]
        
        documents = group_pages_into_documents(classifications)
        
        assert len(documents) == 3
        
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].page_numbers == [1]
        
        # Unknown pages grouped together
        assert documents[1].document_type == DocumentType.UNKNOWN
        assert documents[1].page_numbers == [2, 3]
        assert documents[1].page_range == "2-3"
        
        assert documents[2].document_type == DocumentType.PACKING_LIST
        assert documents[2].page_numbers == [4]
