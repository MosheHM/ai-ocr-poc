"""Custom error types for processing."""
from enum import Enum
from typing import Optional


class ErrorSeverity(Enum):
    """Processing error severity levels."""
    TRANSIENT = "transient"  # Retry possible (network issues, rate limits)
    PERMANENT = "permanent"  # No retry needed (validation errors, bad input)
    CRITICAL = "critical"    # Alert required (config errors, system failures)


class ProcessingError(Exception):
    """Base exception for processing errors with severity classification."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity,
        original: Optional[Exception] = None
    ):
        """Initialize processing error.

        Args:
            message: Human-readable error message
            severity: Error severity level
            original: Original exception that caused this error
        """
        super().__init__(message)
        self.severity = severity
        self.original = original


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails (permanent error, no retry).

    ValidationError indicates bad input data that will never succeed even with retry.
    """

    def __init__(self, message: str, original: Optional[Exception] = None):
        """Initialize validation error.

        Args:
            message: Human-readable error message
            original: Original exception that caused this error
        """
        super().__init__(message)
        self.original = original
