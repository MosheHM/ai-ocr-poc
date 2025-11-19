"""AI OCR POC - Modular document processing system."""
from .document_splitter import DocumentSplitter, split_and_extract_documents

__all__ = ['DocumentSplitter', 'split_and_extract_documents']
