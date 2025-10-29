"""Main entry point for the modular AI OCR POC application."""
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from modules.workflows import ExtractionWorkflow, ValidationWorkflow


def main():
    """Main function for processing documents."""
    parser = argparse.ArgumentParser(
        description="AI OCR POC - Multi-document type extractor"
    )
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to the PDF file to process'
    )
    parser.add_argument(
        '--ground-truth',
        type=str,
        help='Path to ground truth JSON file for validation (optional)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save results JSON file (optional)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        return 1
    
    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    # Load ground truth if provided
    ground_truth = None
    if args.ground_truth:
        gt_path = Path(args.ground_truth)
        if not gt_path.exists():
            print(f"Warning: Ground truth file not found: {gt_path}")
        else:
            try:
                with open(gt_path, 'r', encoding='utf-8') as f:
                    ground_truth = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load ground truth: {e}")
    
    # Choose workflow based on whether ground truth is provided
    if ground_truth:
        # Use validation workflow
        workflow = ValidationWorkflow(api_key)
        result = workflow.process_document(str(pdf_path), ground_truth)
    else:
        # Use extraction-only workflow (faster, for daily use)
        workflow = ExtractionWorkflow(api_key)
        result = workflow.process_document(str(pdf_path))
    
    # Generate and print report
    report = workflow.generate_report(result)
    print(report)
    
    # Save results if output path specified
    if args.output:
        output_path = Path(args.output)
    else:
        # Default output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = pdf_path.parent / f"results_{pdf_path.stem}_{timestamp}.json"
    
    try:
        # Convert result to dict for JSON serialization
        result_dict = {
            'pdf_path': result.pdf_path,
            'total_pages': result.total_pages,
            'success': result.success,
            'overall_score': result.overall_score,
            'classifications': [
                {
                    'page_number': c.page_number,
                    'document_type': c.document_type.value,
                    'confidence': c.confidence
                }
                for c in result.classifications
            ],
            'extractions': [
                {
                    'page_number': e.page_number,
                    'document_type': e.document_type.value,
                    'data': e.data,
                    'success': e.success,
                    'error_message': e.error_message
                }
                for e in result.extractions
            ],
            'validations': [
                {
                    'page_number': v.page_number,
                    'document_type': v.document_type.value,
                    'score': v.score,
                    'correct_fields': v.correct_fields,
                    'total_fields': v.total_fields,
                    'field_comparison': v.field_comparison
                }
                for v in result.validations
            ] if result.validations else [],
            'errors': result.errors
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_path}")
    
    except Exception as e:
        print(f"Warning: Failed to save results: {e}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    exit(main())
