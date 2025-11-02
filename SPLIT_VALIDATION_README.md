# Split Document Validation Script

## Overview

The `validate_split_docs.py` script validates document splitting performed on original (ORG) files by:

1. **Parsing XML metadata** from ORG files to extract split document information
2. **Sending split PDFs to Gemini** for OCR extraction
3. **Validating splitting correctness** by comparing:
   - Page counts (XML vs Gemini)
   - Document types (XML vs Gemini)
   - Extracted data (Gemini vs .txt ground truth files)

## File Structure

The script expects the following file structure:

```
sampels/
├── combined-sampels/          # Contains ORG files and their XML metadata
│   ├── {primary_num}_ORG_{parent_com_id}.PDF
│   └── {primary_num}_ORG_{parent_com_id}.xml
└── invoices-sampels/          # Contains split documents
    ├── {primary_num}_SC_INVOICE_{filing_com_id}.PDF
    ├── {primary_num}_SC_INVOICE_{filing_com_id}.xml
    └── {primary_num}_SC_INVOICE_{filing_com_id}.txt  (optional)
```

### XML Structure

ORG XML files contain metadata about how documents were split:

```xml
<SplittedResult>
  <ParentComId>x9cp+3yx40mttjvnrwzffg00000000</ParentComId>
  <SplittedDocs>
    <SplitDoc>
      <FilingComId>5qpckztl_kohxvofp6jmrg00000000</FilingComId>
      <FilingDocTypeName>Supplier Invoice</FilingDocTypeName>
      <FilingDocTypeCode>FSI</FilingDocTypeCode>
      <PrimaryNum>81124344</PrimaryNum>
      <Pages>
        <Page>
          <PageNum>1</PageNum>
          <Rotate>0</Rotate>
        </Page>
      </Pages>
    </SplitDoc>
  </SplittedDocs>
</SplittedResult>
```

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

Run the validation script:

```bash
python validate_split_docs.py
```

The script will:
1. Find all ORG XML files in `sampels/combined-sampels/`
2. For each ORG file, parse the XML to extract split document metadata
3. For each split document:
   - Find the corresponding PDF in `sampels/invoices-sampels/`
   - Send it to Gemini for extraction
   - Validate page counts match
   - Validate document types match
   - If a .txt file exists, validate extracted data matches
4. Generate a comprehensive validation report

## Output

### Console Output

The script provides real-time progress and validation results:

```
Processing ORG file: 81124344_ORG_x9cp+3yx40mttjvnrwzffg00000000.xml
  Parent ComId: x9cp+3yx40mttjvnrwzffg00000000
  Total split documents: 19

  Split Doc: 5qpckztl_kohxvofp6jmrg00000000
    Type: Supplier Invoice
    Pages: 1
    PDF found: ✓
    TXT found: ✗
    Pages match: ✓
    Doc type match: ✓

================================================================================
OVERALL SUMMARY
================================================================================
Total ORG files processed: 5
Total split documents: 95
PDFs found: 95/95
TXT files found: 45/95
Pages match: 93/95
Doc types match: 90/95
TXT data match: 40/45
Total errors: 12
```

### JSON Results File

Results are saved to `split_doc_validation_results.json` with detailed information:

```json
{
  "total_org_files": 5,
  "overall_summary": {
    "total_split_docs": 95,
    "pdf_found": 95,
    "txt_found": 45,
    "pages_match": 93,
    "doc_type_match": 90,
    "txt_data_match": 40,
    "errors": 12
  },
  "org_file_results": [
    {
      "org_xml_path": "...",
      "org_metadata": {
        "parent_com_id": "x9cp+3yx40mttjvnrwzffg00000000",
        "split_docs": [...]
      },
      "split_doc_validations": [
        {
          "filing_com_id": "5qpckztl_kohxvofp6jmrg00000000",
          "doc_type_name": "Supplier Invoice",
          "xml_metadata": {...},
          "extraction_result": {...},
          "validations": {
            "pages_match": true,
            "doc_type_match": true,
            "txt_data_match": null
          },
          "errors": []
        }
      ]
    }
  ]
}
```

## Validation Checks

### 1. Page Count Validation
Compares the number of pages in the XML metadata with the `TOTAL_PAGES` extracted by Gemini.

### 2. Document Type Validation
Compares the `FilingDocTypeCode` from XML (e.g., "FSI") with the `DOC_TYPE` extracted by Gemini.

### 3. Extracted Data Validation (if .txt file exists)
Compares Gemini extraction results with ground truth data from .txt files, checking fields like:
- INVOICE_NO
- INVOICE_DATE
- CURRENCY_ID
- INCOTERMS
- INVOICE_AMOUNT
- CUSTOMER_ID

## Testing

Run the unit tests to verify functionality:

```bash
python -m pytest test_validate_split_docs.py -v
```

Tests cover:
- XML parsing
- Page information extraction
- Prompt generation
- File path construction
- Code block removal

## Error Handling

The script handles various error cases:
- **Missing PDF files**: Logged as errors
- **Missing TXT files**: Noted but not treated as errors (optional)
- **Extraction failures**: Logged with detailed error messages
- **JSON parse errors**: Raw response captured for debugging
- **Page/type mismatches**: Reported as validation errors

## Supported Document Types

The script creates specialized extraction prompts for:
- **Supplier Invoice**: Extracts invoice number, date, amount, currency, etc.
- **Packing List**: Extracts customer name, pieces, weight
- **Other types**: Generic extraction with TOTAL_PAGES

## Requirements

- Python 3.7+
- google-genai
- pypdf
- pytest (for testing)

## Notes

- The script uses the `gemini-2.5-flash` model by default
- Processing time depends on the number of split documents and API response time
- API key is required for extraction but not for XML parsing tests
- Results are saved after processing all ORG files
