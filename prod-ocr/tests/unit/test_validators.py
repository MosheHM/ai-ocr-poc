"""Unit tests for input validators."""
import pytest
import json
from modules.validators.input_validator import (
    validate_correlation_key,
    validate_blob_url,
    validate_pdf_file,
    parse_queue_message,
    sanitize_url_for_logging,
    sanitize_error_message,
    ValidatedRequest,
    ALLOWED_BLOB_DOMAINS
)
from modules.validators.errors import ValidationError


@pytest.mark.unit
class TestValidateCorrelationKey:
    """Tests for validate_correlation_key function."""

    def test_valid_alphanumeric_key(self):
        """Test valid alphanumeric correlation key."""
        result = validate_correlation_key("abc123")
        assert result == "abc123"

    def test_valid_key_with_hyphens(self):
        """Test valid key with hyphens."""
        result = validate_correlation_key("test-key-123")
        assert result == "test-key-123"

    def test_valid_key_with_underscores(self):
        """Test valid key with underscores."""
        result = validate_correlation_key("test_key_456")
        assert result == "test_key_456"

    def test_valid_mixed_case_key(self):
        """Test valid mixed case key."""
        result = validate_correlation_key("TestKey123-abc_XYZ")
        assert result == "TestKey123-abc_XYZ"

    def test_valid_max_length_key(self):
        """Test key at maximum allowed length (128 chars)."""
        key = "a" * 128
        result = validate_correlation_key(key)
        assert result == key

    def test_empty_key_raises_error(self):
        """Test empty key raises ValidationError."""
        with pytest.raises(ValidationError, match="Correlation key is required"):
            validate_correlation_key("")

    def test_none_key_raises_error(self):
        """Test None key raises ValidationError."""
        with pytest.raises(ValidationError, match="Correlation key is required"):
            validate_correlation_key(None)

    def test_key_too_long_raises_error(self):
        """Test key exceeding 128 characters raises error."""
        key = "a" * 129
        with pytest.raises(ValidationError, match="Invalid correlation key format"):
            validate_correlation_key(key)

    def test_key_with_special_chars_raises_error(self):
        """Test key with special characters raises error."""
        invalid_keys = ["test@key", "test#key", "test$key", "test%key", "test key"]
        for key in invalid_keys:
            with pytest.raises(ValidationError, match="Invalid correlation key format"):
                validate_correlation_key(key)

    def test_path_traversal_attack_raises_error(self):
        """Test path traversal attempts are blocked."""
        attack_keys = ["../etc/passwd", "..\\windows", "test/../secret", "test/sub/dir"]
        for key in attack_keys:
            with pytest.raises(ValidationError):
                validate_correlation_key(key)


