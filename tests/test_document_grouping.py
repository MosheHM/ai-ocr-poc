"""Tests for document grouping functionality."""
import pytest
from modules.types import DocumentType, PageClassification, ProcessingResult, DocumentInstance
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


class TestDocumentSummary:
    """Tests for document summary in ProcessingResult."""
    
    def test_processing_result_with_document_instances(self):
        """Test that ProcessingResult properly stores document instances."""
        # Create sample document instances - scenario from problem statement
        # One PDF with 10 pages: 3 invoices and 2 packing lists
        # Invoice 1: pages 1-3
        # Invoice 2: page 4
        # Invoice 3: pages 5-6
        # PL 1: pages 7-9
        # PL 2: page 10
        
        doc_instances = [
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=1,
                end_page=3,
                page_numbers=[1, 2, 3]
            ),
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=4,
                end_page=4,
                page_numbers=[4]
            ),
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=5,
                end_page=6,
                page_numbers=[5, 6]
            ),
            DocumentInstance(
                document_type=DocumentType.PACKING_LIST,
                start_page=7,
                end_page=9,
                page_numbers=[7, 8, 9]
            ),
            DocumentInstance(
                document_type=DocumentType.PACKING_LIST,
                start_page=10,
                end_page=10,
                page_numbers=[10]
            ),
        ]
        
        result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=10,
            classifications=[],
            extractions=[],
            validations=[],
            document_instances=doc_instances
        )
        
        # Verify document instances are stored correctly
        assert len(result.document_instances) == 5
        
        # Count documents by type
        from collections import Counter
        doc_type_counts = Counter(doc.document_type for doc in result.document_instances)
        
        assert doc_type_counts[DocumentType.INVOICE] == 3
        assert doc_type_counts[DocumentType.PACKING_LIST] == 2
        
        # Verify page ranges
        assert result.document_instances[0].page_range == "1-3"
        assert result.document_instances[1].page_range == "4"
        assert result.document_instances[2].page_range == "5-6"
        assert result.document_instances[3].page_range == "7-9"
        assert result.document_instances[4].page_range == "10"
    
    def test_complex_multi_document_scenario(self):
        """Test a scenario with alternating document types to create multiple instances."""
        # Modified scenario: One PDF with 10 pages where document types alternate
        # to create separate instances:
        # Invoice 1: pages 1-3
        # PL 1: page 4
        # Invoice 2: pages 5-6
        # PL 2: pages 7-9
        # Invoice 3: page 10
        
        classifications = [
            # Invoice 1: pages 1-3
            PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
            PageClassification(page_number=2, document_type=DocumentType.INVOICE, confidence=0.93),
            PageClassification(page_number=3, document_type=DocumentType.INVOICE, confidence=0.97),
            # PL 1: page 4
            PageClassification(page_number=4, document_type=DocumentType.PACKING_LIST, confidence=0.94),
            # Invoice 2: pages 5-6
            PageClassification(page_number=5, document_type=DocumentType.INVOICE, confidence=0.96),
            PageClassification(page_number=6, document_type=DocumentType.INVOICE, confidence=0.95),
            # PL 2: pages 7-9
            PageClassification(page_number=7, document_type=DocumentType.PACKING_LIST, confidence=0.98),
            PageClassification(page_number=8, document_type=DocumentType.PACKING_LIST, confidence=0.97),
            PageClassification(page_number=9, document_type=DocumentType.PACKING_LIST, confidence=0.96),
            # Invoice 3: page 10
            PageClassification(page_number=10, document_type=DocumentType.INVOICE, confidence=0.99),
        ]
        
        # Group pages into document instances
        documents = group_pages_into_documents(classifications)
        
        # Should have 5 document instances
        assert len(documents) == 5
        
        # Count by type
        from collections import Counter
        doc_type_counts = Counter(doc.document_type for doc in documents)
        assert doc_type_counts[DocumentType.INVOICE] == 3
        assert doc_type_counts[DocumentType.PACKING_LIST] == 2
        
        # Verify each document instance
        # Invoice 1: pages 1-3
        assert documents[0].document_type == DocumentType.INVOICE
        assert documents[0].page_range == "1-3"
        assert len(documents[0].page_numbers) == 3
        
        # PL 1: page 4
        assert documents[1].document_type == DocumentType.PACKING_LIST
        assert documents[1].page_range == "4"
        assert len(documents[1].page_numbers) == 1
        
        # Invoice 2: pages 5-6
        assert documents[2].document_type == DocumentType.INVOICE
        assert documents[2].page_range == "5-6"
        assert len(documents[2].page_numbers) == 2
        
        # PL 2: pages 7-9
        assert documents[3].document_type == DocumentType.PACKING_LIST
        assert documents[3].page_range == "7-9"
        assert len(documents[3].page_numbers) == 3
        
        # Invoice 3: page 10
        assert documents[4].document_type == DocumentType.INVOICE
        assert documents[4].page_range == "10"
        assert len(documents[4].page_numbers) == 1

