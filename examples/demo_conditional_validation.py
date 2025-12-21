#!/usr/bin/env python3
"""Demonstration script showing conditional validation in action."""
import os
from pathlib import Path
from modules.workflows import ValidationWorkflow


def demonstrate_conditional_validation():
    """Demonstrate the conditional validation feature."""
    print("=" * 80)
    print("DEMONSTRATION: Conditional Validation Based on .txt Files")
    print("=" * 80)
    
    # Note: This will use dummy API key, so actual extraction will fail
    # But it will demonstrate the conditional logic perfectly
    api_key = os.getenv('GEMINI_API_KEY', 'demo-key')
    workflow = ValidationWorkflow(api_key)
    
    # Test files
    test_files = [
        {
            'path': 'sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF',
            'type': 'Invoice',
            'has_txt': True
        },
        {
            'path': 'sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF',
            'type': 'BOL',
            'has_txt': False
        },
        {
            'path': 'sampels/combined-sampels/81123758_SC_PACKING LIST_ddbh7b79suuww8wv+yzf7w00000000.PDF',
            'type': 'Packing List',
            'has_txt': False
        }
    ]
    
    results = []
    
    for test_file in test_files:
        if not Path(test_file['path']).exists():
            print(f"\n⚠ Test file not found: {test_file['path']}")
            continue
        
        print(f"\n{'-' * 80}")
        print(f"Processing: {test_file['type']}")
        print(f"File: {Path(test_file['path']).name}")
        print(f"Expected: {'Has .txt file' if test_file['has_txt'] else 'No .txt file'}")
        print(f"{'-' * 80}")
        
        # Process the document
        result = workflow.process_document(test_file['path'])
        
        # Check if skipped
        skipped = any("No .txt ground truth file" in err for err in result.errors)
        
        # Display results
        print(f"\nResult:")
        print(f"  Status: {'SKIPPED' if skipped else 'PROCESSED'}")
        print(f"  Success: {result.success}")
        print(f"  Total Pages: {result.total_pages}")
        print(f"  Classifications: {len(result.classifications)}")
        print(f"  Extractions: {len(result.extractions)}")
        print(f"  Validations: {len(result.validations)}")
        
        if result.errors:
            print(f"  Messages:")
            for error in result.errors:
                print(f"    - {error}")
        
        # Verify expected behavior
        if test_file['has_txt']:
            if not skipped:
                print("\n  ✓ CORRECT: Document with .txt file was processed")
            else:
                print("\n  ✗ ERROR: Document with .txt file was skipped!")
        else:
            if skipped:
                print("\n  ✓ CORRECT: Document without .txt file was skipped")
            else:
                print("\n  ✗ ERROR: Document without .txt file was processed!")
        
        results.append({
            'file': test_file['type'],
            'has_txt': test_file['has_txt'],
            'skipped': skipped,
            'correct': (test_file['has_txt'] and not skipped) or (not test_file['has_txt'] and skipped)
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for result in results:
        status = "✓ PASS" if result['correct'] else "✗ FAIL"
        action = "Processed" if not result['skipped'] else "Skipped"
        print(f"{status}: {result['file']:20s} - {action:10s} ({'Has .txt' if result['has_txt'] else 'No .txt'})")
    
    all_correct = all(r['correct'] for r in results)
    
    print("\n" + "=" * 80)
    if all_correct:
        print("✓ ALL TESTS PASSED - Conditional validation working correctly!")
    else:
        print("✗ SOME TESTS FAILED - Review implementation")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_conditional_validation()
