"""AI OCR POC - Modular document processing system."""
from .document_splitter import DocumentSplitter
from .config import AppConfig

__all__ = [
    'DocumentSplitter',
    'AppConfig'
]
