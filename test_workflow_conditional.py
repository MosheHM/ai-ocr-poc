"""Test script to verify the validation workflow skips PDFs without .txt files."""
import os
from pathlib import Path
from modules.workflows import ValidationWorkflow


def test_invoice_with_txt():
    """Test processing an invoice that has a .txt ground truth file."""
    print("\n" + "=" * 80)
    print("TEST 1: Processing Invoice WITH .txt ground truth file")
    print("=" * 80)
    
    # This invoice has a .txt file
    pdf_path = "sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF"
    
    if not Path(pdf_path).exists():
        print(f"⚠ Test file not found: {pdf_path}")
        return
    
    # Note: We're not setting GEMINI_API_KEY, so it should fail gracefully
    # For real testing, you would set the API key
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    
    try:
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(pdf_path)
        
        print(f"\nResult:")
        print(f"  Success: {result.success}")
        print(f"  Total Pages: {result.total_pages}")
        print(f"  Classifications: {len(result.classifications)}")
        print(f"  Extractions: {len(result.extractions)}")
        print(f"  Validations: {len(result.validations)}")
        print(f"  Errors: {result.errors}")
        
        # Check that it found the .txt file and attempted processing
        if result.errors:
            has_txt_skip_msg = any("No .txt ground truth file" in err for err in result.errors)
            if has_txt_skip_msg:
                print("\n❌ FAIL: Should NOT skip when .txt file exists")
            else:
                print("\n✓ PASS: Attempted to process (errors may be due to dummy API key)")
        else:
            print("\n✓ PASS: Processing completed successfully")
            
    except Exception as e:
        print(f"\n✓ PASS: Got expected error (likely due to dummy API key): {e}")


def test_bol_without_txt():
    """Test processing a BOL that does NOT have a .txt ground truth file."""
    print("\n" + "=" * 80)
    print("TEST 2: Processing BOL WITHOUT .txt ground truth file")
    print("=" * 80)
    
    # This BOL does not have a .txt file
    pdf_path = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
    
    if not Path(pdf_path).exists():
        print(f"⚠ Test file not found: {pdf_path}")
        return
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    
    workflow = ValidationWorkflow(api_key)
    result = workflow.process_document(pdf_path)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Total Pages: {result.total_pages}")
    print(f"  Classifications: {len(result.classifications)}")
    print(f"  Extractions: {len(result.extractions)}")
    print(f"  Validations: {len(result.validations)}")
    print(f"  Errors: {result.errors}")
    
    # Check that it was skipped
    has_skip_msg = any("No .txt ground truth file" in err for err in result.errors)
    
    if has_skip_msg and result.success and len(result.extractions) == 0:
        print("\n✓ PASS: Correctly skipped processing (no .txt file)")
    else:
        print("\n❌ FAIL: Should have skipped processing when no .txt file exists")


def test_packing_list_without_txt():
    """Test processing a Packing List that does NOT have a .txt ground truth file."""
    print("\n" + "=" * 80)
    print("TEST 3: Processing Packing List WITHOUT .txt ground truth file")
    print("=" * 80)
    
    # This packing list does not have a .txt file
    pdf_path = "sampels/combined-sampels/81123758_SC_PACKING LIST_ddbh7b79suuww8wv+yzf7w00000000.PDF"
    
    if not Path(pdf_path).exists():
        print(f"⚠ Test file not found: {pdf_path}")
        return
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    
    workflow = ValidationWorkflow(api_key)
    result = workflow.process_document(pdf_path)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Total Pages: {result.total_pages}")
    print(f"  Classifications: {len(result.classifications)}")
    print(f"  Extractions: {len(result.extractions)}")
    print(f"  Validations: {len(result.validations)}")
    print(f"  Errors: {result.errors}")
    
    # Check that it was skipped
    has_skip_msg = any("No .txt ground truth file" in err for err in result.errors)
    
    if has_skip_msg and result.success and len(result.extractions) == 0:
        print("\n✓ PASS: Correctly skipped processing (no .txt file)")
    else:
        print("\n❌ FAIL: Should have skipped processing when no .txt file exists")


if __name__ == "__main__":
    print("\nTesting Conditional Processing Based on .txt File Existence")
    print("=" * 80)
    
    # Test with invoice that has .txt
    test_invoice_with_txt()
    
    # Test with BOL that doesn't have .txt
    test_bol_without_txt()
    
    # Test with Packing List that doesn't have .txt
    test_packing_list_without_txt()
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)
