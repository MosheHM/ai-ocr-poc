"""Unit tests for document splitter helper functions."""
import pytest
import json
from modules.document_splitter.splitter import DocumentSplitter


@pytest.mark.unit
class TestCleanJsonResponse:
    """Tests for DocumentSplitter._clean_json_response static method."""

    def test_clean_json_without_markdown(self):
        """Test cleaning JSON without any markdown wrapping."""
        raw = '[{"DOC_TYPE": "INVOICE"}]'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"DOC_TYPE": "INVOICE"}]'

    def test_clean_json_with_json_markdown_block(self):
        """Test removing ```json ... ``` markdown blocks."""
        raw = '```json\n[{"DOC_TYPE": "INVOICE"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"DOC_TYPE": "INVOICE"}]'

    def test_clean_json_with_plain_markdown_block(self):
        """Test removing ``` ... ``` markdown blocks."""
        raw = '```\n[{"DOC_TYPE": "OBL"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"DOC_TYPE": "OBL"}]'

    def test_clean_json_with_whitespace(self):
        """Test stripping whitespace from response."""
        raw = '  \n\n[{"DOC_TYPE": "HAWB"}]  \n  '
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"DOC_TYPE": "HAWB"}]'

    def test_clean_json_complex_markdown(self):
        """Test cleaning complex markdown-wrapped JSON."""
        raw = '''```json
[
    {
        "DOC_TYPE": "INVOICE",
        "INVOICE_NO": "0004833/E",
        "INVOICE_DATE": "2025073000000000",
        "CURRENCY_ID": "EUR"
    }
]
```'''
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["DOC_TYPE"] == "INVOICE"

    def test_clean_json_empty_string(self):
        """Test handling empty string."""
        result = DocumentSplitter._clean_json_response("")
        assert result == ""

    def test_clean_json_preserves_internal_backticks(self):
        """Test that internal backticks in JSON values are preserved."""
        raw = '```json\n[{"DOC_TYPE": "INVOICE", "NOTE": "code `sample`"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert "code `sample`" in parsed[0]["NOTE"]

    def test_clean_json_multiple_documents(self, mock_gemini_multi_document_response):
        """Test cleaning response with multiple documents."""
        raw = f"```json\n{json.dumps(mock_gemini_multi_document_response)}\n```"
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["DOC_TYPE"] == "INVOICE"
        assert parsed[1]["DOC_TYPE"] == "OBL"
        assert parsed[2]["DOC_TYPE"] == "PACKING_LIST"


@pytest.mark.unit
class TestDocumentSchemaValidation:
    """Tests for validating document schema structure."""

    def test_invoice_schema_has_required_fields(self, mock_gemini_invoice_response):
        """Test invoice schema has all required fields."""
        doc = mock_gemini_invoice_response[0]
        
        # Common required fields
        assert "DOC_TYPE" in doc
        assert "DOC_TYPE_CONFIDENCE" in doc
        assert "TOTAL_PAGES" in doc
        assert "START_PAGE_NO" in doc
        assert "END_PAGE_NO" in doc
        
        # Invoice-specific fields
        assert "INVOICE_NO" in doc
        assert "INVOICE_DATE" in doc
        assert "CURRENCY_ID" in doc

    def test_obl_schema_has_required_fields(self, mock_gemini_obl_response):
        """Test OBL schema has all required fields."""
        doc = mock_gemini_obl_response[0]
        
        assert doc["DOC_TYPE"] == "OBL"
        assert "CUSTOMER_NAME" in doc
        assert "WEIGHT" in doc
        assert "VOLUME" in doc

    def test_hawb_schema_has_required_fields(self, mock_gemini_hawb_response):
        """Test HAWB schema has all required fields."""
        doc = mock_gemini_hawb_response[0]
        
        assert doc["DOC_TYPE"] == "HAWB"
        assert "CUSTOMER_NAME" in doc
        assert "CURRENCY" in doc
        assert "CARRIER" in doc
        assert "HAWB_NUMBER" in doc
        assert "PIECES" in doc
        assert "WEIGHT" in doc

    def test_packing_list_schema_has_required_fields(self, mock_gemini_packing_list_response):
        """Test packing list schema has all required fields."""
        doc = mock_gemini_packing_list_response[0]
        
        assert doc["DOC_TYPE"] == "PACKING_LIST"
        assert "CUSTOMER_NAME" in doc
        assert "PIECES" in doc
        assert "WEIGHT" in doc

    def test_confidence_is_valid_float(self, mock_gemini_invoice_response):
        """Test DOC_TYPE_CONFIDENCE is a valid float between 0 and 1."""
        doc = mock_gemini_invoice_response[0]
        confidence = doc["DOC_TYPE_CONFIDENCE"]
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    def test_page_numbers_are_positive_integers(self, mock_gemini_invoice_response):
        """Test page numbers are positive integers."""
        doc = mock_gemini_invoice_response[0]
        
        assert isinstance(doc["START_PAGE_NO"], int)
        assert isinstance(doc["END_PAGE_NO"], int)
        assert isinstance(doc["TOTAL_PAGES"], int)
        assert doc["START_PAGE_NO"] > 0
        assert doc["END_PAGE_NO"] >= doc["START_PAGE_NO"]
        assert doc["TOTAL_PAGES"] > 0

    def test_invoice_date_format(self, mock_gemini_invoice_response):
        """Test INVOICE_DATE is 16-digit format YYYYMMDDHHMMSSSS."""
        doc = mock_gemini_invoice_response[0]
        date = doc["INVOICE_DATE"]
        
        assert isinstance(date, str)
        assert len(date) == 16
        assert date.isdigit()
