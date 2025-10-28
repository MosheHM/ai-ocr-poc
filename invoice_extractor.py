import os
import json
from pathlib import Path
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an expert invoice data extraction system. Extract the following fields from the invoice:

{
    "INVOICE_NO": null,
    "INVOICE_DATE": null,
    "CURRENCY_ID": null,
    "INCOTERMS": null,
    "INVOICE_AMOUNT": null,
    "CUSTOMER_ID": null
}

Return ONLY a valid JSON object with these exact field names. If a field is not found, use null as the value.
"""


class InvoiceExtractor:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        
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
        # Remove markdown code blocks if present
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        print(f"Extracted JSON: {result_text}")
        return json.loads(result_text.strip())
    
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
        
        for field in ground_truth.keys():
            results["total_fields"] += 1
            extracted_value = extracted.get(field)
            truth_value = ground_truth.get(field)
            
            # Normalize values for comparison
            extracted_norm = str(extracted_value).strip().lower() if extracted_value is not None else None
            truth_norm = str(truth_value).strip().lower() if truth_value is not None else None
            
            is_correct = extracted_norm == truth_norm
            if is_correct:
                results["correct_fields"] += 1
            
            results["field_comparison"][field] = {
                "extracted": extracted_value,
                "ground_truth": truth_value,
                "correct": is_correct
            }
        
        if results["total_fields"] > 0:
            results["score"] = results["correct_fields"] / results["total_fields"]
        
        return results
    
    def process_invoice_pair(self, pdf_path: str, txt_path: str) -> dict:
        """Process a PDF-TXT pair and return extraction results with score"""
        print(f"Processing: {Path(pdf_path).name}")
        
        # Extract data from PDF
        extracted_data = self.extract_from_pdf(pdf_path)
        
        # Load ground truth from TXT file containing JSON data
        with open(txt_path, 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
        
        # Calculate score
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
            print(f"Results for {pdf_file.name}:")
            print(f"  results: {results}")
            print(f"  Score: {results['score']:.2%} ({results['correct_fields']}/{results['total_fields']} fields correct)")
            print()
            
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
            continue
    
    output_file = data_dir / "extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    if all_results:
        avg_score = sum(r['results']['score'] for r in all_results) / len(all_results)
        print(f"\nOverall Average Score: {avg_score:.2%}")


if __name__ == "__main__":
    main()
