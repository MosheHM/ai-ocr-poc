"""
Example usage of the SplitDocumentValidator

This script demonstrates how to use the validator programmatically.
"""

import os
from pathlib import Path
from validate_split_docs import SplitDocumentValidator


def example_parse_single_org_file():
    """Example: Parse a single ORG XML file"""
    print("="*80)
    print("Example 1: Parse a single ORG XML file")
    print("="*80)
    
    # Create validator (no API key needed for parsing)
    validator = SplitDocumentValidator(api_key="dummy")
    
    # Find first ORG XML file
    samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
    org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
    
    if not org_xml_files:
        print("No ORG XML files found")
        return
    
    # Parse the XML
    org_xml_path = org_xml_files[0]
    result = validator.parse_org_xml(str(org_xml_path))
    
    print(f"\nORG File: {org_xml_path.name}")
    print(f"Parent ComId: {result['parent_com_id']}")
    print(f"Owner: {result['owner']}")
    print(f"User: {result['user']}")
    print(f"\nSplit Documents: {len(result['split_docs'])}")
    
    # Show details of first few split docs
    for i, split_doc in enumerate(result['split_docs'][:3], 1):
        print(f"\n  Split Doc {i}:")
        print(f"    Filing ComId: {split_doc['filing_com_id']}")
        print(f"    Type: {split_doc['doc_type_name']} ({split_doc['doc_type_code']})")
        print(f"    Pages: {split_doc['total_pages']}")
        if split_doc['pages']:
            page_nums = [p['page_num'] for p in split_doc['pages']]
            print(f"    Page numbers: {page_nums}")


def example_check_file_availability():
    """Example: Check which split document files are available"""
    print("\n" + "="*80)
    print("Example 2: Check file availability for split documents")
    print("="*80)
    
    validator = SplitDocumentValidator(api_key="dummy")
    
    samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
    split_docs_dir = Path(__file__).parent / 'sampels' / 'invoices-sampels'
    org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
    
    if not org_xml_files:
        print("No ORG XML files found")
        return
    
    # Parse first ORG file
    result = validator.parse_org_xml(str(org_xml_files[0]))
    
    print(f"\nChecking files for: {org_xml_files[0].name}")
    print(f"Total split documents: {len(result['split_docs'])}")
    
    pdf_count = 0
    xml_count = 0
    txt_count = 0
    
    for split_doc in result['split_docs']:
        filing_com_id = split_doc['filing_com_id']
        primary_num = split_doc['primary_num']
        
        base_filename = f"{primary_num}_SC_INVOICE_{filing_com_id}"
        pdf_path = split_docs_dir / f"{base_filename}.PDF"
        xml_path = split_docs_dir / f"{base_filename}.xml"
        txt_path = split_docs_dir / f"{base_filename}.txt"
        
        if pdf_path.exists():
            pdf_count += 1
        if xml_path.exists():
            xml_count += 1
        if txt_path.exists():
            txt_count += 1
    
    print(f"\nFile availability:")
    print(f"  PDFs found: {pdf_count}/{len(result['split_docs'])}")
    print(f"  XMLs found: {xml_count}/{len(result['split_docs'])}")
    print(f"  TXTs found: {txt_count}/{len(result['split_docs'])}")


def example_create_extraction_prompts():
    """Example: Create extraction prompts for different document types"""
    print("\n" + "="*80)
    print("Example 3: Create extraction prompts for different document types")
    print("="*80)
    
    validator = SplitDocumentValidator(api_key="dummy")
    
    doc_types = [
        "Supplier Invoice",
        "Packing List",
        "Bill of Lading"
    ]
    
    for doc_type in doc_types:
        print(f"\n{doc_type} Prompt Preview:")
        print("-" * 40)
        prompt = validator._create_extraction_prompt(doc_type)
        # Show first 200 characters
        print(prompt[:200] + "...")


def example_validate_without_api():
    """Example: Validate structure without calling API"""
    print("\n" + "="*80)
    print("Example 4: Validate XML structure and file paths")
    print("="*80)
    
    validator = SplitDocumentValidator(api_key="dummy")
    
    samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
    split_docs_dir = Path(__file__).parent / 'sampels' / 'invoices-sampels'
    org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
    
    if not org_xml_files:
        print("No ORG XML files found")
        return
    
    total_split_docs = 0
    total_pdf_found = 0
    total_with_multi_pages = 0
    
    for org_xml_path in org_xml_files[:2]:  # Process first 2 ORG files
        result = validator.parse_org_xml(str(org_xml_path))
        print(f"\n{org_xml_path.name}:")
        print(f"  Split documents: {len(result['split_docs'])}")
        
        total_split_docs += len(result['split_docs'])
        
        for split_doc in result['split_docs']:
            if split_doc['total_pages'] > 1:
                total_with_multi_pages += 1
            
            filing_com_id = split_doc['filing_com_id']
            primary_num = split_doc['primary_num']
            base_filename = f"{primary_num}_SC_INVOICE_{filing_com_id}"
            pdf_path = split_docs_dir / f"{base_filename}.PDF"
            
            if pdf_path.exists():
                total_pdf_found += 1
    
    print(f"\nSummary:")
    print(f"  Total split documents checked: {total_split_docs}")
    print(f"  PDFs found: {total_pdf_found}")
    print(f"  Multi-page documents: {total_with_multi_pages}")


def main():
    """Run all examples"""
    example_parse_single_org_file()
    example_check_file_availability()
    example_create_extraction_prompts()
    example_validate_without_api()
    
    print("\n" + "="*80)
    print("To run full validation with Gemini API:")
    print("  1. Set GEMINI_API_KEY environment variable")
    print("  2. Run: python validate_split_docs.py")
    print("="*80)


if __name__ == "__main__":
    main()
