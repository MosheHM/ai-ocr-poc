# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Standalone document splitting tool that uses Google Gemini AI to process multi-document PDFs. Automatically detects document boundaries, classifies document types (Invoice, OBL, HAWB, Packing List), extracts structured data, and splits into separate PDF files.

Supports two modes:
1. **Local Mode**: Direct CLI processing
2. **Azure Functions Mode**: Serverless queue-based processing with Azure Functions

This is a self-contained production deployment version extracted from a larger AI-OCR POC project.

## Common Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env  # Add GEMINI_API_KEY, AZURE_STORAGE_ACCOUNT_NAME, and AZURE_STORAGE_ACCESS_KEY

# Local mode - Direct processing
python split_documents.py "path/to/combined.pdf"
python split_documents.py "path/to/file.pdf" --output-dir="custom_output"
python split_documents.py "path/to/file.pdf" --model="gemini-2.5-flash"

# Azure Functions mode - Run locally
func start  # Starts the function, listens to processing-tasks queue

# Send task to Azure Queue
python send_task.py "path/to/document.pdf"
python send_task.py "document.pdf" --container=my-input --correlation-key=custom-123

# Get results from Azure Queue
python get_results.py --correlation-key=<key>
python get_results.py --correlation-key=<key> --download=./results
```

## Project Structure

```
prod-ocr/
├── split_documents.py              # CLI for local processing
├── function_app.py                 # Azure Function with queue trigger
├── send_task.py                    # Client script for sending tasks
├── get_results.py                  # Client script for retrieving results
├── host.json                       # Azure Functions host configuration
├── local.settings.json             # Local development settings
├── modules/
│   ├── __init__.py                # Exports split_and_extract_documents()
│   ├── document_splitter/
│   │   ├── splitter.py            # DocumentSplitter class
│   │   └── __init__.py
│   ├── azure/
│   │   ├── storage.py             # AzureStorageClient (blob operations)
│   │   └── __init__.py
│   ├── system_prompts/
│   │   ├── extraction_prompts.py  # UNIFIED_EXTRACTION_PROMPT
│   │   └── __init__.py
│   └── utils/
│       ├── pdf_utils.py           # PDF manipulation (pypdf)
│       ├── zip_utils.py           # ZIP creation for results
│       └── __init__.py
├── split_output/                   # Default output directory (local mode)
├── requirements.txt
└── .env                           # Not committed (copy from .env.example)
```

## Architecture

### Local Mode Workflow
```
Combined PDF → Gemini AI Analysis → Document Detection & Classification → Data Extraction → Split into Separate PDFs + JSON Results
```

### Azure Functions Mode Workflow
```
Client: Upload PDF to Blob Storage → Send Task Message to Queue
   ↓
