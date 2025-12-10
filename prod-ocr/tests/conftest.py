"""Shared fixtures for all tests."""
import pytest
import json
import io
import os
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock, Mock
from pypdf import PdfWriter


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        'AZURE_STORAGE_ACCOUNT_NAME': 'testaccount',
        'AZURE_STORAGE_ACCESS_KEY': 'dGVzdGtleQ==',  # base64 "testkey"
        'GEMINI_API_KEY': 'test-gemini-api-key',
        'GEMINI_MODEL': 'gemini-2.5-flash',
        'GEMINI_TIMEOUT_SECONDS': '60',
        'RESULTS_CONTAINER': 'processing-results',
        'AzureWebJobsStorage': 'UseDevelopmentStorage=true',
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def azurite_connection_string():
    """Azurite emulator connection string."""
    return (
        "DefaultEndpointsProtocol=http;"
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
        "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    )


# ============================================================================
# PDF Fixtures
# ============================================================================

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generate a minimal valid PDF in memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)  # Letter size
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


@pytest.fixture
def multi_page_pdf_bytes() -> bytes:
    """Generate a 5-page PDF in memory."""
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=612, height=792)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


@pytest.fixture
def sample_pdf_file(tmp_path, sample_pdf_bytes) -> Path:
    """Create a temporary PDF file."""
    pdf_path = tmp_path / "test_document.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)
    return pdf_path


@pytest.fixture
def multi_page_pdf_file(tmp_path, multi_page_pdf_bytes) -> Path:
    """Create a temporary multi-page PDF file."""
    pdf_path = tmp_path / "multi_page_document.pdf"
    pdf_path.write_bytes(multi_page_pdf_bytes)
    return pdf_path


@pytest.fixture
def invalid_pdf_bytes() -> bytes:
    """Generate invalid PDF content."""
    return b"This is not a valid PDF file content"


@pytest.fixture
def invalid_pdf_file(tmp_path, invalid_pdf_bytes) -> Path:
    """Create a temporary invalid PDF file."""
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_bytes(invalid_pdf_bytes)
    return pdf_path


