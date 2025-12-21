# Development Guide

This guide covers development workflows, code standards, and contribution guidelines for the AI Document Processing System.

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Code Standards](#code-standards)
4. [Testing](#testing)
5. [Common Development Tasks](#common-development-tasks)
6. [Debugging](#debugging)

---

## Development Environment Setup

### 1. Prerequisites

```bash
# Python 3.9 or higher
python --version

# Azure Functions Core Tools v4
func --version

# uv (Python package manager)
uv --version

# Git
git --version
```

### 2. Clone and Setup

```bash
git clone <repository-url>
# Clone repository
git clone <repository-url>
cd ai-ocr-poc/prod-ocr

# Install dependencies (creates .venv automatically)
uv sync --extra dev --active

# Optional: activate the virtual environment if you want to run python directly
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
# macOS/Linux
source .venv/bin/activate
```

### 3. Configure Environment

```bash
# Copy example env file
```bash
cp .env.example .env

# Edit .env with your credentials
# GEMINI_API_KEY=...
# AZURE_STORAGE_ACCOUNT_NAME=...
# AZURE_STORAGE_ACCESS_KEY=...
```

### 4. IDE Setup (VS Code)

Recommended extensions:

- Python (ms-python.python)
- Azure Functions (ms-azuretools.vscode-azurefunctions)
- Pylance (ms-python.vscode-pylance)

Settings (`.vscode/settings.json`):

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true
}
```

---

## Project Structure

```text
prod-ocr/
├── function_app.py           # Azure Function entry point (queue trigger)
├── send_task.py              # Client script: upload PDF & send task to queue
├── get_results.py            # Client script: poll results queue & download ZIP
├── requirements.txt          # Python dependencies
├── host.json                 # Azure Functions host config
├── local.settings.json       # Local dev settings (git-ignored)
├── .env                      # Environment variables (git-ignored)
├── .env.example              # Example environment file
│
├── modules/                  # Core application modules
│   ├── __init__.py          # Exports: DocumentSplitter
│   │
│   ├── document_splitter/   # AI-powered document processing
│   │   ├── __init__.py
│   │   └── splitter.py      # DocumentSplitter class + extraction prompt
│   │
│   ├── azure/               # Azure Storage integrations
│   │   ├── __init__.py
│   │   └── storage.py       # AzureStorageClient (blob operations)
│   │
│   ├── validators/          # Input validation & security
│   │   ├── __init__.py      # Exports all validators
│   │   ├── errors.py        # ProcessingError, ValidationError, ConfigurationError
│   │   └── input_validator.py # ValidatedRequest, sanitize functions
│   │
│   └── utils/               # Utility functions
│       ├── __init__.py      # Exports: extract_pdf_pages, create_results_zip
│       ├── pdf_utils.py     # PDF page extraction (pypdf)
│       └── zip_utils.py     # ZIP file creation
│
├── docs/                    # Documentation
│   ├── README.md            # Documentation index
│   ├── PROJECT_OVERVIEW.md
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
│
└── split_output/            # Default output directory (local testing)
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `function_app.py` | Azure Function orchestration |
| `document_splitter` | AI-powered document analysis |
| `azure` | Azure Storage operations |
| `validators` | Input validation and security |
| `utils` | PDF and ZIP utilities |

---

## Code Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [flake8](https://flake8.pycqa.org/) for linting
- Maximum line length: 100 characters

### Docstrings

Use Google-style docstrings:

```python
def process_document(pdf_path: str, output_dir: str) -> dict:
    """Process a PDF document and extract structured data.
    
    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory for output files
        
    Returns:
        Dictionary with extraction results
        
    Raises:
        ValidationError: If input file is invalid
        ProcessingError: If processing fails
        
    Example:
        >>> result = process_document("doc.pdf", "output/")
        >>> print(result['total_documents'])
        3
    """
```

### Type Hints

Use type hints for all functions:

```python
from typing import List, Dict, Any, Optional

def extract_pages(
    pdf_path: str,
    start_page: int,
    end_page: int
) -> bytes:
    ...

def process_batch(
    files: List[str],
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    ...
```

### Error Handling

Use custom exceptions with severity:

```python
from modules.validators import (
    ValidationError,
    ProcessingError,
    ConfigurationError,
    ErrorSeverity
)

# Validation errors (no retry)
raise ValidationError("Invalid correlation key format")

# Processing errors (with severity)
raise ProcessingError(
    "Network timeout while downloading file",
    ErrorSeverity.TRANSIENT,  # Retry possible
    original_exception
)

# Configuration errors
raise ConfigurationError("GEMINI_API_KEY not configured")
```

### Logging

Use the logging module with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

# Debug: Detailed diagnostic info
logger.debug(f"Processing page {page_num}")

# Info: General operational messages
logger.info(f"Found {doc_count} documents")

# Warning: Unexpected but handled situations
logger.warning(f"Retry attempt {attempt}/{max_retries}")

# Error: Error conditions that were handled
logger.error(f"Failed to process: {sanitized_error}")

# Critical: System-level failures
logger.critical(f"Configuration error: {error}")
```

---

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=modules --cov-report=html

# Run specific test file
uv run pytest tests/test_splitter.py

# Run specific test
uv run pytest tests/test_splitter.py::test_extract_documents
```

### Test Structure

```text
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_splitter.py      # Document splitter tests
├── test_storage.py       # Azure storage tests
├── test_validators.py    # Validation tests
├── test_utils.py         # Utility function tests
└── fixtures/             # Test data
    ├── sample.pdf
    └── expected_output.json
```

### Writing Tests

```python
import pytest
from modules.document_splitter import DocumentSplitter
from modules.validators import ValidationError

class TestDocumentSplitter:
    """Tests for DocumentSplitter class."""
    
    @pytest.fixture
    def splitter(self, mock_api_key):
        """Create a splitter instance for testing."""
        return DocumentSplitter(api_key=mock_api_key)
    
    def test_extract_documents_success(self, splitter, sample_pdf):
        """Test successful document extraction."""
        documents = splitter.extract_documents(sample_pdf)
        
        assert len(documents) > 0
        assert all('DOC_TYPE' in doc for doc in documents)
    
    def test_extract_documents_invalid_pdf(self, splitter, invalid_pdf):
        """Test handling of invalid PDF."""
        with pytest.raises(ValidationError):
            splitter.extract_documents(invalid_pdf)
```

---

## Common Development Tasks

### Adding a New Document Type

1. Update the extraction prompt in `splitter.py`:

    ```python
    UNIFIED_EXTRACTION_PROMPT = """
    ...
    Supported Document Types:
    1. Invoice
    2. OBL (Ocean Bill of Lading)
    3. HAWB (House Air Waybill)
    4. Packing List
    5. NEW_TYPE (Description)  # Add new type

    ...
    TYPE 5: NEW_TYPE
    - FIELD_1: Description
    - FIELD_2: Description
    ...
    """
    ```

2. Update documentation with new schema

3. Add tests for new document type

### Adding a New Validation Rule

1. Add validation function in `input_validator.py`:

   ```python
   def validate_new_field(value: str) -> str:
       """Validate new field.
       
       Args:
           value: Field value to validate
           
       Returns:
           Validated value
           
       Raises:
           ValidationError: If validation fails
       """
       if not value:
           raise ValidationError("Field is required")
       # Add validation logic
       return value
   ```

2. Export in `validators/__init__.py`

3. Add tests

### Adding a New Azure Storage Operation

1. Add method to `AzureStorageClient` in `storage.py`:

```python
def new_operation(self, param: str) -> str:
    """Description of operation.
    
    Args:
        param: Parameter description
        
    Returns:
        Return value description
        
    Raises:
        AzureError: If operation fails
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Implementation
            return result
        except (ServiceRequestError, ServiceResponseError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY_SECONDS * (2 ** attempt))
```

---

## Debugging

### Local Function Debugging

1. Set breakpoints in VS Code
2. Use F5 to start debugging (uses `launch.json`)
3. Send test messages to local queue

### Debugging Tips

```python
# Add temporary debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print intermediate results
logger.debug(f"Gemini response: {response.text[:500]}")
logger.debug(f"Parsed documents: {json.dumps(documents, indent=2)}")
```

### Azure Functions Debugging

```bash
# Stream live logs
func azure functionapp logstream <app-name>

# View Application Insights
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "traces | take 100"
```

### Common Debug Scenarios

| Scenario | Approach |
|----------|----------|
| API response parsing | Log raw response text |
| PDF processing | Check page counts, sizes |
| Queue messages | Verify JSON structure |
| Storage operations | Check URLs, permissions |
| Validation failures | Log input values |

### Environment Variable Debugging

```python
import os

# Log all relevant env vars (without values)
env_vars = [
    'GEMINI_API_KEY',
    'AZURE_STORAGE_ACCOUNT_NAME',
    'AZURE_STORAGE_ACCESS_KEY',
    'AzureWebJobsStorage'
]

for var in env_vars:
    value = os.getenv(var)
    logger.debug(f"{var}: {'SET' if value else 'NOT SET'}")
```

---

## Release Checklist

Before deploying:

- [ ] All tests pass (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] No linting errors (`flake8`)
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Version number updated (if applicable)
- [ ] CHANGELOG updated
- [ ] Security review completed