Azure Function: Triggered by Queue → Download PDF → Process (Gemini AI) → Create ZIP → Upload ZIP → Send Result to Output Queue
```

### Key Components

**Azure Function** (`function_app.py`):
- Queue-triggered serverless function
- `@app.queue_trigger` - Listens to `processing-tasks` queue
- `@app.queue_output` - Sends results to `processing-tasks-results` queue
- Processes task message: downloads PDF, extracts/splits documents, creates ZIP, uploads to blob storage
- Automatic error handling and result message generation
- Uses temporary directories (auto-cleanup)

**Message Format**:
- Task message: `{"correlationKey": "...", "pdfBlobUrl": "..."}`
- Result message (success): `{"correlationKey": "...", "status": "success", "resultsBlobUrl": "..."}`
- Result message (failure): `{"correlationKey": "...", "status": "failure", "errorMessage": "..."}`

**Azure Storage Client** (`modules/azure/storage.py`):
- `AzureStorageClient` - Blob operations (upload_file, download_blob, upload_bytes)
- Initialized with storage account name and access key
- Used by both the function and client scripts

**DocumentSplitter** (`modules/document_splitter/splitter.py`):
- Main class orchestrating the entire process
- `extract_documents()` - Sends PDF to Gemini with `UNIFIED_EXTRACTION_PROMPT`, returns list of document dicts
- `split_and_save()` - Complete pipeline: extract metadata, split PDF pages, save individual files, write JSON results
- Uses `google.genai.Client` for API calls with model `gemini-2.5-flash` (default)

**Unified Extraction Approach**:
- Single API call processes entire PDF (all pages at once)
- Gemini AI detects document boundaries, classifies types, extracts fields, and provides page ranges
- Returns JSON array with one object per detected document
- Each document includes `START_PAGE_NO`, `END_PAGE_NO`, `DOC_TYPE`, `DOC_TYPE_CONFIDENCE`, and type-specific fields

**Utilities**:
- `pdf_utils.py` - PDF operations (extract_pdf_pages, combine_pdf_pages, split_pdf_to_pages) using pypdf
- `zip_utils.py` - ZIP creation (create_results_zip) for packaging split PDFs + results JSON

**Prompt System** (`modules/system_prompts/extraction_prompts.py`):
- `UNIFIED_EXTRACTION_PROMPT` - Complete instruction set for Gemini
- Defines document types, schemas, extraction rules, and output format
- Critical rules: INVOICE_DATE format (16-digit YYYYMMDD00000000), INCOTERMS (code only), DOC_TYPE_CONFIDENCE scoring

### Output Format

**JSON Results** (`{filename}_extraction_results.json`):
```json
{
  "source_pdf": "path/to/input.pdf",
  "output_directory": "split_output",
  "total_documents": 2,
  "documents": [
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
      "FILE_PATH": "split_output/filename_INVOICE_1_pages_1-2.pdf",
      "FILE_NAME": "filename_INVOICE_1_pages_1-2.pdf"
    }
  ]
}
```

**Split PDF Files**: Named `{base}_{DOC_TYPE}_{index}_pages_{start}-{end}.pdf`

## Document Types & Schemas

Defined in `UNIFIED_EXTRACTION_PROMPT`:

**Common Fields** (all types):
- `DOC_TYPE`: "INVOICE" | "OBL" | "HAWB" | "PACKING_LIST"
- `DOC_TYPE_CONFIDENCE`: Float 0-1 (e.g., 0.95 = high confidence)
- `TOTAL_PAGES`: Page count for this document
- `START_PAGE_NO`: 1-based page where document starts
- `END_PAGE_NO`: 1-based page where document ends

**Type-Specific Fields**:
- **INVOICE**: INVOICE_NO, INVOICE_DATE (16-digit), CURRENCY_ID, INCOTERMS (code only), INVOICE_AMOUNT, CUSTOMER_ID
- **OBL**: CUSTOMER_NAME, WEIGHT, VOLUME, INCOTERMS
- **HAWB**: CUSTOMER_NAME, CURRENCY, CARRIER, HAWB_NUMBER, PIECES, WEIGHT
- **PACKING_LIST**: CUSTOMER_NAME, PIECES, WEIGHT

## Configuration

**Local Settings** (`local.settings.json` for Azure Functions):
- `AzureWebJobsStorage` - Azure Storage connection string (required for Functions runtime)
- `AZURE_STORAGE_ACCOUNT_NAME` - Azure Storage account name (required)
- `AZURE_STORAGE_ACCESS_KEY` - Azure Storage access key (required)
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `GEMINI_MODEL` - Model to use (default: gemini-2.5-flash)
- `RESULTS_CONTAINER` - Blob container for result ZIPs (default: processing-results)

**Environment Variables** (`.env` file for local mode and client scripts):
- `GEMINI_API_KEY` - Google Gemini API key
- `AZURE_STORAGE_ACCOUNT_NAME` - Azure Storage account name
- `AZURE_STORAGE_ACCESS_KEY` - Azure Storage access key

**Azure Resources Required** (Azure Functions mode):
- Function App (Python 3.9+, Consumption or Premium plan)
- Storage Account
- Queues: `processing-tasks`, `processing-tasks-results`
- Blob containers: `processing-input` (for PDFs), `processing-results` (for ZIP files)

## Public API

**Local Processing**:
```python
from modules import split_and_extract_documents

result = split_and_extract_documents(
    pdf_path="combined_docs.pdf",
    output_dir="output/splits",
    api_key=None,  # Optional, defaults to GEMINI_API_KEY env var
    model="gemini-2.5-flash",
    base_filename=None  # Optional, defaults to input filename
)

# Returns dict with structure shown in Output Format section above
print(f"Found {result['total_documents']} documents")
for doc in result['documents']:
    print(f"{doc['DOC_TYPE']}: {doc['FILE_PATH']}")
```

**Azure Functions Processing**:
```python
# The function_app.py handles this automatically
# Just send messages to the queue and Azure Functions will process them

# Client example - Send task
from azure.storage.queue import QueueClient
import json
import os

account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
access_key = os.getenv('AZURE_STORAGE_ACCESS_KEY')
account_url = f"https://{account_name}.queue.core.windows.net"

queue_client = QueueClient(
    account_url=account_url,
    queue_name="processing-tasks",
    credential=access_key
)
message = {
    "correlationKey": "unique-id",
    "pdfBlobUrl": "https://..."
}
queue_client.send_message(json.dumps(message))

# Client example - Get results
results_queue = QueueClient(
    account_url=account_url,
    queue_name="processing-tasks-results",
    credential=access_key
)
messages = results_queue.receive_messages()
for msg in messages:
    result = json.loads(msg.content)
    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        print(f"Results: {result['resultsBlobUrl']}")
```

## Important Implementation Details

1. **Single API Call**: Entire PDF processed in one Gemini request, not page-by-page
2. **Page Numbering**: All page numbers are 1-indexed, both in API responses and PDF operations
3. **JSON Cleaning**: Response text is cleaned of markdown code blocks before parsing (splitter.py:148)
4. **Error Handling**: JSON parsing failures raise `ValueError` with logged debug info
5. **File Naming**: Output files include document type, sequential index, and page range for traceability
6. **Temporary Storage**: Azure Function uses temporary directories that are automatically cleaned up after processing
7. **Message Correlation**: `correlationKey` field (camelCase) links request/response messages across queues
8. **ZIP Results**: All split PDFs + extraction_results.json packaged in a single ZIP file
9. **Serverless Scaling**: Azure Functions automatically scales based on queue length
10. **Result Status**: Result messages have SUCCESS/FAILURE status with either resultsBlobUrl or errorMessage