@pytest.fixture
def empty_pdf_file(tmp_path) -> Path:
    """Create an empty PDF file."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_bytes(b"")
    return pdf_path


# ============================================================================
# Mock Gemini Response Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_invoice_response() -> List[Dict[str, Any]]:
    """Mock Gemini response for an invoice document."""
    return [
        {
            "DOC_TYPE": "INVOICE",
            "INVOICE_NO": "0004833/E",
            "INVOICE_DATE": "2025073000000000",
            "CURRENCY_ID": "EUR",
            "INCOTERMS": "FCA",
            "INVOICE_AMOUNT": 7632.00,
            "CUSTOMER_ID": "D004345",
            "DOC_TYPE_CONFIDENCE": 0.95,
            "TOTAL_PAGES": 2,
            "START_PAGE_NO": 1,
            "END_PAGE_NO": 2
        }
    ]


@pytest.fixture
def mock_gemini_obl_response() -> List[Dict[str, Any]]:
    """Mock Gemini response for an OBL document."""
    return [
        {
            "DOC_TYPE": "OBL",
            "CUSTOMER_NAME": "LAPIDOTH CAPITAL LTD.",
            "WEIGHT": 115000.0,
            "VOLUME": 1.116,
            "INCOTERMS": "CIF",
            "DOC_TYPE_CONFIDENCE": 0.9,
            "TOTAL_PAGES": 1,
            "START_PAGE_NO": 1,
            "END_PAGE_NO": 1
        }
    ]


@pytest.fixture
def mock_gemini_hawb_response() -> List[Dict[str, Any]]:
    """Mock Gemini response for a HAWB document."""
    return [
        {
            "DOC_TYPE": "HAWB",
            "CUSTOMER_NAME": "Example Corp",
            "CURRENCY": "USD",
            "CARRIER": "Emirates",
            "HAWB_NUMBER": "176-12345678",
            "PIECES": 10,
            "WEIGHT": 500.5,
            "DOC_TYPE_CONFIDENCE": 0.92,
            "TOTAL_PAGES": 1,
            "START_PAGE_NO": 1,
            "END_PAGE_NO": 1
        }
    ]


@pytest.fixture
def mock_gemini_packing_list_response() -> List[Dict[str, Any]]:
    """Mock Gemini response for a packing list document."""
    return [
        {
            "DOC_TYPE": "PACKING_LIST",
            "CUSTOMER_NAME": "DEF Manufacturing",
            "PIECES": 100,
            "WEIGHT": 2500.0,
            "DOC_TYPE_CONFIDENCE": 0.88,
            "TOTAL_PAGES": 1,
            "START_PAGE_NO": 1,
            "END_PAGE_NO": 1
        }
    ]


@pytest.fixture
def mock_gemini_multi_document_response() -> List[Dict[str, Any]]:
    """Mock Gemini response for a PDF with multiple documents."""
    return [
        {
            "DOC_TYPE": "INVOICE",
            "INVOICE_NO": "0004833/E",
            "INVOICE_DATE": "2025073000000000",
            "CURRENCY_ID": "EUR",
            "INCOTERMS": "FCA",
            "INVOICE_AMOUNT": 7632.00,
            "CUSTOMER_ID": "D004345",
            "DOC_TYPE_CONFIDENCE": 0.95,
            "TOTAL_PAGES": 2,
            "START_PAGE_NO": 1,
            "END_PAGE_NO": 2
        },
        {
            "DOC_TYPE": "OBL",
            "CUSTOMER_NAME": "LAPIDOTH CAPITAL LTD.",
            "WEIGHT": 115000.0,
            "VOLUME": 1.116,
            "DOC_TYPE_CONFIDENCE": 0.9,
            "TOTAL_PAGES": 1,
            "START_PAGE_NO": 3,
            "END_PAGE_NO": 3
        },
        {
            "DOC_TYPE": "PACKING_LIST",
            "CUSTOMER_NAME": "DEF Manufacturing",
            "PIECES": 100,
            "WEIGHT": 2500.0,
            "DOC_TYPE_CONFIDENCE": 0.88,
            "TOTAL_PAGES": 2,
            "START_PAGE_NO": 4,
            "END_PAGE_NO": 5
        }
    ]


@pytest.fixture
def mock_gemini_response_with_markdown() -> str:
    """Mock raw Gemini response wrapped in markdown code blocks."""
    return '''```json
[
    {
        "DOC_TYPE": "INVOICE",
        "INVOICE_NO": "TEST-001",
        "DOC_TYPE_CONFIDENCE": 0.95,
        "TOTAL_PAGES": 1,
        "START_PAGE_NO": 1,
        "END_PAGE_NO": 1
    }
]
```'''


# ============================================================================
# Queue Message Fixtures
# ============================================================================

@pytest.fixture
def valid_queue_message_bytes() -> bytes:
    """Valid queue message as bytes."""
    message = {
        "correlationKey": "test-correlation-key-123",
        "pdfBlobUrl": "https://testaccount.blob.core.windows.net/processing-input/test.pdf"
    }
    return json.dumps(message).encode('utf-8')


@pytest.fixture
def valid_queue_message_alt_keys() -> bytes:
    """Valid queue message with alternative key names (snake_case)."""
    message = {
        "correlation_key": "test-correlation-key-456",
        "pdf_blob_url": "https://testaccount.blob.core.windows.net/trusted-uploads/test.pdf"
    }
    return json.dumps(message).encode('utf-8')


@pytest.fixture
def invalid_queue_message_missing_key() -> bytes:
    """Queue message missing correlationKey."""
    message = {
        "pdfBlobUrl": "https://testaccount.blob.core.windows.net/processing-input/test.pdf"
    }
    return json.dumps(message).encode('utf-8')


@pytest.fixture
def invalid_queue_message_bad_url() -> bytes:
    """Queue message with invalid blob URL."""
    message = {
        "correlationKey": "test-key",
        "pdfBlobUrl": "http://evil.com/malware.pdf"
    }
    return json.dumps(message).encode('utf-8')


# ============================================================================
# Mock Azure Client Fixtures
# ============================================================================

@pytest.fixture
def mock_blob_client():
    """Mock Azure BlobClient."""
    client = MagicMock()
    client.url = "https://testaccount.blob.core.windows.net/container/blob"
    client.download_blob.return_value.readinto = MagicMock()
    client.upload_blob = MagicMock()
    return client


@pytest.fixture
def mock_blob_service_client(mock_blob_client):
    """Mock Azure BlobServiceClient."""
    service_client = MagicMock()
    service_client.get_blob_client.return_value = mock_blob_client
    service_client.get_service_properties.return_value = {}
    return service_client


@pytest.fixture
def mock_azure_storage_client(mock_blob_service_client):
    """Mock AzureStorageClient."""
    from modules.azure.storage import AzureStorageClient
    
    client = MagicMock(spec=AzureStorageClient)
    client.blob_service_client = mock_blob_service_client
    client.download_blob = MagicMock(return_value="/tmp/downloaded.pdf")
    client.upload_file = MagicMock(return_value="https://test.blob.core.windows.net/results/file.zip")
    client.upload_bytes = MagicMock(return_value="https://test.blob.core.windows.net/results/data")
    return client


# ============================================================================
# Mock Gemini Client Fixtures
# ============================================================================

@pytest.fixture
def mock_gemini_client(mock_gemini_invoice_response):
    """Mock Google Gemini client."""
    client = MagicMock()
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_gemini_invoice_response)
    
    client.models.generate_content.return_value = mock_response
    return client


@pytest.fixture
def mock_document_splitter(mock_gemini_client, mock_gemini_invoice_response):
    """Mock DocumentSplitter."""
    from modules.document_splitter.splitter import DocumentSplitter
    
    splitter = MagicMock(spec=DocumentSplitter)
    splitter.extract_documents.return_value = mock_gemini_invoice_response
    splitter.split_and_save.return_value = {
        'source_pdf': '/tmp/input.pdf',
        'output_directory': '/tmp/output',
        'total_documents': 1,
        'documents': [
            {
                **mock_gemini_invoice_response[0],
                'FILE_PATH': '/tmp/output/doc_INVOICE_1_pages_1-2.pdf',
                'FILE_NAME': 'doc_INVOICE_1_pages_1-2.pdf'
            }
        ]
    }
    return splitter


# ============================================================================
# Mock Azure Functions Fixtures
# ============================================================================

@pytest.fixture
def mock_queue_message(valid_queue_message_bytes):
    """Mock Azure Functions QueueMessage."""
    msg = MagicMock()
    msg.get_body.return_value = valid_queue_message_bytes
    msg.id = "test-message-id"
    msg.dequeue_count = 1
    return msg


@pytest.fixture
def mock_output_queue():
    """Mock Azure Functions output queue binding."""
    output_queue = MagicMock()
    output_queue.set = MagicMock()
    return output_queue


# ============================================================================
# Helper Functions for Tests
# ============================================================================

def create_mock_gemini_response(documents: List[Dict[str, Any]], wrap_markdown: bool = False) -> MagicMock:
    """Create a mock Gemini API response.
    
    Args:
        documents: List of document dictionaries
        wrap_markdown: Whether to wrap in markdown code blocks
        
    Returns:
        Mock response object
    """
    response_text = json.dumps(documents)
    if wrap_markdown:
        response_text = f"```json\n{response_text}\n```"
    
    mock_response = MagicMock()
    mock_response.text = response_text
    return mock_response