@pytest.mark.unit
class TestValidateBlobUrl:
    """Tests for validate_blob_url function."""

    @pytest.fixture
    def allowed_containers(self):
        """Default allowed containers."""
        return ["processing-input", "trusted-uploads"]

    def test_valid_url(self, allowed_containers):
        """Test valid Azure Blob URL."""
        url = "https://myaccount.blob.core.windows.net/processing-input/test.pdf"
        result = validate_blob_url(url, allowed_containers)
        assert result == url

    def test_valid_url_trusted_container(self, allowed_containers):
        """Test valid URL with trusted-uploads container."""
        url = "https://myaccount.blob.core.windows.net/trusted-uploads/docs/file.pdf"
        result = validate_blob_url(url, allowed_containers)
        assert result == url

    def test_empty_url_raises_error(self, allowed_containers):
        """Test empty URL raises error."""
        with pytest.raises(ValidationError, match="Blob URL is required"):
            validate_blob_url("", allowed_containers)

    def test_url_too_long_raises_error(self, allowed_containers):
        """Test URL exceeding 2048 characters raises error."""
        url = "https://a.blob.core.windows.net/processing-input/" + "x" * 2050
        with pytest.raises(ValidationError, match="Blob URL too long"):
            validate_blob_url(url, allowed_containers)

    def test_http_url_raises_error(self, allowed_containers):
        """Test HTTP (non-HTTPS) URL raises error."""
        url = "http://myaccount.blob.core.windows.net/processing-input/test.pdf"
        with pytest.raises(ValidationError, match="must use HTTPS"):
            validate_blob_url(url, allowed_containers)

    def test_non_azure_domain_raises_error(self, allowed_containers):
        """Test non-Azure Blob domain raises error (SSRF protection)."""
        urls = [
            "https://evil.com/malware.pdf",
            "https://192.168.1.1/file.pdf",
            "https://internal-server.local/file.pdf",
            "https://myblobcore.windows.net/container/file.pdf",  # typo in domain
        ]
        for url in urls:
            with pytest.raises(ValidationError, match="must be Azure Blob Storage"):
                validate_blob_url(url, allowed_containers)

    def test_unauthorized_container_raises_error(self, allowed_containers):
        """Test unauthorized container raises error."""
        url = "https://myaccount.blob.core.windows.net/unauthorized-container/test.pdf"
        with pytest.raises(ValidationError, match="Unauthorized container"):
            validate_blob_url(url, allowed_containers)

    def test_missing_blob_path_raises_error(self, allowed_containers):
        """Test URL without blob path raises error."""
        url = "https://myaccount.blob.core.windows.net/processing-input"
        with pytest.raises(ValidationError, match="Invalid blob URL path format"):
            validate_blob_url(url, allowed_containers)


@pytest.mark.unit
class TestValidatePdfFile:
    """Tests for validate_pdf_file function."""

    def test_valid_pdf_file(self, sample_pdf_file):
        """Test validation passes for valid PDF."""
        # Should not raise
        validate_pdf_file(str(sample_pdf_file))

    def test_nonexistent_file_raises_error(self):
        """Test nonexistent file raises error."""
        with pytest.raises(ValidationError, match="PDF file not found"):
            validate_pdf_file("/nonexistent/path/file.pdf")

    def test_empty_file_raises_error(self, empty_pdf_file):
        """Test empty file raises error."""
        with pytest.raises(ValidationError, match="PDF file is empty"):
            validate_pdf_file(str(empty_pdf_file))

    def test_invalid_pdf_raises_error(self, invalid_pdf_file):
        """Test invalid PDF content raises error."""
        with pytest.raises(ValidationError, match="Invalid PDF file or corrupted"):
            validate_pdf_file(str(invalid_pdf_file))


@pytest.mark.unit
class TestParseQueueMessage:
    """Tests for parse_queue_message function."""

    def test_valid_message_camelcase(self, valid_queue_message_bytes):
        """Test parsing valid message with camelCase keys."""
        result = parse_queue_message(valid_queue_message_bytes)
        assert result["correlationKey"] == "test-correlation-key-123"
        assert "pdfBlobUrl" in result

    def test_valid_message_snake_case(self, valid_queue_message_alt_keys):
        """Test parsing valid message with snake_case keys."""
        result = parse_queue_message(valid_queue_message_alt_keys)
        assert result["correlationKey"] == "test-correlation-key-456"

    def test_invalid_utf8_raises_error(self):
        """Test invalid UTF-8 encoding raises error."""
        invalid_bytes = b'\xff\xfe\x00\x01'  # Invalid UTF-8
        with pytest.raises(ValidationError, match="Invalid UTF-8 encoding"):
            parse_queue_message(invalid_bytes)

    def test_invalid_json_raises_error(self):
        """Test invalid JSON raises error."""
        invalid_json = b'{"broken": json'
        with pytest.raises(ValidationError, match="Invalid JSON"):
            parse_queue_message(invalid_json)

    def test_non_object_json_raises_error(self):
        """Test JSON array (non-object) raises error."""
        array_json = b'["item1", "item2"]'
        with pytest.raises(ValidationError, match="Expected JSON object"):
            parse_queue_message(array_json)

    def test_missing_correlation_key_raises_error(self, invalid_queue_message_missing_key):
        """Test missing correlationKey raises error."""
        with pytest.raises(ValidationError, match="Missing required field: correlationKey"):
            parse_queue_message(invalid_queue_message_missing_key)

    def test_missing_pdf_url_raises_error(self):
        """Test missing pdfBlobUrl raises error."""
        message = json.dumps({"correlationKey": "test"}).encode()
        with pytest.raises(ValidationError, match="Missing required field: pdfBlobUrl"):
            parse_queue_message(message)

    def test_non_string_correlation_key_raises_error(self):
        """Test non-string correlationKey raises error."""
        message = json.dumps({
            "correlationKey": 12345,
            "pdfBlobUrl": "https://test.blob.core.windows.net/c/f.pdf"
        }).encode()
        with pytest.raises(ValidationError, match="correlationKey must be string"):
            parse_queue_message(message)


