"""Integration tests for DocumentSplitter with mocked Gemini API."""
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from modules.document_splitter.splitter import DocumentSplitter, split_and_extract_documents


@pytest.mark.integration
class TestDocumentSplitterExtractDocuments:
    """Tests for DocumentSplitter.extract_documents with mocked Gemini."""

    @pytest.fixture
    def splitter(self, mocker):
        """Create a DocumentSplitter with mocked Gemini client."""
        mocker.patch('modules.document_splitter.splitter.genai.Client')
        return DocumentSplitter(api_key="test-api-key", model="gemini-2.5-flash")

    def test_extract_single_invoice(self, splitter, sample_pdf_file, mock_gemini_invoice_response, mocker):
        """Test extracting a single invoice document."""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert len(result) == 1
        assert result[0]["DOC_TYPE"] == "INVOICE"
        assert result[0]["INVOICE_NO"] == "0004833/E"
        assert result[0]["DOC_TYPE_CONFIDENCE"] == 0.95

    def test_extract_multiple_documents(self, splitter, multi_page_pdf_file, mock_gemini_multi_document_response, mocker):
        """Test extracting multiple documents from a single PDF."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_multi_document_response)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(multi_page_pdf_file))

        assert len(result) == 3
        assert result[0]["DOC_TYPE"] == "INVOICE"
        assert result[1]["DOC_TYPE"] == "OBL"
        assert result[2]["DOC_TYPE"] == "PACKING_LIST"

    def test_extract_handles_markdown_wrapped_response(self, splitter, sample_pdf_file, mock_gemini_invoice_response):
        """Test handling Gemini response wrapped in markdown code blocks."""
        markdown_response = f"```json\n{json.dumps(mock_gemini_invoice_response)}\n```"
        mock_response = MagicMock()
        mock_response.text = markdown_response
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert len(result) == 1
        assert result[0]["DOC_TYPE"] == "INVOICE"

    def test_extract_wraps_single_object_in_list(self, splitter, sample_pdf_file, mock_gemini_invoice_response):
        """Test that a single document object is wrapped in a list."""
        # Return a single object, not an array
        single_doc = mock_gemini_invoice_response[0]
        mock_response = MagicMock()
        mock_response.text = json.dumps(single_doc)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert isinstance(result, list)
        assert len(result) == 1

    def test_extract_raises_on_too_many_documents(self, splitter, sample_pdf_file):
        """Test that more than 100 documents raises ValueError."""
        # Create 101 mock documents
        many_docs = [
            {
                "DOC_TYPE": "INVOICE",
                "INVOICE_NO": f"INV-{i}",
                "DOC_TYPE_CONFIDENCE": 0.9,
                "TOTAL_PAGES": 1,
                "START_PAGE_NO": i,
                "END_PAGE_NO": i
            }
            for i in range(101)
        ]
        mock_response = MagicMock()
        mock_response.text = json.dumps(many_docs)
        splitter.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="Too many documents"):
            splitter.extract_documents(str(sample_pdf_file))

    def test_extract_raises_on_invalid_json(self, splitter, sample_pdf_file):
        """Test that invalid JSON response raises ValueError."""
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON at all"
        splitter.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON response"):
            splitter.extract_documents(str(sample_pdf_file))

    def test_extract_handles_obl_document(self, splitter, sample_pdf_file, mock_gemini_obl_response):
        """Test extracting OBL document type."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_obl_response)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert result[0]["DOC_TYPE"] == "OBL"
        assert result[0]["CUSTOMER_NAME"] == "LAPIDOTH CAPITAL LTD."
        assert result[0]["WEIGHT"] == 115000.0
        assert result[0]["VOLUME"] == 1.116

    def test_extract_handles_hawb_document(self, splitter, sample_pdf_file, mock_gemini_hawb_response):
        """Test extracting HAWB document type."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_hawb_response)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert result[0]["DOC_TYPE"] == "HAWB"
        assert result[0]["HAWB_NUMBER"] == "176-12345678"
        assert result[0]["CARRIER"] == "Emirates"

    def test_extract_handles_packing_list(self, splitter, sample_pdf_file, mock_gemini_packing_list_response):
        """Test extracting packing list document type."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_packing_list_response)
        splitter.client.models.generate_content.return_value = mock_response

        result = splitter.extract_documents(str(sample_pdf_file))

        assert result[0]["DOC_TYPE"] == "PACKING_LIST"
        assert result[0]["PIECES"] == 100
        assert result[0]["WEIGHT"] == 2500.0


