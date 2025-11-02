"""
Validation Script for Split Documents

This script processes ORG (original) files and validates the document splitting:
1. Parses XML files to extract split document metadata
2. Sends each split PDF to Gemini for extraction
3. Validates splitting correctness (pages, document types)
4. Validates extracted data against .txt files (if available)
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from google import genai
from google.genai import types


class SplitDocumentValidator:
    """Validates split documents against XML metadata and Gemini extraction"""
    
    def __init__(self, api_key: str):
        self.client: genai.Client = genai.Client(api_key=api_key)
    
    def parse_org_xml(self, xml_path: str) -> Dict:
        """Parse ORG XML file to extract split document information"""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        result = {
            'parent_com_id': None,
            'owner': None,
            'user': None,
            'file_path': None,
            'split_docs': []
        }
        
        # Extract parent info
        parent_com_id = root.find('ParentComId')
        if parent_com_id is not None:
            result['parent_com_id'] = parent_com_id.text
        
        owner = root.find('Owner')
        if owner is not None:
            result['owner'] = owner.text
        
        user = root.find('User')
        if user is not None:
            result['user'] = user.text
        
        file_path = root.find('FilePath')
        if file_path is not None:
            result['file_path'] = file_path.text
        
        # Extract split documents
        splitted_docs = root.find('SplittedDocs')
        if splitted_docs is not None:
            for split_doc in splitted_docs.findall('SplitDoc'):
                doc_info = self._parse_split_doc(split_doc)
                result['split_docs'].append(doc_info)
        
        return result
    
    def _parse_split_doc(self, split_doc_elem) -> Dict:
        """Parse individual SplitDoc element"""
        doc_info = {
            'entname': None,
            'primary_num': None,
            'doc_type': None,
            'doc_type_code': None,
            'doc_type_name': None,
            'filing_com_id': None,
            'filing_file_ref': None,
            'filing_desc': None,
            'pages': [],
            'total_pages': 0
        }
        
        # Extract basic info
        entname = split_doc_elem.find('Entname')
        if entname is not None:
            doc_info['entname'] = entname.text
        
        primary_num = split_doc_elem.find('PrimaryNum')
        if primary_num is not None:
            doc_info['primary_num'] = primary_num.text
        
        doc_type = split_doc_elem.find('DocType')
        if doc_type is not None:
            doc_info['doc_type'] = doc_type.text
        
        doc_type_code = split_doc_elem.find('FilingDocTypeCode')
        if doc_type_code is not None:
            doc_info['doc_type_code'] = doc_type_code.text
        
        doc_type_name = split_doc_elem.find('FilingDocTypeName')
        if doc_type_name is not None:
            doc_info['doc_type_name'] = doc_type_name.text
        
        filing_com_id = split_doc_elem.find('FilingComId')
        if filing_com_id is not None:
            doc_info['filing_com_id'] = filing_com_id.text
        
        filing_file_ref = split_doc_elem.find('FilingFileRef')
        if filing_file_ref is not None:
            doc_info['filing_file_ref'] = filing_file_ref.text
        
        filing_desc = split_doc_elem.find('FilingDesc')
        if filing_desc is not None:
            doc_info['filing_desc'] = filing_desc.text
        
        # Extract pages
        pages_elem = split_doc_elem.find('Pages')
        if pages_elem is not None:
            for page_elem in pages_elem.findall('Page'):
                page_num_elem = page_elem.find('PageNum')
                rotate_elem = page_elem.find('Rotate')
                
                page_info = {
                    'page_num': int(page_num_elem.text) if page_num_elem is not None else None,
                    'rotate': int(rotate_elem.text) if rotate_elem is not None else 0
                }
                doc_info['pages'].append(page_info)
            
            doc_info['total_pages'] = len(doc_info['pages'])
        
        return doc_info
    
    def extract_from_pdf(self, pdf_path: str, doc_type_name: str) -> Dict:
        """Extract data from PDF using Gemini API"""
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Create prompt based on document type
        prompt = self._create_extraction_prompt(doc_type_name)
        
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=pdf_data,
                            mime_type="application/pdf"
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        
        result_text = response.text.strip()
        
        # Remove markdown code blocks if present
        result_text = self._remove_code_blocks(result_text)
        
        try:
            return json.loads(result_text)
        except json.JSONDecodeError as e:
            return {
                'error': f'Failed to parse JSON: {e}',
                'raw_response': result_text
            }
    
    def _create_extraction_prompt(self, doc_type_name: str) -> str:
        """Create extraction prompt based on document type"""
        if 'Invoice' in doc_type_name or 'INVOICE' in doc_type_name:
            return """You are an AI assistant specialized in extracting structured data from invoices.

