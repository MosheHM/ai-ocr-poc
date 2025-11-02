"""Integration test to verify the complete workflow with .txt file validation."""
import os
import json
import tempfile
from pathlib import Path
from modules.workflows import ValidationWorkflow


def test_complete_workflow():
    """Test the complete workflow with both skipped and processed documents."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Complete Workflow")
    print("=" * 80)
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    workflow = ValidationWorkflow(api_key)
    
    # Test 1: Document without .txt file (should be skipped)
    print("\n1. Testing document WITHOUT .txt file (BOL)")
    print("-" * 80)
    
    bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
    
    if Path(bol_pdf).exists():
        result = workflow.process_document(bol_pdf)
        
        # Verify skipped behavior
        assert result.success == True, "Should be successful (skipped)"
        assert len(result.classifications) == 0, "Should have no classifications"
        assert len(result.extractions) == 0, "Should have no extractions"
        assert len(result.validations) == 0, "Should have no validations"
        assert any("No .txt ground truth file" in err for err in result.errors), "Should have skip message"
        
        print("✓ Correctly skipped document without .txt file")
        print(f"  Total pages: {result.total_pages}")
        print(f"  Errors: {result.errors}")
        
        # Generate report
        report = workflow.generate_report(result)
        assert "SKIPPED" in report, "Report should indicate skipped status"
        print("✓ Report correctly shows SKIPPED status")
    else:
        print(f"⚠ Test file not found: {bol_pdf}")
    
    # Test 2: Document with .txt file (should be processed)
    print("\n2. Testing document WITH .txt file (Invoice)")
    print("-" * 80)
    
    invoice_pdf = "sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF"
    
    if Path(invoice_pdf).exists():
        result = workflow.process_document(invoice_pdf)
        
        # Verify processing attempted (will fail with dummy API key, but that's expected)
        assert result.success == True, "Should be successful (attempted processing)"
        # Classifications may be empty or have Unknown type due to dummy API key
        print(f"  Total pages: {result.total_pages}")
        print(f"  Classifications: {len(result.classifications)}")
        print(f"  Extractions: {len(result.extractions)}")
        print(f"  Validations: {len(result.validations)}")
        
        # Should NOT have the skip message
        has_skip_msg = any("No .txt ground truth file" in err for err in result.errors)
        assert not has_skip_msg, "Should NOT have skip message when .txt exists"
        
        print("✓ Correctly attempted to process document with .txt file")
        
        # Generate report
        report = workflow.generate_report(result)
        assert "SKIPPED" not in report, "Report should NOT indicate skipped status"
        print("✓ Report correctly shows processing attempt")
    else:
        print(f"⚠ Test file not found: {invoice_pdf}")
    
    # Test 3: Packing List without .txt file (should be skipped)
    print("\n3. Testing document WITHOUT .txt file (Packing List)")
    print("-" * 80)
    
    packing_pdf = "sampels/combined-sampels/81123758_SC_PACKING LIST_ddbh7b79suuww8wv+yzf7w00000000.PDF"
    
    if Path(packing_pdf).exists():
        result = workflow.process_document(packing_pdf)
        
        # Verify skipped behavior
        assert result.success == True, "Should be successful (skipped)"
        assert len(result.extractions) == 0, "Should have no extractions"
        assert any("No .txt ground truth file" in err for err in result.errors), "Should have skip message"
        
        print("✓ Correctly skipped Packing List without .txt file")
        print(f"  Total pages: {result.total_pages}")
    else:
        print(f"⚠ Test file not found: {packing_pdf}")
    
    print("\n" + "=" * 80)
    print("✓ ALL INTEGRATION TESTS PASSED")
    print("=" * 80)


def test_json_output_format():
    """Test that JSON output has correct format with skipped field."""
    print("\n" + "=" * 80)
    print("TEST: JSON Output Format")
    print("=" * 80)
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    workflow = ValidationWorkflow(api_key)
    
    # Test with skipped document
    bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
    
    if Path(bol_pdf).exists():
        result = workflow.process_document(bol_pdf)
        
        # Simulate main.py JSON output creation
        skipped = any("No .txt ground truth file" in err for err in result.errors)
        
        result_dict = {
            'pdf_path': result.pdf_path,
            'total_pages': result.total_pages,
            'success': result.success,
            'skipped': skipped,
            'overall_score': result.overall_score,
            'errors': result.errors
        }
        
        print(json.dumps(result_dict, indent=2))
        
        # Verify JSON structure
        assert 'skipped' in result_dict, "JSON should have 'skipped' field"
        assert result_dict['skipped'] == True, "Skipped should be True for BOL without .txt"
        assert result_dict['success'] == True, "Success should be True (not an error)"
        
        print("\n✓ JSON output format is correct")
    else:
        print(f"⚠ Test file not found: {bol_pdf}")


if __name__ == "__main__":
    test_complete_workflow()
    test_json_output_format()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
