# Validators Module

Input validation, security enforcement, and custom error types.

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Exports all validators and errors |
| `errors.py` | Custom exception classes |
| `input_validator.py` | Validation functions and `ValidatedRequest` class |

## Exports

```python
from modules.validators import (
    # Validation functions
    validate_correlation_key,
    validate_blob_url,
    validate_pdf_file,
    ValidatedRequest,
    sanitize_url_for_logging,
    sanitize_error_message,
    
    # Error classes
    ValidationError,
    ProcessingError,
    ConfigurationError,
    ErrorSeverity
)
```

---

## Error Classes

### ValidationError

Raised when input validation fails. **No retry** - bad data won't improve.

```python
class ValidationError(Exception):
    def __init__(self, message: str, original: Exception = None)
```

### ProcessingError

Raised during processing with severity classification.

```python
class ProcessingError(Exception):
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity,
        original: Exception = None
    )
```

### ConfigurationError

Raised when required configuration is missing.

```python
class ConfigurationError(Exception):
    pass
```

### ErrorSeverity

```python
class ErrorSeverity(Enum):
    TRANSIENT = "transient"   # Retry possible (network, rate limits)
    PERMANENT = "permanent"   # No retry (bad input)
    CRITICAL = "critical"     # Alert required (system failure)
```

---

## Validation Functions

### validate_correlation_key

Validates correlation key against strict whitelist.

```python
key = validate_correlation_key(key: str) -> str
```

**Rules:**
- 1-128 characters
- Alphanumeric, hyphens, underscores only
- No path separators (prevents traversal)

**Pattern:** `^[a-zA-Z0-9\-_]{1,128}$`

### validate_blob_url

Validates blob URL is from authorized Azure Storage.

```python
url = validate_blob_url(
    url: str,
    allowed_containers: List[str]
) -> str
```

**Rules:**
- Must use HTTPS
- Must be `*.blob.core.windows.net`
- Container must be in allowlist
- Max 2048 characters

### validate_pdf_file

Validates PDF file before processing.

```python
validate_pdf_file(pdf_path: str) -> None
```

**Rules:**
- File must exist
- Not empty
- Max size: 10 GB
- Max pages: 500
- Valid PDF structure

---

## ValidatedRequest Class

Immutable validated request from queue message.

```python
class ValidatedRequest:
    correlation_key: str  # Validated correlation key
    pdf_blob_url: str     # Validated blob URL
    
    @classmethod
    def from_queue_message(
        cls,
        message_body: bytes,
        allowed_containers: List[str]
    ) -> 'ValidatedRequest'
```

**Usage:**

```python
validated = ValidatedRequest.from_queue_message(
    msg.get_body(),
    ['processing-input', 'trusted-uploads']
)
print(validated.correlation_key)
print(validated.pdf_blob_url)
```

---

## Sanitization Functions

### sanitize_url_for_logging

Remove sensitive query parameters (SAS tokens).

```python
safe_url = sanitize_url_for_logging(url: str) -> str
# "https://storage.blob.../path?sig=xxx" -> "https://storage.blob.../path"
```

### sanitize_error_message

Remove sensitive data from error messages.

```python
safe_msg = sanitize_error_message(error: str) -> str
```

**Removes:**
- `AccountKey=...`
- API keys
- Long alphanumeric strings (40+ chars)

---

## Validation Limits

| Limit | Value |
|-------|-------|
| Correlation key length | 1-128 characters |
| Blob URL max length | 2048 characters |
| PDF max size | 10 GB |
| PDF max pages | 500 |
| Max output documents | 1000 |

## Security Features

- ✅ Path traversal prevention
- ✅ SSRF prevention (domain allowlist)
- ✅ Container allowlist enforcement
- ✅ Sensitive data sanitization
- ✅ Input size limits
