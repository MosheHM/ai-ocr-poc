"""Thread-safe context storage for request metadata."""
import contextvars
from typing import Optional

_correlation_key = contextvars.ContextVar('correlation_key', default=None)
_pdf_blob_url = contextvars.ContextVar('pdf_blob_url', default=None)
_ent_name = contextvars.ContextVar('ent_name', default=None)
_file_no = contextvars.ContextVar('file_no', default=None)


class RequestMetadata:
    """
    Accessor class for request metadata stored in context variables.
    
    This replaces the Singleton pattern with ContextVars to ensure thread-safety
    and correct behavior in concurrent Azure Functions executions.
    """

    @property
    def correlation_key(self) -> Optional[str]:
        return _correlation_key.get()

    @property
    def pdf_blob_url(self) -> Optional[str]:
        return _pdf_blob_url.get()

    @property
    def ent_name(self) -> Optional[str]:
        return _ent_name.get()

    @property
    def file_no(self) -> Optional[str]:
        return _file_no.get()

    @classmethod
    def initialize(
        cls,
        correlation_key: Optional[str] = None,
        pdf_blob_url: Optional[str] = None,
        ent_name: Optional[str] = None,
        file_no: Optional[str] = None
    ) -> 'RequestMetadata':
        """
        Initialize context variables for the current request.

        Args:
            correlation_key: Unique identifier for the processing request
            pdf_blob_url: URL to the PDF blob in Azure Storage
            ent_name: Entity name from the request
            file_no: File number from the request

        Returns:
            An instance of RequestMetadata accessor
        """
        _correlation_key.set(correlation_key)
        _pdf_blob_url.set(pdf_blob_url)
        _ent_name.set(ent_name)
        _file_no.set(file_no)
        return cls()

    def to_result_dict(self) -> dict:
        """
        Convert metadata to dictionary format for inclusion in result messages.

        Returns:
            Dictionary containing all metadata fields with original values
        """
        return {
            "correlationKey": self.correlation_key,
            "entName": self.ent_name,
            "fileNo": self.file_no
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"RequestMetadata(correlation_key={self.correlation_key!r}, "
            f"ent_name={self.ent_name!r}, file_no={self.file_no!r})"
        )
