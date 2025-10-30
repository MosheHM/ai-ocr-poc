"""
Example script showing how to use the AI OCR POC programmatically.

This demonstrates the main API and workflow without requiring actual PDFs or API keys.
"""
import json
from modules.types import DocumentType, ExtractionResult, ValidationResult
from modules.validators import PerformanceValidator


def example_classification_workflow():
    """Example showing how the classification workflow works."""
    print("=" * 70)
    print("Example 1: Document Classification Workflow")
    print("=" * 70)
    
    print("\nStep 1: Multi-page PDF is loaded")
    print("  PDF: shipment_documents.pdf (3 pages)")
    
    print("\nStep 2: Each page is classified")
    classifications = [
        {"page": 1, "type": "Invoice", "confidence": 0.98},
        {"page": 2, "type": "Packing List", "confidence": 0.95},
        {"page": 3, "type": "OBL", "confidence": 0.92},
    ]
    
    for cls in classifications:
        print(f"  Page {cls['page']}: {cls['type']} (confidence: {cls['confidence']:.2f})")
    
    print("\nStep 3: Type-specific extractors are used for each page")
    print("  Page 1 → InvoiceExtractor")
    print("  Page 2 → PackingListExtractor")
    print("  Page 3 → OBLExtractor")


def example_extraction_schemas():
    """Example showing the different extraction schemas."""
    print("\n" + "=" * 70)
    print("Example 2: Document Type Schemas")
    print("=" * 70)
    
    schemas = {
        "Invoice": {
            "INVOICE_NO": "0004833/E",
            "INVOICE_DATE": "2025073000000000",
            "CURRENCY_ID": "EUR",
            "INCOTERMS": "FCA",
            "INVOICE_AMOUNT": 7632.00,
            "CUSTOMER_ID": "D004345"
        },
        "OBL": {
            "CUSTOMER_NAME": "ABC Shipping Ltd",
            "WEIGHT": 1500.5,
            "VOLUME": 45.2,
            "INCOTERMS": "FOB"
        },
        "HAWB": {
            "CUSTOMER_NAME": "XYZ Logistics",
            "CURRENCY": "USD",
            "CARRIER": "Air Freight Co",
            "HAWB_NUMBER": "HAWB-2025-001234",
            "PIECES": 25,
            "WEIGHT": 450.5
        },
        "Packing List": {
            "CUSTOMER_NAME": "DEF Manufacturing",
            "PIECES": 100,
            "WEIGHT": 2500.0
        }
    }
    
    for doc_type, schema in schemas.items():
        print(f"\n{doc_type}:")
        print(json.dumps(schema, indent=2))


def example_validation():
    """Example showing validation against ground truth."""
    print("\n" + "=" * 70)
    print("Example 3: Validation Against Ground Truth")
    print("=" * 70)
    
    # Create sample extraction with some missing fields
    extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.INVOICE,
        data={
            "INVOICE_NO": "0004833/E",
            "INVOICE_DATE": "2025073000000000",
            "CURRENCY_ID": "EUR",
            "INCOTERMS": "FCA",
            "INVOICE_AMOUNT": 7632.00,
            # CUSTOMER_ID is missing - will be tracked
        },
        success=True
    )
    
    # Ground truth with one intentional error and missing field
    ground_truth = {
        "INVOICE_NO": "0004833/E",
        "INVOICE_DATE": "2025073000000000",
        "CURRENCY_ID": "EUR",
        "INCOTERMS": "FOB",  # Different from extracted
        "INVOICE_AMOUNT": 7632.00,
        "CUSTOMER_ID": "D004345"  # Missing from extraction
    }
    
    # Validate
    validator = PerformanceValidator()
    result = validator.validate(extraction, ground_truth)
    
    print(f"\nExtracted Fields: {len(extraction.data)}")
    print(f"Validation Score: {result.score:.2f}%")
    print(f"Correct Fields: {result.correct_fields}/{result.total_fields}")
    
    print("\nField-by-field comparison:")
    for field, comparison in result.field_comparison.items():
        status = "✓" if comparison['correct'] else "✗"
        extracted = comparison['extracted']
        expected = comparison['ground_truth']
        
        if extracted is None:
            # Field was not extracted
            print(f"  {status} {field}: NOT EXTRACTED (expected: {expected})")
        elif comparison['correct']:
            print(f"  {status} {field}: {extracted}")
        else:
            print(f"  {status} {field}: {extracted} (expected: {expected})")
    
    print("\n📝 Note: Missing fields are now tracked even when not extracted,")
    print("   making model blind spots visible for better performance assessment.")


def example_error_handling():
    """Example showing error handling."""
    print("\n" + "=" * 70)
    print("Example 4: Error Handling")
    print("=" * 70)
    
    scenarios = [
        {
            "scenario": "Unknown Document Type",
            "action": "Page is marked as 'Unknown' and skipped for extraction",
            "feedback": "Warning: Page 2 classified as Unknown (confidence: 0.45)"
        },
        {
            "scenario": "Extraction Failure",
            "action": "Error is logged, extraction marked as failed",
            "feedback": "Error: Failed to extract data from page 3 - Invalid JSON response"
        },
        {
            "scenario": "Missing Ground Truth Field",
            "action": "Field is not validated, only extracted fields are compared",
            "feedback": "Info: Field 'EXTRA_FIELD' in extracted data not in ground truth"
        },
        {
            "scenario": "API Rate Limit",
            "action": "Processing halts, partial results are saved",
            "feedback": "Error: API rate limit exceeded - Results saved for 2/5 pages"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['scenario']}")
        print(f"  Action: {scenario['action']}")
        print(f"  Feedback: {scenario['feedback']}")


def example_usage_commands():
    """Example showing command-line usage."""
    print("\n" + "=" * 70)
    print("Example 5: Command-Line Usage")
    print("=" * 70)
    
    examples = [
        {
            "description": "Process a single PDF",
            "command": "python main.py documents/shipment_2025.pdf"
        },
        {
            "description": "Process with validation",
            "command": "python main.py documents/invoice.pdf --ground-truth data/invoice_gt.json"
        },
        {
            "description": "Save results to specific file",
            "command": "python main.py documents/mixed.pdf --output results/mixed_results.json"
        },
        {
            "description": "Verbose output",
            "command": "python main.py documents/package.pdf --verbose"
        }
    ]
    
    for example in examples:
        print(f"\n{example['description']}:")
        print(f"  $ {example['command']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("AI OCR POC - Usage Examples")
    print("=" * 70)
    
    example_classification_workflow()
    example_extraction_schemas()
    example_validation()
    example_error_handling()
    example_usage_commands()
    
    print("\n" + "=" * 70)
    print("For more information, see README.md and ARCHITECTURE.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
