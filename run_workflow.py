#!/usr/bin/env python3
"""
Minimal script to check and test the AI OCR POC.

This script demonstrates the POC functionality by:
1. Checking if all dependencies are installed
2. Verifying the module structure
3. Running a basic workflow test (if API key is provided)

Usage:
    # Basic check (no API key required)
    python run_workflow.py

    # Full test with a sample PDF (requires GEMINI_API_KEY)
    python run_workflow.py --pdf path/to/sample.pdf

    # Test with ground truth validation
    python run_workflow.py --pdf path/to/sample.pdf --ground-truth path/to/ground_truth.json
"""

import os
import sys
import argparse
from pathlib import Path


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("=" * 70)
    print("Checking Dependencies")
    print("=" * 70)
    
    dependencies = {
        'google.genai': 'google-genai',
        'pypdf': 'pypdf'
    }
    
    all_installed = True
    for module_name, package_name in dependencies.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"✗ {package_name} is NOT installed")
            all_installed = False
    
    print()
    return all_installed


def check_modules():
    """Check if POC modules are available."""
    print("=" * 70)
    print("Checking POC Modules")
    print("=" * 70)
    
    modules_to_check = [
        'modules.types',
        'modules.llm',
        'modules.document_classifier',
        'modules.extractors',
        'modules.validators',
        'modules.workflows'
    ]
    
    all_available = True
    for module_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {module_name} is available")
        except ImportError as e:
            print(f"✗ {module_name} is NOT available: {e}")
            all_available = False
    
    print()
    return all_available


def check_sample_data():
    """Check for available sample data."""
    print("=" * 70)
    print("Checking Sample Data")
    print("=" * 70)
    
    samples_dir = Path(__file__).parent / 'invoices-sampels'
    
    if not samples_dir.exists():
        print(f"✗ Sample directory not found: {samples_dir}")
        return None
    
    pdf_files = list(samples_dir.glob("*.PDF"))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {samples_dir}")
        return None
    
    print(f"✓ Found {len(pdf_files)} sample PDF files")
    print(f"  Sample directory: {samples_dir}")
    print(f"  First sample: {pdf_files[0].name}")
    print()
    
    return pdf_files[0]


def run_basic_test():
    """Run a basic test without API key to verify module structure."""
    print("=" * 70)
    print("Running Basic Module Test")
    print("=" * 70)
    
    try:
        from modules.types import DocumentType
        
        # Test document types
        doc_types = [dt.value for dt in DocumentType]
        print(f"✓ Document types: {', '.join(doc_types)}")
        
        # Test that we can import workflows
        from modules.workflows import ExtractionWorkflow, ValidationWorkflow
        print(f"✓ Workflows imported successfully")
        
        print("\n✓ Basic module test passed!")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        print()
        return False


def run_full_test(pdf_path, ground_truth_path=None):
    """Run a full workflow test with API key."""
    print("=" * 70)
    print("Running Full Workflow Test")
    print("=" * 70)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("✗ GEMINI_API_KEY environment variable not set")
        print("\nTo run the full test, set your API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print()
        return False
    
    print(f"✓ API key found")
    print(f"✓ PDF file: {pdf_path}")
    
    if ground_truth_path:
        print(f"✓ Ground truth: {ground_truth_path}")
    
    print()
    
    try:
        # Import workflow
        from modules.workflows import ValidationWorkflow, ExtractionWorkflow
        import json
        
        # Load ground truth if provided
        ground_truth = None
        if ground_truth_path:
            with open(ground_truth_path, 'r') as f:
                ground_truth = json.load(f)
            print("Ground truth loaded successfully")
        
        # Create workflow
        if ground_truth:
            workflow = ValidationWorkflow(api_key)
            print("Using ValidationWorkflow (with ground truth)")
        else:
            workflow = ExtractionWorkflow(api_key)
            print("Using ExtractionWorkflow (extraction only)")
        
        print(f"\nProcessing: {Path(pdf_path).name}")
        print("-" * 70)
        
        # Process document
        if ground_truth:
            result = workflow.process_document(str(pdf_path), ground_truth)
        else:
            result = workflow.process_document(str(pdf_path))
        
        # Generate report
        report = workflow.generate_report(result)
        print(report)
        
        if result.success:
            print("\n✓ Full workflow test completed successfully!")
        else:
            print("\n✗ Workflow completed with errors")
        
        print()
        return result.success
        
    except Exception as e:
        print(f"\n✗ Full test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Minimal script to check and test the AI OCR POC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic check (no API key required)
  python run_workflow.py

  # Test with a sample PDF
  python run_workflow.py --pdf invoices-sampels/sample.PDF

  # Test with ground truth validation
  python run_workflow.py --pdf sample.PDF --ground-truth sample.json
        """
    )
    
    parser.add_argument(
        '--pdf',
        type=str,
        help='Path to PDF file to process'
    )
    
    parser.add_argument(
        '--ground-truth',
        type=str,
        help='Path to ground truth JSON file (optional)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("AI OCR POC - Minimal Check Script")
    print("=" * 70)
    print()
    
    # Step 1: Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print("⚠ Some dependencies are missing. Install them with:")
        print("  pip install -r requirements.txt")
        print()
    
    # Step 2: Check modules
    modules_ok = check_modules()
    if not modules_ok:
        print("⚠ Some modules are not available.")
        print("  Make sure you're running from the repository root.")
        return 1
    
    # Step 3: Run basic test
    basic_ok = run_basic_test()
    if not basic_ok:
        print("⚠ Basic test failed.")
        return 1
    
    # Step 4: Check sample data
    sample_pdf = check_sample_data()
    
    # Step 5: Run full test if PDF is provided or use sample
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"✗ PDF file not found: {pdf_path}")
            return 1
        
        gt_path = args.ground_truth
        if gt_path and not Path(gt_path).exists():
            print(f"✗ Ground truth file not found: {gt_path}")
            return 1
        
        full_ok = run_full_test(str(pdf_path), gt_path)
        return 0 if full_ok else 1
    
    elif sample_pdf and os.getenv('GEMINI_API_KEY'):
        print("=" * 70)
        print("API key detected - you can run a full test with a sample:")
        print("=" * 70)
        print(f"  python run_workflow.py --pdf {sample_pdf}")
        print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("✓ POC modules are properly installed and working")
    print("✓ Basic functionality check passed")
    
    if not os.getenv('GEMINI_API_KEY'):
        print("\nTo test with actual documents, set your API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
    
    print("\nFor full functionality, use:")
    print("  python main.py path/to/document.pdf")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