Extract the following fields from the invoice and return them as a JSON object:

REQUIRED RETURN FIELDS AND FORMATS:
- INVOICE_NO: Extract as-is, preserving all characters
- INVOICE_DATE: Format as YYYYMMDDHHMMSSSS (16 digits)
- CURRENCY_ID: 3-letter currency code in uppercase
- INCOTERMS: INCOTERMS code in uppercase (code only, no location)
- INVOICE_AMOUNT: number (integer or float) without currency symbols
- CUSTOMER_ID: Extract as-is
- DOC_TYPE: Document type code (e.g., "SC_INVOICE", "FSI")
- TOTAL_PAGES: Total number of pages in the document (integer)

Return ONLY valid JSON with these exact field names. If a field is not found, omit it.

Example:
{
    "INVOICE_NO": "0004833/E",
    "INVOICE_DATE": "2025073000000000",
    "CURRENCY_ID": "EUR",
    "INCOTERMS": "FCA",
    "INVOICE_AMOUNT": 7632.00,
    "CUSTOMER_ID": "D004345",
    "DOC_TYPE": "SC_INVOICE",
    "TOTAL_PAGES": 1
}
"""
        elif 'Packing List' in doc_type_name or 'PACKING' in doc_type_name:
            return """You are an AI assistant specialized in extracting structured data from packing lists.

Extract the following fields from the packing list and return them as a JSON object:

REQUIRED RETURN FIELDS:
- CUSTOMER_NAME: Customer name
- PIECES: Number of pieces/packages
- WEIGHT: Total weight
- DOC_TYPE: "PACKING_LIST" or "FPL"
- TOTAL_PAGES: Total number of pages in the document

Return ONLY valid JSON. If a field is not found, omit it.

Example:
{
    "CUSTOMER_NAME": "ABC Company",
    "PIECES": 100,
    "WEIGHT": 1500.5,
    "DOC_TYPE": "PACKING_LIST",
    "TOTAL_PAGES": 1
}
"""
        else:
            # Generic extraction for other document types
            return f"""Extract structured data from this {doc_type_name} document.

Return the data as a JSON object with appropriate field names.
Include a TOTAL_PAGES field with the number of pages in the document.

