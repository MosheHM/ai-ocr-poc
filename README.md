# AI OCR POC - Multi-Document Processing System

A modular document processing system that automatically classifies and extracts data from multi-page PDFs containing different document types including Invoices, Ocean Bills of Lading (OBL), House Air Waybills (HAWB), and Packing Lists.

## Overview

This application uses Google's Gemini API to:
1. **Classify** each page of a PDF to identify its document type
2. **Extract** structured data using type-specific extractors for each document type
3. **Validate** extracted data against ground truth (optional)

## Features

- **Multi-page PDF Processing**: Handles PDFs with multiple pages of different document types
- **Automatic Classification**: AI-powered identification of document types
- **Document Instance Grouping**: Automatically groups consecutive pages of the same type into document instances
- **Document Summary**: Clear reporting of how many documents of each type exist and which pages they occupy
- **Type-specific Extraction**: Specialized extractors for each document type with tailored schemas
- **Performance Validation**: Compares extracted data against ground truth with detailed scoring
- **PDF Splitting Validation**: Validates document splitting results against XML ground truth files (see [SPLITTING_VALIDATION.md](SPLITTING_VALIDATION.md))
- **Error Handling**: Comprehensive error handling with detailed feedback
- **Modular Architecture**: Clean, maintainable code structure with reusable components

## Architecture

```
modules/
├── types/              # Type definitions, enums, and protocols
├── llm/                # LLM client for Google Gemini API
├── document_classifier/ # Page type classification
├── extractors/         # Type-specific data extractors
├── validators/         # Performance validation
├── utils/              # Utility functions (PDF handling)
└── workflow.py         # Main processing orchestrator
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Supported Document Types

### Invoice
Extracts: Invoice number, date, currency, incoterms, amount, customer ID

### OBL (Ocean Bill of Lading)
Extracts: Customer name, weight, volume, incoterms

### HAWB (House Air Waybill)
Extracts: Customer name, currency, carrier, HAWB number, pieces, weight

### Packing List
Extracts: Customer name, pieces, weight

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your Gemini API key:**
```bash
# Linux/Mac
export GEMINI_API_KEY='your-api-key-here'

# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key-here'

# Windows CMD
set GEMINI_API_KEY=your-api-key-here
```

## Usage

### New Modular System

Process a PDF document with automatic page classification:
```bash
python main.py path/to/document.pdf
```

With ground truth validation:
```bash
python main.py path/to/document.pdf --ground-truth path/to/ground_truth.json
```

**NEW:** Conditional validation mode (only processes PDFs with .txt ground truth files):
```bash
python main.py path/to/document.pdf --validate-txt
```

This mode automatically detects `.txt` ground truth files and only processes documents that have them, saving API quota. See [CONDITIONAL_VALIDATION.md](CONDITIONAL_VALIDATION.md) for details.

Specify output file:
```bash
python main.py path/to/document.pdf --output results.json
```

### Demonstration Script

To see a demonstration of the document summary feature:
```bash
python demo_summary.py
```

This shows how the system handles a 10-page PDF with multiple invoices and packing lists, displaying:
- Document counts by type
- Page ranges for each document instance
- JSON output format

### Legacy Invoice Extractor

The original invoice-only extractor is still available:
```bash
python invoice_extractor.py
```

This processes all PDFs in the `invoices-sampels` folder.

### PDF Splitting Validation

Validate PDF splitting results against XML ground truth files:
```bash
# Validate all PDFs in sampels/combined-sampels directory
python validate_splitting.py

