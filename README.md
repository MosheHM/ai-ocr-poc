# Invoice OCR Validation App

This application uses Google's Gemini API to extract data from PDF invoices and validates the extraction against ground truth JSON files.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:
```bash
# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key-here'

# Windows CMD
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY='your-api-key-here'
```

## Usage

1. Place your PDF invoices and corresponding JSON ground truth files in the `ai-ocr-poc` folder
2. Ensure each PDF has a matching JSON file with the same name (e.g., `invoice.pdf` and `invoice.json`)
3. The JSON files should contain the extracted data in this format:
```json
{
    "Invoice Number": "12345",
    "Date": "2024-01-15",
    "Currency": "USD",
    "Incoterms": "FOB",
    "Total": "1500.00",
    "Client": "Acme Corp"
}
```

4. Run the script:
```bash
python invoice_extractor.py
```

## Output

The script will:
- Process each PDF-JSON pair
- Extract invoice data using Gemini API
- Compare extracted data against ground truth
- Calculate accuracy score for each invoice
- Display results in the console
- Save detailed results to `extraction_results.json`

## Expected Fields

The extractor looks for these fields:
- **Invoice Number**: The unique invoice identifier
- **Date**: Invoice date
- **Currency**: Currency code (USD, EUR, etc.)
- **Incoterms**: International commercial terms
- **Total**: Total invoice amount
- **Client**: Customer/client name

## Scoring

Each field is compared against the ground truth:
- Exact match = correct
- Any difference = incorrect
- Score = (correct fields / total fields) × 100%
