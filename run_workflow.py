"""Run full workflow on a specific sample PDF."""
import os
from pathlib import Path
from modules.workflows import ExtractionWorkflow


def main():
    """Process a specific PDF through the full workflow."""
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: $env:GEMINI_API_KEY='your-api-key'")
        return 1
    
    # Define the PDF path
    pdf_path = Path(__file__).parent / "sampels" / "81124344_ORG_x9cp+3yx40mttjvnrwzffg00000000.PDF"
    
    # Validate PDF exists
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    print(f"Processing: {pdf_path.name}")
    print("-" * 70)
    
    # Create workflow and process document
    workflow = ExtractionWorkflow(api_key)
    result = workflow.process_document(str(pdf_path))
    
    # Generate and print report
    report = workflow.generate_report(result)
    print(report)
    
    # Save results
    output_path = pdf_path.parent / f"results_{pdf_path.stem}.json"
    
    import json
    from datetime import datetime
    
    # Convert result to dict for JSON serialization
    result_dict = {
        'pdf_path': result.pdf_path,
        'total_pages': result.total_pages,
        'success': result.success,
        'overall_score': result.overall_score,
        'timestamp': datetime.now().isoformat(),
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
        'errors': result.errors
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_path}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    exit(main())