# Validate a specific PDF
python validate_splitting.py --pdf sampels/combined-sampels/81124047_ORG_pxutqxvrveky75v6dwhymg00000000.PDF
```

See [SPLITTING_VALIDATION.md](SPLITTING_VALIDATION.md) for detailed documentation on PDF splitting validation.

## Processing Pipeline

The system follows a four-stage pipeline:

1. **Classification Phase**
   - Each page is analyzed by an AI classifier
   - Returns document type and confidence score
   - Supported types: Invoice, OBL, HAWB, Packing List

2. **Document Grouping Phase**
   - Consecutive pages of the same type are grouped into document instances
   - For example, pages 1-3 classified as Invoice become one Invoice instance
   - Enables accurate counting of distinct documents in multi-page PDFs

3. **Extraction Phase**
   - Data is extracted using type-specific extractors
   - Each extractor has a specialized system prompt
   - Multi-page documents are processed as a single unit
   - Returns structured JSON data

4. **Validation Phase** (Optional)
   - Extracted data is compared against ground truth
   - Field-by-field comparison with scoring
   - Detailed mismatch reporting

## Output

### Console Report
Human-readable processing report showing:
- **Document Summary**: Count of each document type and page ranges for each document instance
- Page-by-page classifications with confidence scores
- Extraction results for each document instance (grouped pages)
- Validation scores (if ground truth provided)
- Detailed error messages

Example console output:
```
Document Summary:
--------------------------------------------------------------------------------
  Invoice: 3 document(s)
  Packing List: 2 document(s)

Document Instances:
  1. Invoice - pages 1-3
  2. Packing List - page 4
  3. Invoice - pages 5-6
  4. Packing List - pages 7-9
  5. Invoice - page 10
```

### JSON Results File
Machine-readable results containing:
- Document summary with counts by type
- Document instances with page ranges
- All page classifications
- All extracted data
- Validation metrics and field comparisons
- Error logs

Example output structure:
```json
{
  "pdf_path": "document.pdf",
  "total_pages": 10,
  "success": true,
  "overall_score": 95.5,
  "document_summary": {
    "total_documents": 5,
    "documents_by_type": {
      "Invoice": 3,
      "Packing List": 2
    }
  },
  "document_instances": [
    {
      "document_type": "Invoice",
      "start_page": 1,
      "end_page": 3,
      "page_count": 3,
      "page_range": "1-3"
    }
  ],
  "classifications": [...],
  "extractions": [...],
  "validations": [...]
}
```

## Ground Truth Format

Ground truth files should be JSON with the expected extracted fields:

```json
{
  "INVOICE_NO": "0004833/E",
  "INVOICE_DATE": "2025073000000000",
  "CURRENCY_ID": "EUR",
  "INCOTERMS": "FCA",
  "INVOICE_AMOUNT": 7632.00,
  "CUSTOMER_ID": "D004345"
}
```

Or with OCC wrapper:
```json
{
  "OCC": {
    "INVOICE_NO": "0004833/E",
    ...
  }
}
```

## Error Handling

The system provides comprehensive error handling:
- **Classification Failures**: Pages marked as "Unknown" type
- **Extraction Failures**: Logged with detailed error messages
- **Validation Errors**: Field-by-field mismatch reporting
- **Processing Errors**: Overall pipeline errors captured

## Development

### Configuring the LLM Model

The system uses Google Gemini models for classification and extraction. The default model is `gemini-2.5-flash`, but you can configure it:

**Supported Models:**
- `gemini-2.0-flash-exp`
- `gemini-1.5-flash`
- `gemini-1.5-flash-8b`
- `gemini-1.5-pro`
- `gemini-2.5-flash` (default)

To use a different model:
```python
from modules.llm import GeminiLLMClient

client = GeminiLLMClient(api_key)
response = client.generate_content(
    prompt="Your prompt",
    model="gemini-1.5-pro"  # Specify model
)
```

The model list is maintained in `modules/llm/client.py` (`SUPPORTED_GEMINI_MODELS`).

### Adding a New Document Type

1. Add enum value to `DocumentType` in `modules/types/__init__.py`
2. Define schema in `DOCUMENT_SCHEMAS`
3. Create extractor class in `modules/extractors/extractors.py`
4. Update `ExtractorFactory` mapping

### Running Tests

The system can be tested with ground truth files matching the document schemas.

## Requirements

- Python 3.7+
- google-genai
- pypdf

## License

See repository license.
