# Modules

Core application modules for the AI Document Processing System.

## Module Overview

| Module | Description |
|--------|-------------|
| [document_splitter](./document_splitter/) | AI-powered document analysis and PDF splitting |
| [azure](./azure/) | Azure Blob Storage operations |
| [validators](./validators/) | Input validation and security |
| [utils](./utils/) | PDF and ZIP utility functions |

## Package Exports

```python
# modules/__init__.py
from .document_splitter import DocumentSplitter

__all__ = ['DocumentSplitter']
```

## Dependencies Between Modules

```
function_app.py
    │
    ├── modules.azure.AzureStorageClient
    │       └── Blob upload/download
    │
    ├── modules.document_splitter.DocumentSplitter
    │       └── modules.utils.extract_pdf_pages
    │
    ├── modules.utils.create_results_zip
    │
    └── modules.validators.*
            ├── ValidatedRequest
            ├── ValidationError
            ├── ProcessingError
            └── sanitize functions
```
