"""Tests for ZIP utility functions."""
import pytest
import json
import zipfile
from pathlib import Path

from modules.utils.zip_utils import create_results_zip


@pytest.mark.unit
class TestCreateResultsZip:
    """Tests for create_results_zip function."""

    @pytest.fixture
    def sample_results_data(self, tmp_path, sample_pdf_bytes):
        """Create sample results data with actual PDF files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create sample PDF files
        pdf1_path = output_dir / "doc_INVOICE_1_pages_1-2.pdf"
        pdf2_path = output_dir / "doc_OBL_2_pages_3-3.pdf"
        pdf1_path.write_bytes(sample_pdf_bytes)
        pdf2_path.write_bytes(sample_pdf_bytes)
        
        results = {
            "source_pdf": "/original/input.pdf",
            "total_documents": 2,
            "documents": [
                {
                    "doc_type": "invoice",
                    "doc_type_confidence": 0.95,
                    "total_pages": 2,
                    "start_page_no": 1,
                    "end_page_no": 2,
                    "pages_info": [],
                    "doc_data": [{"field_id": "invoice_no", "field_value": "INV-001"}]
                },
                {
                    "doc_type": "obl",
                    "doc_type_confidence": 0.90,
                    "total_pages": 1,
                    "start_page_no": 3,
                    "end_page_no": 3,
                    "pages_info": [],
                    "doc_data": [{"field_id": "customer_name", "field_value": "Test Corp"}]
                }
            ]
        }
        
        return output_dir, results

    def test_creates_zip_file(self, sample_results_data):
        """Test that ZIP file is created."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        assert Path(zip_path).exists()
        assert zip_path.endswith(".zip")

    def test_zip_contains_results_json(self, sample_results_data):
        """Test that ZIP contains extraction_results.json."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            assert "extraction_results.json" in zf.namelist()
            
            with zf.open("extraction_results.json") as f:
                saved_results = json.load(f)
            
            assert saved_results["total_documents"] == 2

    def test_zip_contains_pdf_files(self, sample_results_data):
        """Test that ZIP contains all PDF files."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            filenames = zf.namelist()
            assert "doc_INVOICE_1_pages_1-2.pdf" in filenames
            assert "doc_OBL_2_pages_3-3.pdf" in filenames

    def test_custom_zip_filename(self, sample_results_data):
        """Test using custom ZIP filename."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(
            str(output_dir), 
            results, 
            zip_filename="custom_name.zip"
        )
        
        assert Path(zip_path).name == "custom_name.zip"

    def test_default_zip_filename(self, sample_results_data):
        """Test default ZIP filename is processing_results.zip."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        assert Path(zip_path).name == "processing_results.zip"

    def test_handles_missing_files_gracefully(self, tmp_path):
        """Test that missing files are skipped without error."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        results = {
            "source_pdf": "/input.pdf",
            "total_documents": 1,
            "documents": [
                {
                    "doc_type": "invoice",
                    "doc_type_confidence": 0.95,
                    "total_pages": 1,
                    "start_page_no": 1,
                    "end_page_no": 1,
                    "pages_info": [],
                    "doc_data": []
                }
            ]
        }
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Should only contain the JSON, not the missing PDF
            assert "extraction_results.json" in zf.namelist()
            assert "nonexistent.pdf" not in zf.namelist()

    def test_zip_is_compressed(self, sample_results_data):
        """Test that ZIP uses compression."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check compression type
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_DEFLATED

    def test_handles_empty_documents_list(self, tmp_path):
        """Test handling results with no documents."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        results = {
            "source_pdf": "/input.pdf",
            "output_directory": str(output_dir),
            "total_documents": 0,
            "documents": []
        }
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            assert len(zf.namelist()) == 1  # Only the JSON file
            assert "extraction_results.json" in zf.namelist()

    def test_json_is_properly_formatted(self, sample_results_data):
        """Test that JSON in ZIP is properly formatted with indentation."""
        output_dir, results = sample_results_data
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open("extraction_results.json") as f:
                content = f.read().decode('utf-8')
        
        # Check it's indented (not minified)
        assert '\n' in content
        assert '  ' in content  # Has indentation

    def test_handles_unicode_in_results(self, tmp_path, sample_pdf_bytes):
        """Test handling Unicode characters in results data."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        pdf_path = output_dir / "doc.pdf"
        pdf_path.write_bytes(sample_pdf_bytes)
        
        results = {
            "source_pdf": "/input.pdf",
            "total_documents": 1,
            "documents": [
                {
                    "doc_type": "invoice",
                    "doc_type_confidence": 0.95,
                    "total_pages": 1,
                    "start_page_no": 1,
                    "end_page_no": 1,
                    "pages_info": [],
                    "doc_data": [{"field_id": "customer_name", "field_value": "日本語テスト 中文测试 עברית"}],
                    "FILE_NAME": "doc.pdf"
                }
            ]
        }
        
        zip_path = create_results_zip(str(output_dir), results)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            with zf.open("extraction_results.json") as f:
                saved = json.load(f)
        
        assert saved["documents"][0]["CUSTOMER_NAME"] == "日本語テスト 中文测试 עברית"
