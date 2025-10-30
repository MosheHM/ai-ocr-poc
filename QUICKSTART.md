# Quick Start Guide

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/MosheHM/ai-ocr-poc.git
cd ai-ocr-poc
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your API key**
```bash
# Linux/Mac
export GEMINI_API_KEY='your-api-key-here'

# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key-here'

# Windows CMD
set GEMINI_API_KEY=your-api-key-here
```

## Basic Usage

### Process a PDF document
```bash
python main.py path/to/document.pdf
```

This will:
1. Classify each page to identify document type
2. Extract data using type-specific extractors
3. Display results in the console
4. Save results to a JSON file

### With ground truth validation
```bash
python main.py path/to/document.pdf --ground-truth path/to/ground_truth.json
```

This adds validation of extracted data against known correct values.

### Specify output file
```bash
python main.py path/to/document.pdf --output my_results.json
```

## Testing

Run the test suite to verify everything is working:
```bash
python test_modules.py
```

Expected output:
```
============================================================
AI OCR POC - Module Tests
============================================================
Testing imports...
✓ All imports successful

Testing document types...
✓ Document types correct: ['Invoice', 'OBL', 'HAWB', 'Packing List', 'Unknown']

...

============================================================
Results: 6/6 tests passed
✓ All tests passed!
```

## Examples

View usage examples and demonstrations:
```bash
python examples.py
```

## Supported Document Types

1. **Invoice** - Commercial invoices
   - Fields: invoice number, date, currency, incoterms, amount, customer ID

2. **OBL** - Ocean Bill of Lading
   - Fields: customer name, weight, volume, incoterms

3. **HAWB** - House Air Waybill
   - Fields: customer name, currency, carrier, HAWB number, pieces, weight

4. **Packing List** - Package contents
   - Fields: customer name, pieces, weight

## Expected Output

### Console Report
```
================================================================================
Document Processing Report: document.pdf
================================================================================
Total Pages: 3
Success: True

Page Classifications:
--------------------------------------------------------------------------------
  Page 1: Invoice (confidence: 0.98)
  Page 2: Packing List (confidence: 0.95)
  Page 3: OBL (confidence: 0.92)

Data Extractions:
--------------------------------------------------------------------------------
  Page 1 (Invoice): ✓ Success
    Fields extracted: 6
      - INVOICE_NO: 0004833/E
      - INVOICE_DATE: 2025073000000000
      - CURRENCY_ID: EUR
      - INCOTERMS: FCA
      - INVOICE_AMOUNT: 7632.0
      - CUSTOMER_ID: D004345
  ...
```

### JSON Results File
```json
{
  "pdf_path": "document.pdf",
  "total_pages": 3,
  "success": true,
  "overall_score": 95.5,
  "classifications": [
    {
      "page_number": 1,
      "document_type": "Invoice",
      "confidence": 0.98
    },
    ...
  ],
  "extractions": [
    {
      "page_number": 1,
      "document_type": "Invoice",
      "data": {
        "INVOICE_NO": "0004833/E",
        "INVOICE_DATE": "2025073000000000",
        ...
      },
      "success": true
    },
    ...
  ]
}
```

## Troubleshooting

### API Key Not Set
```
Error: GEMINI_API_KEY environment variable not set
Set it with: export GEMINI_API_KEY='your-api-key'
```
**Solution:** Set the GEMINI_API_KEY environment variable as shown in step 3 above.

### PDF Not Found
```
Error: PDF file not found: path/to/document.pdf
```
**Solution:** Check the path to your PDF file is correct.

### Import Errors
```
ImportError: No module named 'google.genai'
```
**Solution:** Install dependencies with `pip install -r requirements.txt`

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Review [SUMMARY.md](SUMMARY.md) for implementation overview

## Legacy Script

The original invoice-only extractor is still available:
```bash
python invoice_extractor.py
```

This processes all PDFs in the `invoices-sampels` folder.
