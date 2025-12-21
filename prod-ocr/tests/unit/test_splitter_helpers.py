"""Unit tests for document splitter helper functions."""
import pytest
import json
from modules.document_splitter.splitter import DocumentSplitter


@pytest.mark.unit
class TestCleanJsonResponse:
    """Tests for DocumentSplitter._clean_json_response static method."""

    def test_clean_json_without_markdown(self):
        """Test cleaning JSON without any markdown wrapping."""
        raw = '[{"doc_type": "invoice"}]'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"doc_type": "invoice"}]'

    def test_clean_json_with_json_markdown_block(self):
        """Test removing ```json ... ``` markdown blocks."""
        raw = '```json\n[{"doc_type": "invoice"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"doc_type": "invoice"}]'

    def test_clean_json_with_plain_markdown_block(self):
        """Test removing ``` ... ``` markdown blocks."""
        raw = '```\n[{"doc_type": "obl"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"doc_type": "obl"}]'

    def test_clean_json_with_whitespace(self):
        """Test stripping whitespace from response."""
        raw = '  \n\n[{"doc_type": "hawb"}]  \n  '
        result = DocumentSplitter._clean_json_response(raw)
        assert result == '[{"doc_type": "hawb"}]'

    def test_clean_json_complex_markdown(self):
        """Test cleaning complex markdown-wrapped JSON."""
        raw = '''```json
[
    {
        "doc_type": "invoice",
        "invoice_no": "0004833/E",
        "invoice_date": "2025073000000000",
        "currency_id": "EUR"
    }
]
```'''
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["doc_type"] == "invoice"

    def test_clean_json_empty_string(self):
        """Test handling empty string."""
        result = DocumentSplitter._clean_json_response("")
        assert result == ""

    def test_clean_json_preserves_internal_backticks(self):
        """Test that internal backticks in JSON values are preserved."""
        raw = '```json\n[{"doc_type": "invoice", "note": "code `sample`"}]\n```'
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert "code `sample`" in parsed[0]["note"]

    def test_clean_json_multiple_documents(self, mock_gemini_multi_document_response):
        """Test cleaning response with multiple documents."""
        raw = f"```json\n{json.dumps(mock_gemini_multi_document_response)}\n```"
        result = DocumentSplitter._clean_json_response(raw)
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0]["doc_type"] == "invoice"
        assert parsed[1]["doc_type"] == "obl"
        assert parsed[2]["doc_type"] == "packing_list"


@pytest.mark.unit
class TestDocumentSchemaValidation:
    """Tests for validating document schema structure."""

    def test_invoice_schema_has_required_fields(self, mock_gemini_invoice_response):
        """Test invoice schema has all required fields."""
        doc = mock_gemini_invoice_response[0]

        # Common required fields
        assert "doc_type" in doc
        assert "doc_type_confidence" in doc
        assert "total_pages" in doc
        assert "start_page_no" in doc
        assert "end_page_no" in doc

        # Invoice-specific fields
        assert "invoice_no" in doc
        assert "invoice_date" in doc
        assert "currency_id" in doc

    def test_obl_schema_has_required_fields(self, mock_gemini_obl_response):
        """Test OBL schema has all required fields."""
        doc = mock_gemini_obl_response[0]

        assert doc["doc_type"] == "obl"
        assert "customer_name" in doc
        assert "weight" in doc
        assert "volume" in doc

    def test_hawb_schema_has_required_fields(self, mock_gemini_hawb_response):
        """Test HAWB schema has all required fields."""
        doc = mock_gemini_hawb_response[0]

        assert doc["doc_type"] == "hawb"
        assert "customer_name" in doc
        assert "currency" in doc
        assert "carrier" in doc
        assert "hawb_number" in doc
        assert "pieces" in doc
        assert "weight" in doc

    def test_packing_list_schema_has_required_fields(self, mock_gemini_packing_list_response):
        """Test packing list schema has all required fields."""
        doc = mock_gemini_packing_list_response[0]

        assert doc["doc_type"] == "packing_list"
        assert "customer_name" in doc
        assert "pieces" in doc
        assert "weight" in doc

    def test_confidence_is_valid_float(self, mock_gemini_invoice_response):
        """Test doc_type_confidence is a valid float between 0 and 1."""
        doc = mock_gemini_invoice_response[0]
        confidence = doc["doc_type_confidence"]

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    def test_page_numbers_are_positive_integers(self, mock_gemini_invoice_response):
        """Test page numbers are positive integers."""
        doc = mock_gemini_invoice_response[0]

        assert isinstance(doc["start_page_no"], int)
        assert isinstance(doc["end_page_no"], int)
        assert isinstance(doc["total_pages"], int)
        assert doc["start_page_no"] > 0
        assert doc["end_page_no"] >= doc["start_page_no"]
        assert doc["total_pages"] > 0

    def test_pages_info_structure(self, mock_gemini_invoice_response):
        """Test pages_info has correct structure with page numbers and rotations."""
        doc = mock_gemini_invoice_response[0]

        assert "pages_info" in doc
        pages_info = doc["pages_info"]
        assert isinstance(pages_info, list)
        assert len(pages_info) == doc["total_pages"]

        for page_info in pages_info:
            assert "page_no" in page_info
            assert "rotation" in page_info
            assert isinstance(page_info["page_no"], int)
            assert isinstance(page_info["rotation"], int)
            assert page_info["rotation"] in [0, 90, 180, 270]

    def test_pages_info_covers_all_pages(self, mock_gemini_multi_document_response):
        """Test pages_info covers all pages for each document."""
        for doc in mock_gemini_multi_document_response:
            pages_info = doc["pages_info"]
            start_page = doc["start_page_no"]
            end_page = doc["end_page_no"]

            # Check we have info for all pages in the document
            page_numbers = [p["page_no"] for p in pages_info]
            expected_pages = list(range(start_page, end_page + 1))
            assert sorted(page_numbers) == expected_pages

    def test_invoice_date_format(self, mock_gemini_invoice_response):
        """Test invoice_date is 16-digit format YYYYMMDDHHMMSSSS."""
        doc = mock_gemini_invoice_response[0]
        date = doc["invoice_date"]

        assert isinstance(date, str)
        assert len(date) == 16
        assert date.isdigit()
