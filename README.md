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
- **Type-specific Extraction**: Specialized extractors for each document type with tailored schemas
- **Performance Validation**: Compares extracted data against ground truth with detailed scoring
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

Specify output file:
```bash
python main.py path/to/document.pdf --output results.json
```

### Legacy Invoice Extractor

The original invoice-only extractor is still available:
```bash
python invoice_extractor.py
```

This processes all PDFs in the `invoices-sampels` folder.

## Processing Pipeline

The system follows a three-stage pipeline:

1. **Classification Phase**
   - Each page is analyzed by an AI classifier
   - Returns document type and confidence score
   - Supported types: Invoice, OBL, HAWB, Packing List

2. **Extraction Phase**
   - Data is extracted using type-specific extractors
   - Each extractor has a specialized system prompt
   - Returns structured JSON data

3. **Validation Phase** (Optional)
   - Extracted data is compared against ground truth
   - Field-by-field comparison with scoring
   - Detailed mismatch reporting

## Output

### Console Report
Human-readable processing report showing:
- Page classifications with confidence scores
- Extraction results for each page
- Validation scores (if ground truth provided)
- Detailed error messages

### JSON Results File
Machine-readable results containing:
- All page classifications
- All extracted data
- Validation metrics and field comparisons
- Error logs

Example output structure:
```json
{
  "pdf_path": "document.pdf",
  "total_pages": 3,
  "success": true,
  "overall_score": 95.5,
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