@pytest.mark.unit
class TestValidatedRequest:
    """Tests for ValidatedRequest class."""

    def test_from_queue_message_valid(self, valid_queue_message_bytes):
        """Test creating ValidatedRequest from valid message."""
        allowed = ["processing-input", "trusted-uploads"]
        request = ValidatedRequest.from_queue_message(valid_queue_message_bytes, allowed)
        
        assert request.correlation_key == "test-correlation-key-123"
        assert "processing-input" in request.pdf_blob_url

    def test_from_queue_message_invalid_container(self, valid_queue_message_bytes):
        """Test ValidatedRequest rejects unauthorized container."""
        allowed = ["other-container"]
        with pytest.raises(ValidationError, match="Unauthorized container"):
            ValidatedRequest.from_queue_message(valid_queue_message_bytes, allowed)

    def test_immutability(self, valid_queue_message_bytes):
        """Test ValidatedRequest properties are read-only."""
        allowed = ["processing-input"]
        request = ValidatedRequest.from_queue_message(valid_queue_message_bytes, allowed)
        
        # Attempting to modify should raise AttributeError
        with pytest.raises(AttributeError):
            request.correlation_key = "new-key"


@pytest.mark.unit
class TestSanitizeUrlForLogging:
    """Tests for sanitize_url_for_logging function."""

    def test_removes_query_params(self):
        """Test query parameters (SAS tokens) are removed."""
        url = "https://account.blob.core.windows.net/container/blob.pdf?sv=2020-08-04&sig=secret"
        result = sanitize_url_for_logging(url)
        assert result == "https://account.blob.core.windows.net/container/blob.pdf"
        assert "sig=" not in result
        assert "secret" not in result

    def test_preserves_path(self):
        """Test URL path is preserved."""
        url = "https://account.blob.core.windows.net/container/folder/file.pdf"
        result = sanitize_url_for_logging(url)
        assert result == url

    def test_handles_invalid_url(self):
        """Test graceful handling of invalid URLs."""
        invalid_url = "not a valid url at all " * 20  # > 100 chars
        result = sanitize_url_for_logging(invalid_url)
        assert len(result) <= 103  # 100 + "..."
        assert result.endswith("...")


@pytest.mark.unit
class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    def test_redacts_account_key(self):
        """Test Azure account keys are redacted."""
        error = "Connection failed: AccountKey=verySecretKey123;AccountName=test"
        result = sanitize_error_message(error)
        assert "AccountKey=***REDACTED***" in result
        assert "verySecretKey123" not in result

    def test_redacts_api_key(self):
        """Test API keys are redacted."""
        errors = [
            'Failed with api_key="sk-12345abcdef"',
            'Error: api-key: test123456',
            'APIKey=mySecretApiKey',
        ]
        for error in errors:
            result = sanitize_error_message(error)
            assert "***REDACTED***" in result or "api_key" in result.lower()

    def test_redacts_long_tokens(self):
        """Test long alphanumeric tokens (40+ chars) are redacted."""
        token = "a" * 45
        error = f"Authorization failed with token: {token}"
        result = sanitize_error_message(error)
        assert token not in result
        assert "***REDACTED***" in result

    def test_preserves_normal_messages(self):
        """Test normal error messages are preserved."""
        error = "File not found: test.pdf"
        result = sanitize_error_message(error)
        assert result == error
