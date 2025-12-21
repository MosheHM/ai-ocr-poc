# Azure Module

Azure Blob Storage operations with automatic retry logic.

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Exports `AzureStorageClient` |
| `storage.py` | `AzureStorageClient` class implementation |

## Classes

### AzureStorageClient

Client for Azure Blob Storage with built-in retry logic.

```python
from modules.azure import AzureStorageClient

client = AzureStorageClient(
    account_name: str,  # Azure Storage account name
    access_key: str     # Azure Storage access key
)
```

## Methods

### download_blob

Download a blob from Azure Storage.

```python
local_path = client.download_blob(
    blob_url: str,      # Full URL to blob
    local_path: str     # Where to save locally
) -> str               # Returns local path
```

**Raises:**
- `ResourceNotFoundError` - Blob doesn't exist
- `AzureError` - Download failed after retries

### upload_file

Upload a local file to blob storage.

```python
blob_url = client.upload_file(
    container_name: str,    # Container name
    blob_name: str,         # Blob path/name
    file_path: str,         # Local file to upload
    overwrite: bool = True  # Overwrite if exists
) -> str                   # Returns blob URL
```

**Raises:**
- `FileNotFoundError` - Local file doesn't exist
- `AzureError` - Upload failed after retries

### upload_bytes

Upload bytes data directly to blob storage.

```python
blob_url = client.upload_bytes(
    container_name: str,
    blob_name: str,
    data: bytes,
    overwrite: bool = True
) -> str
```

## Retry Configuration

| Setting | Value |
|---------|-------|
| MAX_RETRIES | 3 |
| RETRY_DELAY_SECONDS | 2 (with exponential backoff) |

Retry applies to:
- `ServiceRequestError` (network issues)
- `ServiceResponseError` (server errors)

## Usage Example

```python
from modules.azure import AzureStorageClient
import os

client = AzureStorageClient(
    account_name=os.getenv('AZURE_STORAGE_ACCOUNT_NAME'),
    access_key=os.getenv('AZURE_STORAGE_ACCESS_KEY')
)

# Upload a file
url = client.upload_file(
    container_name="processing-input",
    blob_name="task-123/document.pdf",
    file_path="./document.pdf"
)

# Download a file
client.download_blob(
    blob_url=url,
    local_path="./downloaded.pdf"
)
```

## Security

- Paths are sanitized before logging (only filename shown)
- Connection uses HTTPS
- Access key should be stored securely (Key Vault in production)
