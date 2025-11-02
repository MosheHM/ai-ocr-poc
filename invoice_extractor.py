import time
import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an AI assistant specialized in extracting structured data from invoices.

Extract the following fields from the invoice and return them as a JSON object:

REQUIRED RETURN FIELDS AND FORMATS:
- INVOICE_NO: Extract as-is, preserving all characters including slashes (e.g., "0004833/E", "INV-25-0026439")
- INVOICE_DATE: Format as YYYYMMDDHHMMSSSS (16 digits)
  * Convert any date format to: YYYYMMDD00000000
  * Example: "30.07.2025" becomes "2025073000000000"
- CURRENCY_ID: 3-letter currency code in uppercase (e.g., "EUR", "USD", "GBP")
- INCOTERMS: INCOTERMS code in uppercase (e.g., "FCA", "FOB", "CIF", "EXW")
  * Do NOT include location details or additional text
- INVOICE_AMOUNT: number (integer or float) without currency symbols
- CUSTOMER_ID: Extract as-is (e.g., "D004345")
- DOC_TYPE: Document type code (e.g., "SC_INVOICE", "INV")
- TOTAL_PAGES: Total number of pages in the document (integer)

CRITICAL FORMAT RULES:
1. INVOICE_DATE must be exactly 16 digits: YYYYMMDD00000000
2. INCOTERMS must be ONLY the code (3 letters usually), no location or extra text
3. INVOICE_AMOUNT must be a number type, not a string
4. TOTAL_PAGES must be an integer (count the pages in the document)
5. DOC_TYPE should reflect that this is an invoice document
6. Preserve exact formatting for INVOICE_NO (keep slashes, dashes, etc.)
7. Return ONLY valid JSON with these exact field names
8. If a field is not found, omit it from the response

