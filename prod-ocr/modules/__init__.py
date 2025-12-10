"""AI OCR POC - Modular document processing system."""
from .document_splitter import DocumentSplitter
from .config import (
    get_environment,
    get_storage_config,
    get_queue_storage_config,
    get_app_config,
    is_development,
    is_production,
    AppConfig,
    StorageConfig,
    QueueStorageConfig,
    Environment
)

__all__ = [
    'DocumentSplitter',
    'get_environment',
    'get_storage_config',
    'get_queue_storage_config',
    'get_app_config',
    'is_development',
    'is_production',
    'AppConfig',
    'StorageConfig',
    'QueueStorageConfig',
    'Environment'
]
