# Document Splitter Module

AI-powered document analysis and PDF splitting using Google Gemini.

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Exports `DocumentSplitter`, `split_and_extract_documents` |
| `splitter.py` | Main `DocumentSplitter` class and extraction prompt |

## Classes

### DocumentSplitter

Main class for processing PDFs with Gemini AI.

```python
from modules.document_splitter import DocumentSplitter

splitter = DocumentSplitter(
    api_key: str,                    # Google Gemini API key (required)
    model: str = 'gemini-2.5-flash', # Gemini model name
    timeout_seconds: int = 300       # API timeout
)
```

#### Methods

##### `extract_documents(pdf_path: str) -> List[Dict[str, Any]]`

Send PDF to Gemini AI and get document analysis.

```python
documents = splitter.extract_documents("combined.pdf")
# Returns: [{"DOC_TYPE": "INVOICE", "START_PAGE_NO": 1, ...}, ...]
```

##### `split_and_save(pdf_path: str, output_dir: str, base_filename: str = None) -> Dict[str, Any]`

Full pipeline: analyze PDF → split into files → save results JSON.

```python
result = splitter.split_and_save("combined.pdf", "output/")
# Returns: {"source_pdf": "...", "total_documents": 3, "documents": [...]}
```

## Convenience Function

```python
from modules.document_splitter import split_and_extract_documents

result = split_and_extract_documents(
    pdf_path="document.pdf",
    output_dir="output/",
    api_key=None,  # Uses GEMINI_API_KEY env var
    model="gemini-2.5-flash",
    base_filename=None
)
```

## UNIFIED_EXTRACTION_PROMPT

The AI prompt is embedded in `splitter.py`. It instructs Gemini to:

1. Detect document boundaries in multi-document PDFs
2. Classify each document (INVOICE, OBL, HAWB, PACKING_LIST)
3. Extract type-specific fields
4. Return page ranges for splitting

### Supported Document Types

| Type | Fields |
|------|--------|
| INVOICE | INVOICE_NO, INVOICE_DATE, CURRENCY_ID, INCOTERMS, INVOICE_AMOUNT, CUSTOMER_ID |
| OBL | CUSTOMER_NAME, WEIGHT, VOLUME, INCOTERMS |
| HAWB | CUSTOMER_NAME, CURRENCY, CARRIER, HAWB_NUMBER, PIECES, WEIGHT |
| PACKING_LIST | CUSTOMER_NAME, PIECES, WEIGHT |

### Common Fields (All Types)

| Field | Type | Description |
|-------|------|-------------|
| DOC_TYPE | string | Document classification |
| DOC_TYPE_CONFIDENCE | float | 0.0-1.0 confidence score |
| START_PAGE_NO | int | 1-based start page |
| END_PAGE_NO | int | 1-based end page |
| TOTAL_PAGES | int | Page count for document |

## Output Format

### Results JSON

```json
{
  "source_pdf": "path/to/input.pdf",
  "output_directory": "output/",
  "total_documents": 2,
  "documents": [
    {
      "DOC_TYPE": "INVOICE",
      "DOC_TYPE_CONFIDENCE": 0.95,
      "INVOICE_NO": "0004833/E",
      "START_PAGE_NO": 1,
      "END_PAGE_NO": 2,
      "FILE_PATH": "output/doc_INVOICE_1_pages_1-2.pdf",
      "FILE_NAME": "doc_INVOICE_1_pages_1-2.pdf"
    }
  ]
}
```

### Split PDF Naming

Pattern: `{base}_{DOC_TYPE}_{index}_pages_{start}-{end}.pdf`

Example: `document_INVOICE_1_pages_1-2.pdf`

## Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| GEMINI_API_KEY | - | Required for API access |
| GEMINI_MODEL | gemini-2.5-flash | Model to use |
| GEMINI_TIMEOUT_SECONDS | 300 | API call timeout |

## Limits

| Limit | Value |
|-------|-------|
| Max output documents | 100 per PDF |