Example output format:
{
    "INVOICE_NO": "0004833/E",
    "INVOICE_DATE": "2025073000000000",
    "CURRENCY_ID": "EUR",
    "INCOTERMS": "FCA",
    "INVOICE_AMOUNT": 7632.00,
    "CUSTOMER_ID": "D004345",
    "DOC_TYPE": "SC_INVOICE",
    "TOTAL_PAGES": 2
}
"""


class InvoiceExtractor:
    def __init__(self, api_key: str):
        self.client: genai.Client = genai.Client(api_key=api_key)

    def extract_from_pdf(self, pdf_path: str) -> dict:
        """Extract invoice data from PDF using Gemini API"""
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
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
                        types.Part.from_text(text=SYSTEM_PROMPT)
                    ]
                )
            ]
        )
        
        result_text = response.text.strip()
        
        def remove_code_blocks(text: str) -> str:
            """Remove markdown code blocks from text"""
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return text.strip()

        return json.loads(remove_code_blocks(result_text).strip())
    
    def load_ground_truth_txt(self, txt_path: str) -> dict:
        """Load ground truth data from TXT file (JSON format)"""
        with open(txt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'OCC' in data:
            return data['OCC']
        return data
    
    def load_metadata_xml(self, xml_path: str) -> dict:
        """Load metadata from XML file"""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        metadata = {}
        
        split_doc = root.find('.//SplitDoc')
        if split_doc is not None:
            doc_type = split_doc.find('DocType')
            if doc_type is not None:
                metadata['DocType'] = doc_type.text
            
            pages = split_doc.find('Pages')
            if pages is not None:
                page_list = pages.findall('Page')
                metadata['TotalPages'] = len(page_list)
        
        return metadata

    def calculate_score(self, extracted: dict, ground_truth: dict, metadata: dict) -> dict:
        """Calculate accuracy score by comparing extracted data with ground truth and metadata"""
        results = {
            "extracted": extracted,
            "ground_truth": ground_truth,
            "metadata": metadata,
            "field_comparison": {},
            "metadata_comparison": {},
            "total_fields": 0,
            "correct_fields": 0,
            "metadata_fields": 0,
            "correct_metadata_fields": 0,
            "score": 0.0,
            "metadata_score": 0.0,
            "overall_score": 0.0
        }
        
        # Standard invoice fields from ground truth
        expected_fields = ['INVOICE_NO', 'INVOICE_DATE', 'CURRENCY_ID', 'INCOTERMS', 'INVOICE_AMOUNT', 'CUSTOMER_ID']
        
        # Compare standard invoice fields
        for field_name in extracted.keys():
            if field_name in ground_truth:
                extracted_value = extracted[field_name]
                gt_value = ground_truth[field_name]
                
                is_correct = extracted_value == gt_value
                
                results['field_comparison'][field_name] = {
                    'extracted': extracted_value,
                    'ground_truth': gt_value,
                    'correct': is_correct
                }
                
                results['total_fields'] += 1
                if is_correct:
                    results['correct_fields'] += 1
        
        # Check for missing fields
        for field_name in expected_fields:
            if field_name in ground_truth and field_name not in extracted:
                gt_value = ground_truth[field_name]
                
                results['field_comparison'][field_name] = {
                    'extracted': None,
                    'ground_truth': gt_value,
                    'correct': False
                }
                
                results['total_fields'] += 1
        
        # Compare metadata fields (DOC_TYPE and TOTAL_PAGES)
        if 'DocType' in metadata:
            doc_type_extracted = extracted.get('DOC_TYPE')
            doc_type_gt = metadata['DocType']
            doc_type_correct = doc_type_extracted == doc_type_gt
            
            results['metadata_comparison']['DOC_TYPE'] = {
                'extracted': doc_type_extracted,
                'ground_truth': doc_type_gt,
                'correct': doc_type_correct
            }
            
            results['metadata_fields'] += 1
            if doc_type_correct:
                results['correct_metadata_fields'] += 1
        
        if 'TotalPages' in metadata:
            total_pages_extracted = extracted.get('TOTAL_PAGES')
            total_pages_gt = metadata['TotalPages']
            total_pages_correct = total_pages_extracted == total_pages_gt
            
            results['metadata_comparison']['TOTAL_PAGES'] = {
                'extracted': total_pages_extracted,
                'ground_truth': total_pages_gt,
                'correct': total_pages_correct
            }
            
            results['metadata_fields'] += 1
            if total_pages_correct:
                results['correct_metadata_fields'] += 1
        
        # Calculate scores
        if results['total_fields'] > 0:
            results['score'] = (results['correct_fields'] / results['total_fields']) * 100
        
        if results['metadata_fields'] > 0:
            results['metadata_score'] = (results['correct_metadata_fields'] / results['metadata_fields']) * 100
        
        total_all_fields = results['total_fields'] + results['metadata_fields']
        correct_all_fields = results['correct_fields'] + results['correct_metadata_fields']
        if total_all_fields > 0:
            results['overall_score'] = (correct_all_fields / total_all_fields) * 100
        
        return results
    
    def process_invoice(self, pdf_path: str, txt_path: str, xml_path: str) -> dict:
        """Process a PDF with its corresponding TXT and XML ground truth files"""
        print(f"Processing: {Path(pdf_path).name}")
        
        extracted_data = self.extract_from_pdf(pdf_path)
        ground_truth = self.load_ground_truth_txt(txt_path)
        metadata = self.load_metadata_xml(xml_path)
        
        results = self.calculate_score(extracted_data, ground_truth, metadata)
        
        return results


def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: $env:GEMINI_API_KEY='your-api-key'")
        return
    
    extractor = InvoiceExtractor(api_key)
    
    data_dir = Path(__file__).parent / 'sampels' / 'invoices-sampels'
    pdf_files = sorted(data_dir.glob("*_SC_INVOICE_*.PDF"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    all_results = []
    mismatches = []

    for pdf_file in pdf_files:
        txt_file = pdf_file.with_suffix('.txt')
        xml_file = pdf_file.with_suffix('.xml')
        
        if not txt_file.exists():
            print(f"Warning: No matching TXT file for {pdf_file.name}, skipping...")
            continue
        
        if not xml_file.exists():
            print(f"Warning: No matching XML file for {pdf_file.name}, skipping...")
            continue
        
        try:
            results = extractor.process_invoice(str(pdf_file), str(txt_file), str(xml_file))
            all_results.append({
                "pdf_file": pdf_file.name,
                "txt_file": txt_file.name,
                "xml_file": xml_file.name,
                "results": results
            })

            print(f"  Invoice Fields Score: {results['score']:.2f}% ({results['correct_fields']}/{results['total_fields']} fields correct)")
            print(f"  Metadata Score: {results['metadata_score']:.2f}% ({results['correct_metadata_fields']}/{results['metadata_fields']} metadata fields correct)")
            print(f"  Overall Score: {results['overall_score']:.2f}%")
            print(f"  Ground Truth Metadata: DocType={results['metadata'].get('DocType')}, TotalPages={results['metadata'].get('TotalPages')}")
            
            if results['metadata_comparison']:
                print(f"  Metadata Validation:")
                for field_name, comparison in results['metadata_comparison'].items():
                    status = "✓" if comparison['correct'] else "✗"
                    print(f"    {status} {field_name}: {comparison['extracted']} (GT: {comparison['ground_truth']})")
            
            if results['overall_score'] < 100:
                pdf_mismatches = []
                
                # Add invoice field mismatches
                for field_name, comparison in results['field_comparison'].items():
                    if not comparison['correct']:
                        pdf_mismatches.append({
                            "field": field_name,
                            "field_type": "invoice_data",
                            "extracted_value": comparison['extracted'],
                            "ground_truth_value": comparison['ground_truth'],
                        })
                
                # Add metadata mismatches
                for field_name, comparison in results['metadata_comparison'].items():
                    if not comparison['correct']:
                        pdf_mismatches.append({
                            "field": field_name,
                            "field_type": "metadata",
                            "extracted_value": comparison['extracted'],
                            "ground_truth_value": comparison['ground_truth'],
                        })
                
                if pdf_mismatches:
                    mismatches.append({
                        "pdf_name": pdf_file.name,
                        "mismatched_fields": pdf_mismatches
                    })
            
            print()
            
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
            print()

    output_file = data_dir / f"extraction_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    if all_results:
        avg_invoice_score = sum(r['results']['score'] for r in all_results) / len(all_results)
        avg_metadata_score = sum(r['results']['metadata_score'] for r in all_results) / len(all_results)
        avg_overall_score = sum(r['results']['overall_score'] for r in all_results) / len(all_results)
        
        print(f"\nOverall Statistics:")
        print(f"  Average Invoice Fields Score: {avg_invoice_score:.2f}%")
        print(f"  Average Metadata Score: {avg_metadata_score:.2f}%")
        print(f"  Average Overall Score: {avg_overall_score:.2f}%")
    
    if mismatches:
        output_file = data_dir / f"mismatched_fields_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mismatches, f, indent=2, ensure_ascii=False)
        print(f"\nMismatched fields saved to: {output_file}")


if __name__ == "__main__":
    main()
