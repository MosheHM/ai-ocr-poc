"""Validate PDF splitting against XML ground truth for combined samples."""
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from modules.workflows import SplittingValidationWorkflow


def find_matching_xml(pdf_path: Path, samples_dir: Path) -> Path:
    """Find the matching XML file for a PDF."""
    # Get the base name without extension
    pdf_stem = pdf_path.stem
    
    # Look for XML with same base name
    xml_path = samples_dir / f"{pdf_stem}.xml"
    
    if xml_path.exists():
        return xml_path
    
    raise FileNotFoundError(f"No matching XML found for {pdf_path.name}")


def validate_single_pdf(
    workflow: SplittingValidationWorkflow,
    pdf_path: Path,
    xml_path: Path,
    output_dir: Path
) -> dict:
    """
    Validate a single PDF against its XML ground truth.
    
    Returns:
        Dictionary with validation results
    """
    print(f"\nProcessing: {pdf_path.name}")
    print("-" * 80)
    
    # Process document with validation
    result = workflow.process_document_with_xml_ground_truth(
        str(pdf_path),
        str(xml_path)
    )
    
    # Check for errors
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return {
            'pdf': pdf_path.name,
            'xml': xml_path.name,
            'success': False,
            'error': result['error']
        }
    
    processing_result = result['processing_result']
    splitting_validation = result['splitting_validation']
    ground_truth = result['ground_truth']
    
    # Generate and print report
    report = workflow.generate_combined_report(
        processing_result,
        splitting_validation,
        ground_truth
    )
    print(report)
    
    # Save detailed results
    output_file = output_dir / f"validation_{pdf_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    result_dict = {
        'pdf_path': str(pdf_path),
        'xml_path': str(xml_path),
        'timestamp': datetime.now().isoformat(),
        'processing': {
            'total_pages': processing_result.total_pages,
            'success': processing_result.success,
            'total_documents': len(processing_result.document_instances),
            'documents': [
                {
                    'type': doc.document_type.value,
                    'pages': doc.page_numbers,
                    'page_range': doc.page_range
                }
                for doc in processing_result.document_instances
            ],
            'errors': processing_result.errors
        },
        'splitting_validation': splitting_validation.to_dict() if splitting_validation else None
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return {
        'pdf': pdf_path.name,
        'xml': xml_path.name,
        'success': True,
        'overall_score': splitting_validation.overall_score if splitting_validation else 0.0,
        'type_accuracy': splitting_validation.document_type_accuracy if splitting_validation else 0.0,
        'page_accuracy': splitting_validation.page_numbers_accuracy if splitting_validation else 0.0,
    }


def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate PDF splitting against XML ground truth"
    )
    parser.add_argument(
        '--samples-dir',
        type=str,
        default='sampels/combined-sampels',
        help='Directory containing PDF and XML samples (default: sampels/combined-sampels)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='validation_results',
        help='Directory to save validation results (default: validation_results)'
    )
    parser.add_argument(
        '--pdf',
        type=str,
        help='Specific PDF file to validate (if not provided, validates all PDFs in samples-dir)'
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        return 1
    
    # Setup paths
    samples_dir = Path(args.samples_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if not samples_dir.exists():
        print(f"Error: Samples directory not found: {samples_dir}")
        return 1
    
    # Create workflow
    workflow = SplittingValidationWorkflow(api_key)
    
    # Get PDFs to process
    if args.pdf:
        pdf_files = [Path(args.pdf)]
        if not pdf_files[0].exists():
            # Try relative to samples dir
            pdf_files = [samples_dir / args.pdf]
            if not pdf_files[0].exists():
                print(f"Error: PDF file not found: {args.pdf}")
                return 1
    else:
        pdf_files = sorted(samples_dir.glob("*.PDF"))
        if not pdf_files:
            print(f"No PDF files found in {samples_dir}")
            return 1
    
    print(f"Found {len(pdf_files)} PDF file(s) to validate")
    print("=" * 80)
    
    # Process each PDF
    results = []
    for pdf_path in pdf_files:
        try:
            # Find matching XML
            xml_path = find_matching_xml(pdf_path, samples_dir)
            
            # Validate
            result = validate_single_pdf(workflow, pdf_path, xml_path, output_dir)
            results.append(result)
            
        except FileNotFoundError as e:
            print(f"\nSkipping {pdf_path.name}: {e}")
            results.append({
                'pdf': pdf_path.name,
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            print(f"\nError processing {pdf_path.name}: {e}")
            results.append({
                'pdf': pdf_path.name,
                'success': False,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"\nTotal PDFs processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        avg_score = sum(r['overall_score'] for r in successful) / len(successful)
        avg_type_accuracy = sum(r['type_accuracy'] for r in successful) / len(successful)
        avg_page_accuracy = sum(r['page_accuracy'] for r in successful) / len(successful)
        
        print(f"\nAverage Overall Score: {avg_score:.1f}%")
        print(f"Average Type Accuracy: {avg_type_accuracy:.1f}%")
        print(f"Average Page Accuracy: {avg_page_accuracy:.1f}%")
        
        print("\nDetailed Results:")
        for r in successful:
            print(f"  {r['pdf']}: {r['overall_score']:.1f}% (Type: {r['type_accuracy']:.1f}%, Pages: {r['page_accuracy']:.1f}%)")
    
    if failed:
        print("\nFailed:")
        for r in failed:
            print(f"  {r['pdf']}: {r.get('error', 'Unknown error')}")
    
    # Save summary
    summary_file = output_dir / f"validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary saved to: {summary_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
