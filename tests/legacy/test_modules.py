"""
Simple test script to verify the modular system works correctly.
This tests the basic functionality without requiring an actual API key.
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from modules.types import DocumentType, ProcessingResult
        from modules.llm.client import GeminiLLMClient
        from modules.document_classifier import PDFDocumentClassifier
        from modules.extractors import ExtractorFactory
        from modules.validators import PerformanceValidator
        from modules.workflow import DocumentProcessor
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_document_types():
    """Test document type enum."""
    print("\nTesting document types...")
    from modules.types import DocumentType
    
    expected_types = ['Invoice', 'OBL', 'HAWB', 'Packing List', 'Unknown']
    actual_types = [dt.value for dt in DocumentType]
    
    if actual_types == expected_types:
        print(f"✓ Document types correct: {actual_types}")
        return True
    else:
        print(f"✗ Document types mismatch")
        print(f"  Expected: {expected_types}")
        print(f"  Got: {actual_types}")
        return False


def test_schemas():
    """Test that schemas are defined for all document types."""
    print("\nTesting schemas...")
    from modules.types import DocumentType, DOCUMENT_SCHEMAS
    
    all_valid = True
    for doc_type in [DocumentType.INVOICE, DocumentType.OBL, 
                     DocumentType.HAWB, DocumentType.PACKING_LIST]:
        if doc_type in DOCUMENT_SCHEMAS:
            schema = DOCUMENT_SCHEMAS[doc_type]
            print(f"✓ {doc_type.value} schema: {len(schema)} fields")
        else:
            print(f"✗ {doc_type.value} schema missing")
            all_valid = False
    
    return all_valid


def test_extractor_factory():
    """Test that extractors can be created for all types."""
    print("\nTesting extractor factory...")
    from modules.types import DocumentType
    from modules.extractors import ExtractorFactory
    
    # Create a mock LLM client
    class MockLLMClient:
        def generate_json_content(self, **kwargs):
            return {}
    
    mock_client = MockLLMClient()
    all_valid = True
    
    for doc_type in [DocumentType.INVOICE, DocumentType.OBL,
                     DocumentType.HAWB, DocumentType.PACKING_LIST]:
        try:
            extractor = ExtractorFactory.create_extractor(doc_type, mock_client)
            print(f"✓ {doc_type.value} extractor created: {extractor.__class__.__name__}")
        except Exception as e:
            print(f"✗ {doc_type.value} extractor failed: {e}")
            all_valid = False
    
    return all_valid


def test_validator():
    """Test the validator with sample data."""
    print("\nTesting validator...")
    from modules.types import ExtractionResult, DocumentType
    from modules.validators import PerformanceValidator
    
    validator = PerformanceValidator()
    
    # Create sample extraction result
    extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.INVOICE,
        data={
            "INVOICE_NO": "12345",
            "INVOICE_AMOUNT": 1000.0,
            "CURRENCY_ID": "USD"
        },
        success=True
    )
    
    # Create ground truth
    ground_truth = {
        "INVOICE_NO": "12345",
        "INVOICE_AMOUNT": 1000.0,
        "CURRENCY_ID": "EUR"  # Intentional mismatch
    }
    
    # Validate
    result = validator.validate(extraction, ground_truth)
    
    expected_score = 66.67  # 2 out of 3 correct
    if abs(result.score - expected_score) < 0.1:
        print(f"✓ Validator score correct: {result.score:.2f}%")
        print(f"  {result.correct_fields}/{result.total_fields} fields correct")
        return True
    else:
        print(f"✗ Validator score incorrect: {result.score:.2f}% (expected ~{expected_score}%)")
        return False


def test_pdf_utils():
    """Test PDF utility functions (without actual PDFs)."""
    print("\nTesting PDF utils...")
    from modules.utils import split_pdf_to_pages, get_pdf_page_count
    
    # These functions have fallback behavior when PDF libraries aren't available
    # or when files don't exist
    print("✓ PDF utilities imported successfully")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("AI OCR POC - Module Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_document_types,
        test_schemas,
        test_extractor_factory,
        test_validator,
        test_pdf_utils
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
