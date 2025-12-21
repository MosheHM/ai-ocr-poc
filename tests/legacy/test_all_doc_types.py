"""Test missing fields tracking for all document types."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.types import ExtractionResult, DocumentType
from modules.validators import PerformanceValidator


def test_all_document_types():
    """Test missing fields tracking for all document types."""
    validator = PerformanceValidator()
    all_passed = True
    
    # Test 1: Invoice
    print("\n1. Testing Invoice document type...")
    invoice_extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.INVOICE,
        data={"INVOICE_NO": "12345"},
        success=True
    )
    invoice_gt = {
        "INVOICE_NO": "12345",
        "INVOICE_DATE": "2025073000000000",
        "CURRENCY_ID": "EUR"
    }
    result = validator.validate(invoice_extraction, invoice_gt)
    expected_missing = ['INVOICE_DATE', 'CURRENCY_ID']
    for field in expected_missing:
        if field not in result.field_comparison or result.field_comparison[field]['extracted'] is not None:
            print(f"   ✗ FAIL: {field} should be tracked as missing")
            all_passed = False
    if all([field in result.field_comparison for field in expected_missing]):
        print(f"   ✓ PASS: Missing fields tracked correctly (score: {result.score:.1f}%)")
    
    # Test 2: OBL
    print("\n2. Testing OBL document type...")
    obl_extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.OBL,
        data={"CUSTOMER_NAME": "Test Corp"},
        success=True
    )
    obl_gt = {
        "CUSTOMER_NAME": "Test Corp",
        "WEIGHT": 500.0,
        "VOLUME": 10.5
    }
    result = validator.validate(obl_extraction, obl_gt)
    expected_missing = ['WEIGHT', 'VOLUME']
    for field in expected_missing:
        if field not in result.field_comparison or result.field_comparison[field]['extracted'] is not None:
            print(f"   ✗ FAIL: {field} should be tracked as missing")
            all_passed = False
    if all([field in result.field_comparison for field in expected_missing]):
        print(f"   ✓ PASS: Missing fields tracked correctly (score: {result.score:.1f}%)")
    
    # Test 3: HAWB
    print("\n3. Testing HAWB document type...")
    hawb_extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.HAWB,
        data={"CARRIER": "AirCo"},
        success=True
    )
    hawb_gt = {
        "CARRIER": "AirCo",
        "HAWB_NUMBER": "HAWB123",
        "PIECES": 10
    }
    result = validator.validate(hawb_extraction, hawb_gt)
    expected_missing = ['HAWB_NUMBER', 'PIECES']
    for field in expected_missing:
        if field not in result.field_comparison or result.field_comparison[field]['extracted'] is not None:
            print(f"   ✗ FAIL: {field} should be tracked as missing")
            all_passed = False
    if all([field in result.field_comparison for field in expected_missing]):
        print(f"   ✓ PASS: Missing fields tracked correctly (score: {result.score:.1f}%)")
    
    # Test 4: Packing List
    print("\n4. Testing Packing List document type...")
    pl_extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.PACKING_LIST,
        data={"PIECES": 100},
        success=True
    )
    pl_gt = {
        "PIECES": 100,
        "WEIGHT": 250.0,
        "CUSTOMER_NAME": ""  # Empty but should still be tracked
    }
    result = validator.validate(pl_extraction, pl_gt)
    expected_missing = ['WEIGHT', 'CUSTOMER_NAME']
    for field in expected_missing:
        if field not in result.field_comparison or result.field_comparison[field]['extracted'] is not None:
            print(f"   ✗ FAIL: {field} should be tracked as missing")
            all_passed = False
    if all([field in result.field_comparison for field in expected_missing]):
        print(f"   ✓ PASS: Missing fields tracked correctly (score: {result.score:.1f}%)")
        if result.field_comparison['CUSTOMER_NAME']['ground_truth'] == "":
            print(f"   ✓ PASS: Empty CUSTOMER_NAME field correctly tracked")
    
    return all_passed


def main():
    print("=" * 70)
    print("Missing Fields Tracking Test - All Document Types")
    print("=" * 70)
    
    result = test_all_document_types()
    
    print()
    print("=" * 70)
    if result:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
