"""Tests for document extractors."""
import pytest
from modules.types import DocumentType, ExtractionResult
from modules.extractors import (
    ExtractorFactory,
    InvoiceExtractor,
    OBLExtractor,
    HAWBExtractor,
    PackingListExtractor
)


class TestExtractorFactory:
    """Tests for ExtractorFactory."""
    
    def test_create_invoice_extractor(self, mock_llm_client):
        """Test creating invoice extractor."""
        extractor = ExtractorFactory.create_extractor(
            DocumentType.INVOICE,
            mock_llm_client
        )
        
        assert isinstance(extractor, InvoiceExtractor)
        assert extractor.get_document_type() == DocumentType.INVOICE
    
    def test_create_obl_extractor(self, mock_llm_client):
        """Test creating OBL extractor."""
        extractor = ExtractorFactory.create_extractor(
            DocumentType.OBL,
            mock_llm_client
        )
        
        assert isinstance(extractor, OBLExtractor)
        assert extractor.get_document_type() == DocumentType.OBL
    
    def test_create_hawb_extractor(self, mock_llm_client):
        """Test creating HAWB extractor."""
        extractor = ExtractorFactory.create_extractor(
            DocumentType.HAWB,
            mock_llm_client
        )
        
        assert isinstance(extractor, HAWBExtractor)
        assert extractor.get_document_type() == DocumentType.HAWB
    
    def test_create_packing_list_extractor(self, mock_llm_client):
        """Test creating packing list extractor."""
        extractor = ExtractorFactory.create_extractor(
            DocumentType.PACKING_LIST,
            mock_llm_client
        )
        
        assert isinstance(extractor, PackingListExtractor)
        assert extractor.get_document_type() == DocumentType.PACKING_LIST
    
    def test_create_unknown_type_extractor(self, mock_llm_client):
        """Test creating extractor for unknown type raises error."""
        with pytest.raises(ValueError):
            ExtractorFactory.create_extractor(
                DocumentType.UNKNOWN,
                mock_llm_client
            )


class TestInvoiceExtractor:
    """Tests for InvoiceExtractor."""
    
    def test_get_document_type(self, mock_llm_client):
        """Test getting document type."""
        extractor = InvoiceExtractor(mock_llm_client)
        assert extractor.get_document_type() == DocumentType.INVOICE
    
    def test_get_system_prompt(self, mock_llm_client):
        """Test getting system prompt."""
        extractor = InvoiceExtractor(mock_llm_client)
        prompt = extractor.get_system_prompt()
        
        assert prompt is not None
        assert len(prompt) > 0
        assert "invoice" in prompt.lower()
    
    def test_extract_with_mock_success(self, mock_llm_client, sample_invoice_data):
        """Test extraction with mocked successful response."""
        # Update mock to return sample data
        mock_llm_client.generate_json_content = lambda **kwargs: sample_invoice_data
        
        extractor = InvoiceExtractor(mock_llm_client)
        result = extractor.extract(b"fake pdf data", page_number=1)
        
        assert isinstance(result, ExtractionResult)
        assert result.success
        assert result.document_type == DocumentType.INVOICE
        assert result.page_number == 1
        assert result.data == sample_invoice_data
    
    def test_extract_with_mock_failure(self, mock_llm_client):
        """Test extraction with mocked failure."""
        # Update mock to raise exception
        def raise_error(**kwargs):
            raise Exception("Mock extraction error")
        
        mock_llm_client.generate_json_content = raise_error
        
        extractor = InvoiceExtractor(mock_llm_client)
        result = extractor.extract(b"fake pdf data", page_number=1)
        
        assert isinstance(result, ExtractionResult)
        assert not result.success
        assert result.error_message is not None
        assert "Mock extraction error" in result.error_message


class TestOBLExtractor:
    """Tests for OBLExtractor."""
    
    def test_get_document_type(self, mock_llm_client):
        """Test getting document type."""
        extractor = OBLExtractor(mock_llm_client)
        assert extractor.get_document_type() == DocumentType.OBL
    
    def test_get_system_prompt(self, mock_llm_client):
        """Test getting system prompt."""
        extractor = OBLExtractor(mock_llm_client)
        prompt = extractor.get_system_prompt()
        
        assert prompt is not None
        assert "OBL" in prompt or "bill of lading" in prompt.lower()


class TestHAWBExtractor:
    """Tests for HAWBExtractor."""
    
    def test_get_document_type(self, mock_llm_client):
        """Test getting document type."""
        extractor = HAWBExtractor(mock_llm_client)
        assert extractor.get_document_type() == DocumentType.HAWB
    
    def test_get_system_prompt(self, mock_llm_client):
        """Test getting system prompt."""
        extractor = HAWBExtractor(mock_llm_client)
        prompt = extractor.get_system_prompt()
        
        assert prompt is not None
        assert "HAWB" in prompt or "air waybill" in prompt.lower()


class TestPackingListExtractor:
    """Tests for PackingListExtractor."""
    
    def test_get_document_type(self, mock_llm_client):
        """Test getting document type."""
        extractor = PackingListExtractor(mock_llm_client)
        assert extractor.get_document_type() == DocumentType.PACKING_LIST
    
    def test_get_system_prompt(self, mock_llm_client):
        """Test getting system prompt."""
        extractor = PackingListExtractor(mock_llm_client)
        prompt = extractor.get_system_prompt()
        
        assert prompt is not None
        assert "packing list" in prompt.lower()
