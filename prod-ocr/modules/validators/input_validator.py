"""Input validation and sanitization for processing requests."""
import re
import json
import os
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from typing import List, TypedDict
from pypdf import PdfReader

from .errors import ValidationError

CORRELATION_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]{1,128}$')
MAX_PDF_SIZE_BYTES = 10000 * 1024 * 1024  # 10000 MB
MAX_PAGES = 500
MAX_OUTPUT_FILES = 1000
ALLOWED_BLOB_DOMAINS = ['.blob.core.windows.net']


class ProcessingRequest(TypedDict):
    """Schema for processing request message."""
    correlationKey: str
    pdfBlobUrl: str


def validate_correlation_key(key: str) -> str:
    """Validate correlation key against strict whitelist.

    Prevents path traversal attacks by ensuring correlation_key
    contains only safe characters and cannot escape directories.

    Args:
        key: Correlation key to validate

    Returns:
        Validated correlation key

    Raises:
        ValidationError: If key is invalid or contains unsafe characters
    """
    if not key:
        raise ValidationError("Correlation key is required")

    if not CORRELATION_KEY_PATTERN.match(key):
        raise ValidationError(
            f"Invalid correlation key format. Must be 1-128 alphanumeric characters, "
            f"hyphens, or underscores. Got: {key[:50]}"
        )

    normalized = PurePosixPath(key)
    if len(normalized.parts) != 1 or str(normalized) != key:
        raise ValidationError(
            f"Correlation key must not contain path separators: {key[:50]}"
        )

    return key


def validate_blob_url(url: str, allowed_container: str) -> str:
    """Validate blob URL is from authorized Azure Storage account.

    Prevents SSRF attacks by ensuring URL points to Azure Blob Storage
    and is in an authorized container.

    Args:
        url: Blob URL to validate
        allowed_container: Allowed container name

    Returns:
        Validated blob URL

    Raises:
        ValidationError: If URL is invalid or unauthorized
    """
    if not url:
        raise ValidationError("Blob URL is required")

    if len(url) > 2048:
        raise ValidationError(f"Blob URL too long: {len(url)} characters (max: 2048)")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")

    if parsed.scheme != 'https':
        raise ValidationError(f"Blob URL must use HTTPS, got: {parsed.scheme}")

    if not parsed.hostname:
        raise ValidationError("Blob URL missing hostname")

    is_valid_domain = any(
        parsed.hostname.endswith(domain)
        for domain in ALLOWED_BLOB_DOMAINS
    )
    if not is_valid_domain:
        raise ValidationError(
            f"URL must be Azure Blob Storage (*.blob.core.windows.net), "
            f"got: {parsed.hostname}"
        )

    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) < 2:
        raise ValidationError(f"Invalid blob URL path format: {parsed.path}")

    container = path_parts[0]
    if container != allowed_container:
        raise ValidationError(
            f"Unauthorized container: {container}. "
            f"Allowed container: {allowed_container}"
        )

    return url


def validate_pdf_file(pdf_path: str) -> None:
    """Validate PDF file size and structure.

    Prevents resource exhaustion attacks by checking file size
    and page count before processing.

    Args:
        pdf_path: Path to PDF file

    Raises:
        ValidationError: If file is invalid, too large, or has too many pages
    """
    if not os.path.exists(pdf_path):
        raise ValidationError(f"PDF file not found: {pdf_path}")

    file_size = os.path.getsize(pdf_path)
    if file_size == 0:
        raise ValidationError("PDF file is empty")

    if file_size > MAX_PDF_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_PDF_SIZE_BYTES / (1024 * 1024)
        raise ValidationError(
            f"PDF file too large: {size_mb:.1f} MB (max: {max_mb:.1f} MB)"
        )

    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        if page_count == 0:
            raise ValidationError("PDF has no pages")

        if page_count > MAX_PAGES:
            raise ValidationError(
                f"PDF has too many pages: {page_count} (max: {MAX_PAGES})"
            )

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid PDF file or corrupted: {e}")


def parse_queue_message(message_body: bytes) -> ProcessingRequest:
    """Parse and validate queue message.

    Args:
        message_body: Raw message bytes from queue

    Returns:
        Parsed and validated processing request

    Raises:
        ValidationError: If message is invalid
    """
    try:
        decoded = message_body.decode('utf-8')
    except UnicodeDecodeError as e:
        raise ValidationError(f"Invalid UTF-8 encoding in message: {e}")

    try:
        data = json.loads(decoded)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in message: {e}")

    if not isinstance(data, dict):
        raise ValidationError(
            f"Expected JSON object, got {type(data).__name__}"
        )

    correlation_key = data.get('correlationKey') or data.get('correlation_key')
    pdf_blob_url = data.get('pdfBlobUrl') or data.get('pdf_blob_url')

    if not correlation_key:
        raise ValidationError("Missing required field: correlationKey")
    if not pdf_blob_url:
        raise ValidationError("Missing required field: pdfBlobUrl")

    if not isinstance(correlation_key, str):
        raise ValidationError(
            f"correlationKey must be string, got {type(correlation_key).__name__}"
        )
    if not isinstance(pdf_blob_url, str):
        raise ValidationError(
            f"pdfBlobUrl must be string, got {type(pdf_blob_url).__name__}"
        )

    return ProcessingRequest(
        correlationKey=correlation_key,
        pdfBlobUrl=pdf_blob_url
    )


class ValidatedRequest:
    """Immutable validated processing request."""

    def __init__(self, correlation_key: str, pdf_blob_url: str):
        """Initialize validated request.

        Args:
            correlation_key: Validated correlation key
            pdf_blob_url: Validated blob URL
        """
        self._correlation_key = correlation_key
        self._pdf_blob_url = pdf_blob_url

    @property
    def correlation_key(self) -> str:
        """Get correlation key."""
        return self._correlation_key

    @property
    def pdf_blob_url(self) -> str:
        """Get PDF blob URL."""
        return self._pdf_blob_url

    @classmethod
    def from_queue_message(
        cls,
        message_body: bytes,
        allowed_containers: List[str]
    ) -> 'ValidatedRequest':
        """Parse, validate, and create validated request from queue message.

        Args:
            message_body: Raw message bytes from queue
            allowed_containers: List of allowed blob containers

        Returns:
            Validated and immutable request object

        Raises:
            ValidationError: If message or fields are invalid
        """
        request = parse_queue_message(message_body)

        correlation_key = validate_correlation_key(request['correlationKey'])
        pdf_blob_url = validate_blob_url(request['pdfBlobUrl'], allowed_containers)

        return cls(correlation_key, pdf_blob_url)


def sanitize_url_for_logging(url: str) -> str:
    """Remove sensitive query parameters from URL for safe logging.

    Prevents SAS tokens and connection strings from appearing in logs.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL without query parameters
    """
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return url[:100] + "..." if len(url) > 100 else url


def sanitize_error_message(error: str) -> str:
    """Remove sensitive information from error messages.

    Prevents API keys and connection strings from appearing in logs.

    Args:
        error: Error message to sanitize

    Returns:
        Sanitized error message
    """
    sanitized = re.sub(
        r'AccountKey=[^;]+',
        'AccountKey=***REDACTED***',
        error
    )

    sanitized = re.sub(
        r'api[_-]?key["\s:=]+[a-zA-Z0-9]+',
        'api_key=***REDACTED***',
        sanitized,
        flags=re.IGNORECASE
    )

    sanitized = re.sub(
        r'\b[a-zA-Z0-9]{40,}\b',
        '***REDACTED***',
        sanitized
    )

    return sanitized
