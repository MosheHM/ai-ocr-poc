"""Test the new missing fields tracking functionality in the validator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.types import ExtractionResult, DocumentType
from modules.validators import PerformanceValidator


def test_missing_fields_tracking():
    """Test that missing fields are tracked in validation."""
    print("Testing missing fields tracking...")
    
    validator = PerformanceValidator()
    
    # Create an extraction result for an Invoice that's missing some fields
    extraction = ExtractionResult(
        page_number=1,
        document_type=DocumentType.INVOICE,
        data={
            "INVOICE_NO": "12345",
            "INVOICE_AMOUNT": 1000.0,
            # Missing: INVOICE_DATE, CURRENCY_ID, INCOTERMS, CUSTOMER_ID
        },
        success=True
    )
    
    # Ground truth with all expected fields
    ground_truth = {
        "INVOICE_NO": "12345",
        "INVOICE_DATE": "2025073000000000",
        "INVOICE_AMOUNT": 1000.0,
        "CURRENCY_ID": "EUR",
        "INCOTERMS": "FCA",
        "CUSTOMER_ID": ""  # Empty field that should still be tracked
    }
    
    # Validate
    result = validator.validate(extraction, ground_truth)
    
    # Expected behavior:
    # - INVOICE_NO: correct (extracted correctly)
    # - INVOICE_AMOUNT: correct (extracted correctly)
    # - INVOICE_DATE: missing (not extracted, should be in field_comparison)
    # - CURRENCY_ID: missing (not extracted, should be in field_comparison)
    # - INCOTERMS: missing (not extracted, should be in field_comparison)
    # - CUSTOMER_ID: missing (not extracted, even though GT is empty, should be tracked)
    
    print(f"\nValidation Results:")
    print(f"  Total fields: {result.total_fields}")
    print(f"  Correct fields: {result.correct_fields}")
    print(f"  Score: {result.score:.2f}%")
    
    print(f"\nField Comparison:")
    for field_name, comparison in result.field_comparison.items():
        status = "✓" if comparison['correct'] else "✗"
        extracted = comparison['extracted']
        gt = comparison['ground_truth']
        if extracted is None:
            print(f"  {status} {field_name}: NOT EXTRACTED (GT: {repr(gt)})")
        else:
            print(f"  {status} {field_name}: {extracted} (GT: {gt})")
    
    # Verify the results
    expected_total_fields = 6  # All 6 invoice fields
    expected_correct_fields = 2  # Only INVOICE_NO and INVOICE_AMOUNT
    expected_score = (2 / 6) * 100  # ~33.33%
    
    success = True
    
    if result.total_fields != expected_total_fields:
        print(f"\n✗ FAIL: Expected {expected_total_fields} total fields, got {result.total_fields}")
        success = False
    
    if result.correct_fields != expected_correct_fields:
        print(f"\n✗ FAIL: Expected {expected_correct_fields} correct fields, got {result.correct_fields}")
        success = False
    
    if abs(result.score - expected_score) > 0.1:
        print(f"\n✗ FAIL: Expected score ~{expected_score:.2f}%, got {result.score:.2f}%")
        success = False
    
    # Check that missing fields are tracked
    missing_fields = ['INVOICE_DATE', 'CURRENCY_ID', 'INCOTERMS', 'CUSTOMER_ID']
    for field in missing_fields:
        if field not in result.field_comparison:
            print(f"\n✗ FAIL: Missing field '{field}' not tracked in field_comparison")
            success = False
        elif result.field_comparison[field]['extracted'] is not None:
            print(f"\n✗ FAIL: Field '{field}' should have extracted=None")
            success = False
        elif result.field_comparison[field]['correct'] is not False:
            print(f"\n✗ FAIL: Field '{field}' should have correct=False")
            success = False
    
    # Check that CUSTOMER_ID is tracked even though GT is empty
    if 'CUSTOMER_ID' in result.field_comparison:
        customer_id_comparison = result.field_comparison['CUSTOMER_ID']
        if customer_id_comparison['ground_truth'] == "" and customer_id_comparison['extracted'] is None:
            print(f"\n✓ PASS: Empty CUSTOMER_ID field is correctly tracked as missing")
        else:
            print(f"\n✗ FAIL: CUSTOMER_ID tracking issue")
            success = False
    
    if success:
        print(f"\n✓ PASS: All missing fields tracking tests passed!")
    
    return success


def main():
    print("=" * 70)
    print("Missing Fields Tracking Test")
    print("=" * 70)
    print()
    
    result = test_missing_fields_tracking()
    
    print()
    print("=" * 70)
    if result:
        print("✓ TEST PASSED")
        return 0
    else:
        print("✗ TEST FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
