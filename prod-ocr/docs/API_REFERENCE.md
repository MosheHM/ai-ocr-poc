# API Reference

This document provides detailed API documentation for the AI Document Processing System.

---

## Table of Contents

1. [Queue Message APIs](#queue-message-apis)
2. [Python Public APIs](#python-public-apis)
3. [Document Schemas](#document-schemas)
4. [Error Handling](#error-handling)

---

## Queue Message APIs

### Task Message (Input)

Send to queue: `processing-tasks`

```json
{
  "correlationKey": "string (required)",
  "pdfBlobUrl": "string (required)"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `correlationKey` | string | ✅ | Unique identifier (1-128 alphanumeric chars, hyphens, underscores) |
| `pdfBlobUrl` | string | ✅ | HTTPS URL to PDF in Azure Blob Storage |

**Example:**
```json
{
  "correlationKey": "task-2024-001",
  "pdfBlobUrl": "https://mystorageaccount.blob.core.windows.net/processing-input/task-2024-001/document.pdf"
}
```

### Result Message (Output)

Received from queue: `processing-tasks-results`

#### Success Response
```json
{
  "correlationKey": "string",
  "status": "success",
  "resultsBlobUrl": "string"
}
```

#### Failure Response
```json
{
  "correlationKey": "string",
  "status": "failure",
  "errorMessage": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `correlationKey` | string | Same key from the task message |
| `status` | string | Either "success" or "failure" |
| `resultsBlobUrl` | string | URL to results ZIP (success only) |
| `errorMessage` | string | Error description (failure only) |

---

## Python Public APIs

### DocumentSplitter Class

Main class for document processing.

```python
from modules.document_splitter import DocumentSplitter

splitter = DocumentSplitter(
    api_key: str,           # Google Gemini API key (required)
    model: str = 'gemini-2.5-flash',  # Gemini model name
    timeout_seconds: int = 300        # API timeout in seconds
)
```

#### Methods

##### `extract_documents(pdf_path: str) -> List[Dict[str, Any]]`

Extract document information from a PDF using Gemini AI.

**Parameters:**
- `pdf_path` (str): Path to the PDF file

**Returns:**
- List of document dictionaries with extraction data

**Raises:**
- `ValueError`: If Gemini response is invalid
- `TimeoutError`: If API call exceeds timeout

**Example:**
```python
documents = splitter.extract_documents("combined.pdf")
for doc in documents:
    print(f"Found: {doc['DOC_TYPE']} (pages {doc['START_PAGE_NO']}-{doc['END_PAGE_NO']})")
```

##### `split_and_save(pdf_path: str, output_dir: str, base_filename: str = None) -> Dict[str, Any]`

Extract documents from PDF, split into separate files, and save results.

**Parameters:**
- `pdf_path` (str): Path to the input PDF file
- `output_dir` (str): Directory to save split files and results
- `base_filename` (str, optional): Base name for output files

**Returns:**
- Dictionary with extraction results and file locations

**Example:**
```python
result = splitter.split_and_save(
    "combined.pdf",
    "output/",
    base_filename="batch_001"
)
print(f"Created {result['total_documents']} documents")
```

---

### Convenience Function

```python
from modules import split_and_extract_documents

result = split_and_extract_documents(
    pdf_path: str,           # Input PDF file path (required)
    output_dir: str,         # Output directory (required)
    api_key: str = None,     # Gemini API key (default: from env)
    model: str = 'gemini-2.5-flash',
    base_filename: str = None
) -> Dict[str, Any]
```

**Example:**
```python
from modules import split_and_extract_documents

result = split_and_extract_documents(
    pdf_path="documents/combined.pdf",
    output_dir="output/split_docs"
)

print(f"Source: {result['source_pdf']}")
print(f"Total documents: {result['total_documents']}")

for doc in result['documents']:
    print(f"  {doc['DOC_TYPE']}: {doc['FILE_NAME']}")
```

---

### AzureStorageClient Class

Client for Azure Blob Storage operations with automatic retry.

```python
from modules.azure import AzureStorageClient

client = AzureStorageClient(
    account_name: str,  # Azure Storage account name
    access_key: str     # Azure Storage access key
)
```

#### Methods

##### `download_blob(blob_url: str, local_path: str) -> str`

Download a blob from Azure Storage with retry logic.

**Parameters:**
- `blob_url` (str): URL to the blob
- `local_path` (str): Local file path to save the downloaded blob

**Returns:**
- Path to the downloaded file

**Raises:**
- `ResourceNotFoundError`: If blob doesn't exist
- `AzureError`: If download fails after retries

##### `upload_file(container_name: str, blob_name: str, file_path: str, overwrite: bool = True) -> str`

Upload a file to Azure Blob Storage with retry logic.

**Parameters:**
- `container_name` (str): Name of the blob container
- `blob_name` (str): Name for the blob
- `file_path` (str): Path to the local file to upload
- `overwrite` (bool): Whether to overwrite existing blob

**Returns:**
- URL of the uploaded blob

##### `upload_bytes(container_name: str, blob_name: str, data: bytes, overwrite: bool = True) -> str`

Upload bytes data to Azure Blob Storage with retry logic.

**Returns:**
- URL of the uploaded blob

---

### Validation Functions

```python
from modules.validators import (
    validate_correlation_key,
    validate_blob_url,
    validate_pdf_file,
    ValidatedRequest,
    sanitize_url_for_logging,
    sanitize_error_message
)
```

##### `validate_correlation_key(key: str) -> str`

Validate correlation key against strict whitelist.

**Raises:**
- `ValidationError`: If key is invalid or contains unsafe characters

##### `validate_blob_url(url: str, allowed_containers: List[str]) -> str`

Validate blob URL is from authorized Azure Storage account.

**Raises:**
- `ValidationError`: If URL is invalid or unauthorized

##### `validate_pdf_file(pdf_path: str) -> None`

Validate PDF file size and structure.

**Raises:**
- `ValidationError`: If file is invalid, too large, or has too many pages

##### `ValidatedRequest.from_queue_message(message_body: bytes, allowed_containers: List[str]) -> ValidatedRequest`

Parse, validate, and create validated request from queue message.

---

## Document Schemas

### Common Fields (All Document Types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `DOC_TYPE` | string | ✅ | One of: INVOICE, OBL, HAWB, PACKING_LIST |
| `DOC_TYPE_CONFIDENCE` | float | ✅ | Confidence score 0.0 - 1.0 |
| `TOTAL_PAGES` | integer | ✅ | Page count for this document |
| `START_PAGE_NO` | integer | ✅ | 1-based start page number |
| `END_PAGE_NO` | integer | ✅ | 1-based end page number |
| `FILE_PATH` | string | ✅ | Path to split PDF file |
| `FILE_NAME` | string | ✅ | Name of split PDF file |

### Invoice Schema

| Field | Type | Description |
|-------|------|-------------|
| `INVOICE_NO` | string | Invoice number (preserved as-is) |
| `INVOICE_DATE` | string | 16-digit format: YYYYMMDD00000000 |
| `CURRENCY_ID` | string | 3-letter currency code (e.g., EUR) |
| `INCOTERMS` | string | INCOTERMS code only (e.g., FCA) |
| `INVOICE_AMOUNT` | number | Invoice amount (numeric) |
| `CUSTOMER_ID` | string | Customer identifier |

**Example:**
```json
{
  "DOC_TYPE": "INVOICE",
  "DOC_TYPE_CONFIDENCE": 0.95,
  "INVOICE_NO": "0004833/E",
  "INVOICE_DATE": "2025073000000000",
  "CURRENCY_ID": "EUR",
  "INCOTERMS": "FCA",
  "INVOICE_AMOUNT": 7632.00,
  "CUSTOMER_ID": "D004345",
  "TOTAL_PAGES": 2,
  "START_PAGE_NO": 1,
  "END_PAGE_NO": 2,
  "FILE_PATH": "output/doc_INVOICE_1_pages_1-2.pdf",
  "FILE_NAME": "doc_INVOICE_1_pages_1-2.pdf"
}
```

### OBL (Ocean Bill of Lading) Schema

| Field | Type | Description |
|-------|------|-------------|
| `CUSTOMER_NAME` | string | Customer/consignee name |
| `WEIGHT` | number | Total weight |
| `VOLUME` | number | Total volume |
| `INCOTERMS` | string | INCOTERMS code |

### HAWB (House Air Waybill) Schema

| Field | Type | Description |
|-------|------|-------------|
| `CUSTOMER_NAME` | string | Customer name |
| `CURRENCY` | string | Currency code |
| `CARRIER` | string | Carrier name |
| `HAWB_NUMBER` | string | HAWB number |
| `PIECES` | integer | Number of pieces |
| `WEIGHT` | number | Total weight |

### Packing List Schema

| Field | Type | Description |
|-------|------|-------------|
| `CUSTOMER_NAME` | string | Customer name |
| `PIECES` | integer | Number of pieces |
| `WEIGHT` | number | Total weight |

---

## Results File Structure

### ZIP Contents

```
{correlation_key}_results.zip
├── extraction_results.json
├── {base}_INVOICE_1_pages_1-2.pdf
├── {base}_PACKING_LIST_2_pages_3-3.pdf
└── ...
```

### extraction_results.json Format

```json
{
  "source_pdf": "string - path to original PDF",
  "output_directory": "string - output directory path",
  "total_documents": "integer - count of documents found",
  "documents": [
    { /* Document object with schema fields */ }
  ]
}
```

---

## Error Handling

### Error Types

| Exception | Description | Retry |
|-----------|-------------|-------|
| `ValidationError` | Invalid input (bad data) | ❌ No |
| `ConfigurationError` | Missing configuration | ❌ No |
| `ProcessingError (TRANSIENT)` | Network/API issues | ✅ Yes |
| `ProcessingError (PERMANENT)` | Bad input data | ❌ No |
| `ProcessingError (CRITICAL)` | System failures | ❌ No (alert) |

### Error Severity Levels

```python
from modules.validators import ErrorSeverity

ErrorSeverity.TRANSIENT   # Retry possible (network issues, rate limits)
ErrorSeverity.PERMANENT   # No retry needed (validation errors)
ErrorSeverity.CRITICAL    # Alert required (config errors, system failures)
```

### Validation Limits

| Limit | Value |
|-------|-------|
| Correlation key length | 1-128 characters |
| Correlation key pattern | Alphanumeric, hyphens, underscores |
| Blob URL max length | 2048 characters |
| PDF max size | 10 GB |
| PDF max pages | 500 |
| Max output documents | 100 |