Return ONLY valid JSON.
"""
    
    def _remove_code_blocks(self, text: str) -> str:
        """Remove markdown code blocks from text"""
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    def load_txt_file(self, txt_path: str) -> Optional[Dict]:
        """Load extracted data from TXT file (JSON format)"""
        if not os.path.exists(txt_path):
            return None
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle OCC wrapper
            if 'OCC' in data:
                return data['OCC']
            return data
        except Exception as e:
            print(f"  Warning: Failed to load {txt_path}: {e}")
            return None
    
    def validate_split_doc(self, split_doc_info: Dict, pdf_path: str, txt_path: Optional[str], 
                          samples_dir: Path, split_docs_dir: Path) -> Dict:
        """Validate a single split document"""
        validation_result = {
            'filing_com_id': split_doc_info['filing_com_id'],
            'doc_type_name': split_doc_info['doc_type_name'],
            'xml_metadata': split_doc_info,
            'pdf_path': str(pdf_path),
            'txt_path': str(txt_path) if txt_path else None,
            'pdf_exists': os.path.exists(pdf_path),
            'txt_exists': txt_path and os.path.exists(txt_path),
            'extraction_result': None,
            'txt_data': None,
            'validations': {
                'pages_match': None,
                'doc_type_match': None,
                'txt_data_match': None
            },
            'errors': []
        }
        
        # Check if PDF exists
        if not validation_result['pdf_exists']:
            validation_result['errors'].append(f"PDF file not found: {pdf_path}")
            return validation_result
        
        # Extract data from PDF
        try:
            extraction_result = self.extract_from_pdf(str(pdf_path), split_doc_info['doc_type_name'])
            validation_result['extraction_result'] = extraction_result
            
            # Validate pages
            xml_pages = split_doc_info['total_pages']
            extracted_pages = extraction_result.get('TOTAL_PAGES')
            if extracted_pages is not None:
                validation_result['validations']['pages_match'] = (xml_pages == extracted_pages)
                if not validation_result['validations']['pages_match']:
                    validation_result['errors'].append(
                        f"Page count mismatch: XML={xml_pages}, Gemini={extracted_pages}"
                    )
            else:
                validation_result['errors'].append("TOTAL_PAGES not found in extraction result")
            
            # Validate document type
            doc_type_code = split_doc_info['doc_type_code']
            extracted_doc_type = extraction_result.get('DOC_TYPE')
            if extracted_doc_type:
                # Check if codes match (e.g., FSI should match FSI or SC_INVOICE)
                validation_result['validations']['doc_type_match'] = (
                    doc_type_code == extracted_doc_type or 
                    doc_type_code in extracted_doc_type or 
                    extracted_doc_type in doc_type_code
                )
                if not validation_result['validations']['doc_type_match']:
                    validation_result['errors'].append(
                        f"Doc type mismatch: XML={doc_type_code}, Gemini={extracted_doc_type}"
                    )
            
        except Exception as e:
            validation_result['errors'].append(f"Extraction failed: {e}")
            return validation_result
        
        # Load and validate against TXT file
        if validation_result['txt_exists']:
            txt_data = self.load_txt_file(txt_path)
            validation_result['txt_data'] = txt_data
            
            if txt_data:
                # Compare extracted data with txt data
                mismatches = []
                for key in txt_data:
                    if key in extraction_result:
                        if txt_data[key] != extraction_result[key]:
                            mismatches.append({
                                'field': key,
                                'txt_value': txt_data[key],
                                'extracted_value': extraction_result[key]
                            })
                
                validation_result['validations']['txt_data_match'] = len(mismatches) == 0
                if mismatches:
                    validation_result['txt_data_mismatches'] = mismatches
        
        return validation_result
    
    def process_org_file(self, org_xml_path: Path, samples_dir: Path, split_docs_dir: Path) -> Dict:
        """Process a single ORG file and validate all its split documents"""
        print(f"\nProcessing ORG file: {org_xml_path.name}")
        
        result = {
            'org_xml_path': str(org_xml_path),
            'org_metadata': None,
            'split_doc_validations': [],
            'summary': {
                'total_split_docs': 0,
                'pdf_found': 0,
                'txt_found': 0,
                'pages_match': 0,
                'doc_type_match': 0,
                'txt_data_match': 0,
                'errors': 0
            }
        }
        
        # Parse ORG XML
        try:
            org_metadata = self.parse_org_xml(str(org_xml_path))
            result['org_metadata'] = org_metadata
            
            print(f"  Parent ComId: {org_metadata['parent_com_id']}")
            print(f"  Total split documents: {len(org_metadata['split_docs'])}")
            
            result['summary']['total_split_docs'] = len(org_metadata['split_docs'])
            
            # Process each split document
            for split_doc in org_metadata['split_docs']:
                filing_com_id = split_doc['filing_com_id']
                primary_num = split_doc['primary_num']
                doc_type_name = split_doc['doc_type_name']
                
                print(f"\n  Split Doc: {filing_com_id}")
                print(f"    Type: {doc_type_name}")
                print(f"    Pages: {split_doc['total_pages']}")
                
                # Construct file paths
                # Pattern: {primary_num}_SC_INVOICE_{filing_com_id}.PDF
                base_filename = f"{primary_num}_SC_INVOICE_{filing_com_id}"
                pdf_path = split_docs_dir / f"{base_filename}.PDF"
                txt_path = split_docs_dir / f"{base_filename}.txt"
                
                # Validate the split document
                validation = self.validate_split_doc(
                    split_doc, pdf_path, txt_path if txt_path.exists() else None, samples_dir, split_docs_dir
                )
                
                result['split_doc_validations'].append(validation)
                
                # Update summary
                if validation['pdf_exists']:
                    result['summary']['pdf_found'] += 1
                if validation['txt_exists']:
                    result['summary']['txt_found'] += 1
                if validation['validations']['pages_match']:
                    result['summary']['pages_match'] += 1
                if validation['validations']['doc_type_match']:
                    result['summary']['doc_type_match'] += 1
                if validation['validations']['txt_data_match']:
                    result['summary']['txt_data_match'] += 1
                if validation['errors']:
                    result['summary']['errors'] += len(validation['errors'])
                
                # Print validation results
                print(f"    PDF found: {'✓' if validation['pdf_exists'] else '✗'}")
                print(f"    TXT found: {'✓' if validation['txt_exists'] else '✗'}")
                if validation['validations']['pages_match'] is not None:
                    print(f"    Pages match: {'✓' if validation['validations']['pages_match'] else '✗'}")
                if validation['validations']['doc_type_match'] is not None:
                    print(f"    Doc type match: {'✓' if validation['validations']['doc_type_match'] else '✗'}")
                if validation['validations']['txt_data_match'] is not None:
                    print(f"    TXT data match: {'✓' if validation['validations']['txt_data_match'] else '✗'}")
                
                for error in validation['errors']:
                    print(f"    ERROR: {error}")
        
        except Exception as e:
            result['error'] = str(e)
            print(f"  ERROR processing ORG file: {e}")
        
        return result
    
    def process_all_org_files(self, samples_dir: Path, split_docs_dir: Path) -> Dict:
        """Process all ORG files in the samples directory"""
        # Find all ORG XML files
        org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
        
        print(f"Found {len(org_xml_files)} ORG XML files")
        
        all_results = {
            'total_org_files': len(org_xml_files),
            'org_file_results': [],
            'overall_summary': {
                'total_split_docs': 0,
                'pdf_found': 0,
                'txt_found': 0,
                'pages_match': 0,
                'doc_type_match': 0,
                'txt_data_match': 0,
                'errors': 0
            }
        }
        
        for org_xml_path in org_xml_files:
            result = self.process_org_file(org_xml_path, samples_dir, split_docs_dir)
            all_results['org_file_results'].append(result)
            
            # Update overall summary
            summary = result.get('summary', {})
            all_results['overall_summary']['total_split_docs'] += summary.get('total_split_docs', 0)
            all_results['overall_summary']['pdf_found'] += summary.get('pdf_found', 0)
            all_results['overall_summary']['txt_found'] += summary.get('txt_found', 0)
            all_results['overall_summary']['pages_match'] += summary.get('pages_match', 0)
            all_results['overall_summary']['doc_type_match'] += summary.get('doc_type_match', 0)
            all_results['overall_summary']['txt_data_match'] += summary.get('txt_data_match', 0)
            all_results['overall_summary']['errors'] += summary.get('errors', 0)
        
        return all_results


def main():
    """Main entry point"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: export GEMINI_API_KEY='your-api-key'")
        return
    
    validator = SplitDocumentValidator(api_key)
    
    # Process combined-sampels directory (has ORG files)
    samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
    # Split documents are in combined-sampels directory
    split_docs_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'

    if not samples_dir.exists():
        print(f"Error: Samples directory not found: {samples_dir}")
        return
    
    if not split_docs_dir.exists():
        print(f"Error: Split docs directory not found: {split_docs_dir}")
        return
    
    # Process all ORG files
    results = validator.process_all_org_files(samples_dir, split_docs_dir)
    
    # Save results
    output_file = Path(__file__).parent / 'split_doc_validation_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    summary = results['overall_summary']
    print(f"Total ORG files processed: {results['total_org_files']}")
    print(f"Total split documents: {summary['total_split_docs']}")
    print(f"PDFs found: {summary['pdf_found']}/{summary['total_split_docs']}")
    print(f"TXT files found: {summary['txt_found']}/{summary['total_split_docs']}")
    print(f"Pages match: {summary['pages_match']}/{summary['total_split_docs']}")
    print(f"Doc types match: {summary['doc_type_match']}/{summary['total_split_docs']}")
    print(f"TXT data match: {summary['txt_data_match']}/{summary['txt_found']}")
    print(f"Total errors: {summary['errors']}")
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
