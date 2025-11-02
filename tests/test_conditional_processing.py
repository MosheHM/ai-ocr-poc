"""Tests for conditional processing based on .txt ground truth files."""
import os
import tempfile
import json
from pathlib import Path
import pytest
from modules.utils import find_ground_truth_txt, load_ground_truth_from_txt
from modules.workflows import ValidationWorkflow


class TestGroundTruthDetection:
    """Test the detection and loading of .txt ground truth files."""
    
    def test_find_ground_truth_txt_not_exists(self):
        """Test when no .txt file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test_invoice.PDF"
            pdf_path.write_text("dummy pdf content")
            
            result = find_ground_truth_txt(str(pdf_path))
            assert result is None
    
    def test_find_ground_truth_txt_exists(self):
        """Test when .txt file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test_invoice.PDF"
            pdf_path.write_text("dummy pdf content")
            
            txt_path = Path(tmpdir) / "test_invoice.txt"
            txt_path.write_text('{"test": "data"}')
            
            result = find_ground_truth_txt(str(pdf_path))
            assert result == str(txt_path)
    
    def test_load_ground_truth_simple_json(self):
        """Test loading simple JSON ground truth."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "test_gt.txt"
            simple_data = {"INVOICE_NO": "12345", "AMOUNT": 100.50}
            txt_path.write_text(json.dumps(simple_data))
            
            result = load_ground_truth_from_txt(str(txt_path))
            assert result == simple_data
    
    def test_load_ground_truth_with_occ_wrapper(self):
        """Test loading JSON with OCC wrapper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "test_gt.txt"
            occ_data = {
                "OCC": {
                    "INVOICE_NO": "67890",
                    "AMOUNT": 200.75
                }
            }
            txt_path.write_text(json.dumps(occ_data))
            
            result = load_ground_truth_from_txt(str(txt_path))
            assert result == occ_data["OCC"]
    
    def test_load_ground_truth_invalid_json(self):
        """Test loading invalid JSON returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = Path(tmpdir) / "test_gt.txt"
            txt_path.write_text("not valid json")
            
            result = load_ground_truth_from_txt(str(txt_path))
            assert result is None


class TestConditionalProcessing:
    """Test the conditional processing workflow."""
    
    def test_workflow_skips_without_txt_file(self):
        """Test that workflow skips processing when no .txt file exists."""
        # Use a BOL sample that doesn't have a .txt file
        bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
        
        if not Path(bol_pdf).exists():
            pytest.skip(f"Test file not found: {bol_pdf}")
        
        api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(bol_pdf)
        
        # Verify skipped behavior
        assert result.success == True
        assert len(result.classifications) == 0
        assert len(result.extractions) == 0
        assert len(result.validations) == 0
        assert any("No .txt ground truth file" in err for err in result.errors)
    
    def test_workflow_processes_with_txt_file(self):
        """Test that workflow attempts processing when .txt file exists."""
        # Use an invoice sample that has a .txt file
        invoice_pdf = "sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF"
        
        if not Path(invoice_pdf).exists():
            pytest.skip(f"Test file not found: {invoice_pdf}")
        
        api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(invoice_pdf)
        
        # Verify processing was attempted (will fail with dummy API key)
        assert result.success == True
        # Should NOT have the skip message
        has_skip_msg = any("No .txt ground truth file" in err for err in result.errors)
        assert not has_skip_msg
    
    def test_report_shows_skipped_status(self):
        """Test that report correctly shows skipped status."""
        # Use a BOL sample without .txt file
        bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
        
        if not Path(bol_pdf).exists():
            pytest.skip(f"Test file not found: {bol_pdf}")
        
        api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(bol_pdf)
        
        # Generate report
        report = workflow.generate_report(result)
        
        # Verify report shows skipped status
        assert "SKIPPED" in report
        assert "No .txt ground truth file" in report
    
    def test_json_output_has_skipped_field(self):
        """Test that JSON output includes skipped field."""
        # Use a BOL sample without .txt file
        bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
        
        if not Path(bol_pdf).exists():
            pytest.skip(f"Test file not found: {bol_pdf}")
        
        api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(bol_pdf)
        
        # Simulate JSON output creation
        skipped = any("No .txt ground truth file" in err for err in result.errors)
        
        result_dict = {
            'pdf_path': result.pdf_path,
            'skipped': skipped,
            'success': result.success,
        }
        
        # Verify JSON structure
        assert 'skipped' in result_dict
        assert result_dict['skipped'] == True
        assert result_dict['success'] == True
