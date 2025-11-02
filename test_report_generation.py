"""Test the report generation for skipped documents."""
import os
from pathlib import Path
from modules.workflows import ValidationWorkflow


def test_skipped_report():
    """Test report generation for a document without .txt file."""
    print("\n" + "=" * 80)
    print("Testing Report Generation for Skipped Document")
    print("=" * 80)
    
    # This BOL does not have a .txt file
    pdf_path = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
    
    if not Path(pdf_path).exists():
        print(f"⚠ Test file not found: {pdf_path}")
        return
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    
    workflow = ValidationWorkflow(api_key)
    result = workflow.process_document(pdf_path)
    
    # Generate and print report
    report = workflow.generate_report(result)
    print(report)


def test_processed_report():
    """Test report generation for a document with .txt file."""
    print("\n" + "=" * 80)
    print("Testing Report Generation for Processed Document")
    print("=" * 80)
    
    # This invoice has a .txt file
    pdf_path = "sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF"
    
    if not Path(pdf_path).exists():
        print(f"⚠ Test file not found: {pdf_path}")
        return
    
    api_key = os.getenv('GEMINI_API_KEY', 'dummy-key-for-testing')
    
    workflow = ValidationWorkflow(api_key)
    result = workflow.process_document(pdf_path)
    
    # Generate and print report
    report = workflow.generate_report(result)
    print(report)


if __name__ == "__main__":
    test_skipped_report()
    test_processed_report()
