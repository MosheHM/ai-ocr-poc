# function_app.py

Azure Function entry point with queue trigger for document processing.

## Overview

This is the main serverless function that processes PDF documents from an Azure Queue.

## Function: process_pdf_file

```python
@app.queue_trigger(
    arg_name="msg",
    queue_name="processing-tasks",
    connection="AzureWebJobsStorage"
)
@app.queue_output(
    arg_name="outputQueue",
    queue_name="processing-tasks-results",
    connection="AzureWebJobsStorage"
)
def process_pdf_file(msg: func.QueueMessage, outputQueue: func.Out[str]) -> None
```

## Processing Pipeline

```
1. Validate input message
        ↓
2. Download PDF from blob storage
        ↓
3. Process with Gemini AI (extract & classify documents)
        ↓
4. Split PDF into separate files
        ↓
5. Package results as ZIP
        ↓
6. Upload ZIP to blob storage
        ↓
7. Send result message to output queue
```

## Input Message

Queue: `processing-tasks`

```json
{
  "correlationKey": "unique-task-id",
  "pdfBlobUrl": "https://storage.blob.core.windows.net/processing-input/..."
}
```

## Output Messages

Queue: `processing-tasks-results`

**Success:**
```json
{
  "correlationKey": "unique-task-id",
  "status": "success",
  "resultsBlobUrl": "https://storage.blob.core.windows.net/processing-results/..."
}
```

**Failure:**
```json
{
  "correlationKey": "unique-task-id",
  "status": "failure",
  "errorMessage": "Error description"
}
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| AzureWebJobsStorage | ✅ | - | Storage connection string |
| AZURE_STORAGE_ACCOUNT_NAME | ✅ | - | Storage account name |
| AZURE_STORAGE_ACCESS_KEY | ✅ | - | Storage access key |
| GEMINI_API_KEY | ✅ | - | Gemini API key |
| GEMINI_MODEL | ❌ | gemini-2.5-flash | Model to use |
| GEMINI_TIMEOUT_SECONDS | ❌ | 300 | API timeout |
| RESULTS_CONTAINER | ❌ | processing-results | Results container |

## Constants

```python
ALLOWED_INPUT_CONTAINERS = ['processing-input', 'trusted-uploads']
RESULTS_CONTAINER = 'processing-results'  # or from env
```

## Singleton Clients

Clients are lazily initialized as singletons:

```python
_storage_client: Optional[AzureStorageClient] = None
_document_splitter: Optional[DocumentSplitter] = None

def get_storage_client() -> AzureStorageClient
def get_document_splitter() -> DocumentSplitter
```

## Helper Functions

| Function | Description |
|----------|-------------|
| `create_secure_temp_dir()` | Create temp directory with 0o700 permissions |
| `cleanup_temp_dir(path)` | Safely remove temp directory |
| `download_pdf(client, url, dest)` | Download and validate PDF |
| `process_pdf(splitter, path, output_dir)` | Extract and split documents |
| `package_results(output_dir, results, key)` | Create results ZIP |
| `upload_results(client, zip_path, key, container)` | Upload ZIP to blob |
| `send_success_result(queue, key, url)` | Send success message |
| `send_error_result(queue, key, message)` | Send error message |

## Error Handling

| Error Type | Severity | Action |
|------------|----------|--------|
| ConfigurationError | Critical | Send error, raise (stop function) |
| ValidationError | Permanent | Send error, don't retry |
| ProcessingError (TRANSIENT) | Transient | Send error, raise (allows retry) |
| ProcessingError (PERMANENT) | Permanent | Send error, don't retry |
| ProcessingError (CRITICAL) | Critical | Send error, raise |
| Exception | Unknown | Send error, raise |

## Temporary File Handling

```python
temp_dir = create_secure_temp_dir()  # /tmp/docproc_{random_hex}
try:
    # Process files in temp_dir
finally:
    cleanup_temp_dir(temp_dir)  # Always cleanup
```

## Host Configuration

See `host.json`:

```json
{
  "functionTimeout": "00:10:00",
  "extensions": {
    "queues": {
      "batchSize": 1,
      "maxDequeueCount": 3,
      "visibilityTimeout": "00:05:00"
    }
  }
}
```
