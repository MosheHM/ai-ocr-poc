import time
import os
import json
from pathlib import Path
from google import genai
from google.genai import types

# System prompt with format validation instructions
SYSTEM_PROMPT = """You are an AI assistant specialized in extracting structured data from invoices.

Extract the following fields from the invoice and return them as a JSON object:


REQUIRED RETURN FIELDS AND FORMATS( THE FORMAT IS JUST FOR RETURN VALIDATION, NOT FOR EXTRACTION):
- INVOICE_NO: Extract as-is, preserving all characters including slashes (e.g., "0004833/E", "INV-25-0026439")
- INVOICE_DATE: Format as YYYYMMDDHHMMSSSS (16 digits)
  * Convert any date format to: YYYYMMDD00000000
  * Example: "30.07.2025" becomes "2025073000000000"
  * Example: "30/07/2025" becomes "2025073000000000"
  * Example: "July 30, 2025" becomes "2025073000000000"
  * Always pad with 00000000 at the end for time portion
- CURRENCY_ID: 3-letter currency code in uppercase (e.g., "EUR", "USD", "GBP")
- INCOTERMS: INCOTERMS code in uppercase (e.g., "FCA", "FOB", "CIF", "EXW")
  * Do NOT include location details or additional text
  * Just the code: "FCA" not "FCA Duisburg, stock Buhlmann"
- INVOICE_AMOUNT: number (integer or float) without currency symbols
  * Example: 7632.00 or 7632
- CUSTOMER_ID: Extract as-is (e.g., "D004345")

CRITICAL FORMAT RULES:
1. INVOICE_DATE must be exactly 16 digits: YYYYMMDD00000000
2. INCOTERMS must be ONLY the code (3 letters usually), no location or extra text
3. INVOICE_AMOUNT must be a number type, not a string
4. Preserve exact formatting for INVOICE_NO (keep slashes, dashes, etc.)
5. Return ONLY valid JSON with these exact field names
6. If a field is not found, omit it from the response

Example output format:
{
    "INVOICE_NO": "0004833/E",
    "INVOICE_DATE": "2025073000000000",
    "CURRENCY_ID": "EUR",
    "INCOTERMS": "FCA",
    "INVOICE_AMOUNT": 7632.00,
    "CUSTOMER_ID": "D004345"
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

    def calculate_score(self, extracted: dict, ground_truth: dict) -> dict:
        """Calculate accuracy score by comparing extracted data with ground truth"""
        results = {
            "extracted": extracted,
            "ground_truth": ground_truth,
            "field_comparison": {},
            "total_fields": 0,
            "correct_fields": 0,
            "score": 0.0
        }
        
        # Extract the actual field values from ground_truth OCC object
        if 'OCC' in ground_truth:
            gt_fields = ground_truth['OCC']
        else:
            gt_fields = ground_truth
        
        for field_name in extracted.keys():
            if field_name in gt_fields:
                extracted_value = extracted[field_name]
                gt_value = gt_fields[field_name]
                
                is_correct = extracted_value == gt_value
                
                results['field_comparison'][field_name] = {
                    'extracted': extracted_value,
                    'ground_truth': gt_value,
                    'correct': is_correct
                }
                
                results['total_fields'] += 1
                if is_correct:
                    results['correct_fields'] += 1
        
        if results['total_fields'] > 0:
            results['score'] = (results['correct_fields'] / results['total_fields']) * 100
        
        return results
    
    def process_invoice_pair(self, pdf_path: str, txt_path: str) -> dict:
        """Process a PDF-TXT pair and return extraction results with score"""
        print(f"Processing: {Path(pdf_path).name}")
        
        extracted_data = self.extract_from_pdf(pdf_path)
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
        
        results = self.calculate_score(extracted_data, ground_truth)
        
        return results


def main():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Set it with: $env:GEMINI_API_KEY='your-api-key'")
        return
    
    extractor = InvoiceExtractor(api_key)
    

    data_dir = Path(f'{Path(__file__).parent}/invoices-sampels')
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    all_results = []
    mismatches = []
    
    for pdf_file in pdf_files:
        txt_file = pdf_file.with_suffix('.txt')
        
        if not txt_file.exists():
            print(f"Warning: No matching TXT file for {pdf_file.name}, skipping...")
            continue
        
        try:
            results = extractor.process_invoice_pair(str(pdf_file), str(txt_file))
            all_results.append({
                "pdf_file": pdf_file.name,
                "txt_file": txt_file.name,
                "results": results
            })

            print(f"  Score: {results['score']:.2%} ({results['correct_fields']}/{results['total_fields']} fields correct)")
            
            if results['score'] < 100:
                pdf_mismatches = []
                for field_name, comparison in results['field_comparison'].items():
                    if not comparison['correct']:
                        pdf_mismatches.append({
                            "field": field_name,
                            "extracted_value": comparison['extracted'],
                            "ground_truth_value": comparison['ground_truth']
                        })
                
                if pdf_mismatches:
                    mismatches.append({
                        "pdf_name": pdf_file.name,
                        "mismatched_fields": pdf_mismatches
                    })
            
            print()
            
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
            

    output_file = data_dir / f"extraction_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    if all_results:
        avg_score = sum(r['results']['score'] for r in all_results) / len(all_results)
        print(f"\nOverall Average Score: {avg_score:.2%}")
    
    if mismatches:
        print("\n" + "="*80)
        print("MISMATCHED FIELDS (Score < 100%):")
        print("="*80)
        print(json.dumps(mismatches, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