@pytest.mark.integration
class TestDocumentSplitterSplitAndSave:
    """Tests for DocumentSplitter.split_and_save with mocked Gemini."""

    @pytest.fixture
    def splitter(self, mocker):
        """Create a DocumentSplitter with mocked Gemini client."""
        mocker.patch('modules.document_splitter.splitter.genai.Client')
        return DocumentSplitter(api_key="test-api-key", model="gemini-2.5-flash")

    def test_split_and_save_creates_output_files(self, splitter, multi_page_pdf_file, tmp_path, mock_gemini_invoice_response):
        """Test that split_and_save creates PDF files in output directory."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        splitter.client.models.generate_content.return_value = mock_response

        output_dir = tmp_path / "split_output"
        result = splitter.split_and_save(str(multi_page_pdf_file), str(output_dir))

        assert output_dir.exists()
        assert result["total_documents"] == 1
        assert len(result["documents"]) == 1
        
        # Check that FILE_PATH and FILE_NAME were added
        doc = result["documents"][0]
        assert "FILE_PATH" in doc
        assert "FILE_NAME" in doc
        assert Path(doc["FILE_PATH"]).exists()

    def test_split_and_save_creates_results_json(self, splitter, sample_pdf_file, tmp_path, mock_gemini_invoice_response):
        """Test that split_and_save creates extraction_results.json."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        splitter.client.models.generate_content.return_value = mock_response

        output_dir = tmp_path / "output"
        splitter.split_and_save(str(sample_pdf_file), str(output_dir), base_filename="test_doc")

        results_file = output_dir / "test_doc_extraction_results.json"
        assert results_file.exists()
        
        with open(results_file) as f:
            saved_results = json.load(f)
        
        assert "source_pdf" in saved_results
        assert "total_documents" in saved_results
        assert "documents" in saved_results

    def test_split_and_save_uses_default_filename(self, splitter, sample_pdf_file, tmp_path, mock_gemini_invoice_response):
        """Test that split_and_save uses PDF filename as default base."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        splitter.client.models.generate_content.return_value = mock_response

        output_dir = tmp_path / "output"
        result = splitter.split_and_save(str(sample_pdf_file), str(output_dir))

        # The default base_filename should be the PDF stem
        doc = result["documents"][0]
        assert "test_document" in doc["FILE_NAME"]  # from sample_pdf_file fixture

    def test_split_and_save_handles_multiple_documents(self, splitter, multi_page_pdf_file, tmp_path, mock_gemini_multi_document_response):
        """Test splitting PDF with multiple document types."""
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_multi_document_response)
        splitter.client.models.generate_content.return_value = mock_response

        output_dir = tmp_path / "output"
        result = splitter.split_and_save(str(multi_page_pdf_file), str(output_dir))

        assert result["total_documents"] == 3
        
        doc_types = [doc["DOC_TYPE"] for doc in result["documents"]]
        assert "INVOICE" in doc_types
        assert "OBL" in doc_types
        assert "PACKING_LIST" in doc_types


@pytest.mark.integration
class TestSplitAndExtractDocumentsConvenience:
    """Tests for the convenience function split_and_extract_documents."""

    def test_uses_env_api_key(self, sample_pdf_file, tmp_path, mock_gemini_invoice_response, monkeypatch, mocker):
        """Test that function uses GEMINI_API_KEY from environment."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-env-api-key")
        
        mock_client = mocker.patch('modules.document_splitter.splitter.genai.Client')
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        mock_client.return_value.models.generate_content.return_value = mock_response

        result = split_and_extract_documents(
            str(sample_pdf_file),
            str(tmp_path / "output")
        )

        assert result["total_documents"] == 1
        mock_client.assert_called_once_with(api_key="test-env-api-key")

    def test_raises_without_api_key(self, sample_pdf_file, tmp_path, monkeypatch):
        """Test that ValueError is raised when no API key available."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            split_and_extract_documents(
                str(sample_pdf_file),
                str(tmp_path / "output")
            )

    def test_accepts_explicit_api_key(self, sample_pdf_file, tmp_path, mock_gemini_invoice_response, mocker):
        """Test that explicit api_key parameter is used."""
        mock_client = mocker.patch('modules.document_splitter.splitter.genai.Client')
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_invoice_response)
        mock_client.return_value.models.generate_content.return_value = mock_response

        split_and_extract_documents(
            str(sample_pdf_file),
            str(tmp_path / "output"),
            api_key="explicit-api-key"
        )

        mock_client.assert_called_once_with(api_key="explicit-api-key")
