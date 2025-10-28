# AI OCR POC - Modular Architecture

A modular document processing system that classifies and extracts data from multi-page PDFs containing different document types.

## Features

- **Multi-page PDF Processing**: Handles PDFs with multiple pages of different document types
- **Document Classification**: Automatically identifies document types (Invoice, OBL, HAWB, Packing List)
- **Type-specific Extraction**: Uses specialized extractors for each document type
- **Performance Validation**: Compares extracted data against ground truth
- **Error Handling**: Comprehensive error handling with detailed feedback
- **Modular Architecture**: Clean separation of concerns with reusable components

## Architecture

```
modules/
├── types/              # Type definitions and protocols
├── llm/                # LLM client for Google Gemini API
├── document_classifier/ # Page type classification
├── extractors/         # Type-specific data extractors
├── validators/         # Performance validation
├── utils/              # Utility functions (PDF handling)
└── workflow.py         # Main processing orchestrator
```

## Document Types & Schemas

### Invoice
```json
{
  "INVOICE_NO": "string",
  "INVOICE_DATE": "YYYYMMDD00000000",
  "CURRENCY_ID": "string (3-letter)",
  "INCOTERMS": "string (uppercase)",
  "INVOICE_AMOUNT": "number",
  "CUSTOMER_ID": "string"
}
```

### OBL (Ocean Bill of Lading)
```json
{
  "CUSTOMER_NAME": "string or null",
  "WEIGHT": "number or null",
  "VOLUME": "number or null",
  "INCOTERMS": "string or null"
}
```

### HAWB (House Air Waybill)
```json
{
  "CUSTOMER_NAME": "string or null",
  "CURRENCY": "string or null",
  "CARRIER": "string or null",
  "HAWB_NUMBER": "string or null",
  "PIECES": "number or null",
  "WEIGHT": "number or null"
}
```

### Packing List
```json
{
  "CUSTOMER_NAME": "string or null",
  "PIECES": "number or null",
  "WEIGHT": "number or null"
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Gemini API key:
```bash
# Linux/Mac
export GEMINI_API_KEY='your-api-key-here'

# Windows PowerShell
$env:GEMINI_API_KEY='your-api-key-here'

# Windows CMD
set GEMINI_API_KEY=your-api-key-here
```

## Usage

### Process a PDF document:
```bash
python main.py path/to/document.pdf
```

### With ground truth validation:
```bash
python main.py path/to/document.pdf --ground-truth path/to/ground_truth.json
```

### Specify output file:
```bash
python main.py path/to/document.pdf --output results.json
```

## Processing Pipeline

1. **Classification Phase**: Each page is analyzed to identify its document type
   - Uses a specialized LLM prompt for classification
   - Returns document type and confidence score
   
2. **Extraction Phase**: Data is extracted from each page using type-specific extractors
   - Each document type has its own extractor with a tailored system prompt
   - Extractors return structured JSON data
   
3. **Validation Phase**: (Optional) Extracted data is compared against ground truth
   - Field-by-field comparison
   - Accuracy scoring
   - Detailed mismatch reporting

## Error Handling

The system provides comprehensive error handling and feedback:

- **Classification Failures**: Pages that cannot be classified are marked as "Unknown"
- **Extraction Failures**: Failed extractions are logged with error messages
- **Validation Errors**: Mismatches between extracted and ground truth data are reported
- **Processing Errors**: Overall pipeline errors are captured and reported

## Output

The system generates:

1. **Console Report**: Human-readable processing report with:
   - Page classifications
   - Extraction results
   - Validation scores (if ground truth provided)
   - Error messages

2. **JSON Results File**: Machine-readable results containing:
   - All classifications
   - All extracted data
   - Validation metrics
   - Error logs

## Legacy Script

The original `invoice_extractor.py` is preserved for backward compatibility but uses the older single-document-type approach.

## Development

### Adding a New Document Type

1. Add the type to `DocumentType` enum in `modules/types/__init__.py`
2. Define the schema in `DOCUMENT_SCHEMAS`
3. Create a new extractor class in `modules/extractors/extractors.py`
4. Update `ExtractorFactory` to support the new type

### Testing

The system can be tested with ground truth files in JSON format. The ground truth should match the schema of the document type being tested.

## Requirements

- Python 3.7+
- google-genai
- pypdf

## License

See repository license.
