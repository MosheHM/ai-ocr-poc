"""Thread-safe singleton for storing all request metadata throughout processing lifecycle."""
import threading
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class RequestMetadata:
    """
    Singleton class to store all request metadata throughout the processing lifecycle.

    This class maintains all fields from the incoming queue message and makes them
    available throughout the processing pipeline until they are included in the
    result message.

    Thread-safe singleton implementation using double-checked locking pattern.

    Attributes:
        correlation_key: Unique identifier for the processing request
        pdf_blob_url: URL to the PDF blob in Azure Storage
        ent_name: Entity name (customer/organization identifier)
        file_no: File number (document reference number)
    """

    correlation_key: Optional[str] = None
    pdf_blob_url: Optional[str] = None
    ent_name: Optional[str] = None
    file_no: Optional[str] = None

    _instance: Optional['RequestMetadata'] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __new__(cls):
        """Implement singleton pattern with thread-safe double-checked locking."""
        if cls._instance is None:
            with threading.Lock():
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(
        cls,
        correlation_key: Optional[str] = None,
        pdf_blob_url: Optional[str] = None,
        ent_name: Optional[str] = None,
        file_no: Optional[str] = None
    ) -> 'RequestMetadata':
        """
        Initialize or update the singleton instance with all metadata values.

        Args:
            correlation_key: Unique identifier for the processing request
            pdf_blob_url: URL to the PDF blob in Azure Storage
            ent_name: Entity name from the request
            file_no: File number from the request

        Returns:
            The singleton instance with updated values
        """
        instance = cls()
        instance.correlation_key = correlation_key
        instance.pdf_blob_url = pdf_blob_url
        instance.ent_name = ent_name
        instance.file_no = file_no
        return instance

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
