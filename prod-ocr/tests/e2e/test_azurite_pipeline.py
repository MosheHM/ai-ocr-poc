"""End-to-end tests using Azurite emulator for Azure Storage.

These tests require Azurite to be running locally:
    docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite

Tests will be skipped if Azurite is not available.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueServiceClient
from azure.core.exceptions import ServiceRequestError


# Azurite connection details
AZURITE_BLOB_ENDPOINT = "http://127.0.0.1:10000/devstoreaccount1"
AZURITE_QUEUE_ENDPOINT = "http://127.0.0.1:10001/devstoreaccount1"
AZURITE_ACCOUNT_NAME = "devstoreaccount1"
AZURITE_ACCOUNT_KEY = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
AZURITE_CONNECTION_STRING = (
    f"DefaultEndpointsProtocol=http;"
    f"AccountName={AZURITE_ACCOUNT_NAME};"
    f"AccountKey={AZURITE_ACCOUNT_KEY};"
    f"BlobEndpoint={AZURITE_BLOB_ENDPOINT};"
    f"QueueEndpoint={AZURITE_QUEUE_ENDPOINT};"
)


def is_azurite_running():
    """Check if Azurite emulator is running."""
    try:
        blob_service = BlobServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)
        blob_service.get_service_properties()
        return True
    except Exception:
        return False


# Skip all e2e tests if Azurite is not running
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not is_azurite_running(),
        reason="Azurite emulator not running. Start with: docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite"
    )
]


@pytest.fixture(scope="module")
def blob_service_client():
    """Create BlobServiceClient for Azurite."""
    return BlobServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)


@pytest.fixture(scope="module")
def queue_service_client():
    """Create QueueServiceClient for Azurite."""
    return QueueServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)


@pytest.fixture
def test_containers(blob_service_client):
    """Create and cleanup test containers."""
    containers = ["processing-input", "processing-results", "trusted-uploads"]
    
    # Create containers
    for container_name in containers:
        try:
            blob_service_client.create_container(container_name)
        except Exception:
            pass  # Container may already exist
    
    yield containers
    
    # Cleanup containers after test
    for container_name in containers:
        try:
            container_client = blob_service_client.get_container_client(container_name)
            # Delete all blobs
            for blob in container_client.list_blobs():
                container_client.delete_blob(blob.name)
            blob_service_client.delete_container(container_name)
        except Exception:
            pass


@pytest.fixture
def test_queues(queue_service_client):
    """Create and cleanup test queues."""
    queues = ["processing-tasks", "processing-tasks-results"]
    
    # Create queues
    for queue_name in queues:
        try:
            queue_service_client.create_queue(queue_name)
        except Exception:
            pass
    
    yield queues
    
    # Cleanup queues after test
    for queue_name in queues:
        try:
            queue_service_client.delete_queue(queue_name)
        except Exception:
            pass


class TestAzuriteBlobOperations:
    """E2E tests for blob storage operations against Azurite."""

    def test_upload_and_download_pdf(self, blob_service_client, test_containers, sample_pdf_bytes, tmp_path):
        """Test uploading and downloading a PDF file."""
        container_name = "processing-input"
        blob_name = "test/document.pdf"
        
        # Upload
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        blob_client.upload_blob(sample_pdf_bytes, overwrite=True)
        
        # Verify blob exists
        assert blob_client.exists()
        
        # Download
        download_path = tmp_path / "downloaded.pdf"
        with open(download_path, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())
        
        # Verify content
        assert download_path.read_bytes() == sample_pdf_bytes

    def test_upload_results_zip(self, blob_service_client, test_containers, tmp_path, sample_pdf_bytes):
        """Test uploading results ZIP to results container."""
        import zipfile
        
        container_name = "processing-results"
        correlation_key = "test-correlation-123"
        
        # Create a test ZIP file
        zip_path = tmp_path / "results.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("extraction_results.json", '{"total_documents": 1}')
        
        # Upload
        blob_name = f"{correlation_key}/results.zip"
        blob_client = blob_service_client.get_blob_client(container_name, blob_name)
        
        with open(zip_path, "rb") as f:
            blob_client.upload_blob(f, overwrite=True)
        
        # Verify
        assert blob_client.exists()
        
        # Download and verify
        downloaded = blob_client.download_blob().readall()
        assert len(downloaded) > 0

    def test_list_blobs_in_container(self, blob_service_client, test_containers, sample_pdf_bytes):
        """Test listing blobs in a container."""
        container_name = "processing-input"
        
        # Upload multiple blobs
        for i in range(3):
            blob_client = blob_service_client.get_blob_client(
                container_name, 
                f"batch/file_{i}.pdf"
            )
            blob_client.upload_blob(sample_pdf_bytes, overwrite=True)
        
        # List blobs
        container_client = blob_service_client.get_container_client(container_name)
        blobs = list(container_client.list_blobs(name_starts_with="batch/"))
        
        assert len(blobs) == 3
        blob_names = [b.name for b in blobs]
        assert "batch/file_0.pdf" in blob_names
        assert "batch/file_1.pdf" in blob_names
        assert "batch/file_2.pdf" in blob_names


class TestAzuriteQueueOperations:
    """E2E tests for queue operations against Azurite."""

    def test_send_and_receive_message(self, queue_service_client, test_queues):
        """Test sending and receiving queue messages."""
        queue_name = "processing-tasks"
        queue_client = queue_service_client.get_queue_client(queue_name)
        
        # Send message
        message = {
            "correlationKey": "test-key-123",
            "pdfBlobUrl": "https://devstoreaccount1.blob.core.windows.net/processing-input/test.pdf"
        }
        queue_client.send_message(json.dumps(message))
        
        # Receive message
        messages = queue_client.receive_messages(max_messages=1)
        received = list(messages)
        
        assert len(received) == 1
        received_content = json.loads(received[0].content)
        assert received_content["correlationKey"] == "test-key-123"

    def test_message_visibility_timeout(self, queue_service_client, test_queues):
        """Test message visibility timeout."""
        queue_name = "processing-tasks"
        queue_client = queue_service_client.get_queue_client(queue_name)
        
        # Send message
        queue_client.send_message("test message")
        
        # Receive with visibility timeout
        messages = list(queue_client.receive_messages(
            max_messages=1, 
            visibility_timeout=5
        ))
        
        assert len(messages) == 1
        
        # Message should not be visible immediately
        more_messages = list(queue_client.receive_messages(max_messages=1))
        assert len(more_messages) == 0

    def test_send_result_message(self, queue_service_client, test_queues):
        """Test sending result message to results queue."""
        queue_name = "processing-tasks-results"
        queue_client = queue_service_client.get_queue_client(queue_name)
        
        # Send success result
        result = {
            "correlationKey": "test-key-456",
            "status": "success",
            "resultsBlobUrl": "https://devstoreaccount1.blob.core.windows.net/processing-results/test-key-456/results.zip"
        }
        queue_client.send_message(json.dumps(result))
        
        # Receive and verify
        messages = list(queue_client.receive_messages(max_messages=1))
        assert len(messages) == 1
        
        received = json.loads(messages[0].content)
        assert received["status"] == "success"


class TestFullProcessingPipeline:
    """E2E tests for the complete processing pipeline with mocked Gemini."""

    def test_full_pipeline_with_mocked_gemini(
        self, 
        blob_service_client, 
        queue_service_client,
        test_containers, 
        test_queues,
        sample_pdf_bytes,
        mock_gemini_invoice_response,
        tmp_path,
        monkeypatch
    ):
        """Test complete pipeline: upload PDF -> process -> get results."""
        # Setup environment for Azurite
        monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_NAME", AZURITE_ACCOUNT_NAME)
        monkeypatch.setenv("AZURE_STORAGE_ACCESS_KEY", AZURITE_ACCOUNT_KEY)
        monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
        monkeypatch.setenv("RESULTS_CONTAINER", "processing-results")
        
        correlation_key = "e2e-test-pipeline-001"
        
        # Step 1: Upload PDF to input container
        input_blob_client = blob_service_client.get_blob_client(
            "processing-input",
            f"{correlation_key}/input.pdf"
        )
        input_blob_client.upload_blob(sample_pdf_bytes, overwrite=True)
        blob_url = f"{AZURITE_BLOB_ENDPOINT}/processing-input/{correlation_key}/input.pdf"
        
        # Step 2: Simulate processing with mocked Gemini
        # This would normally be done by the Azure Function
        from modules.document_splitter.splitter import DocumentSplitter
        
        # Create splitter with mocked Gemini
        with patch('modules.document_splitter.splitter.genai.Client') as mock_genai:
            mock_response = MagicMock()
            mock_response.text = json.dumps(mock_gemini_invoice_response)
            mock_genai.return_value.models.generate_content.return_value = mock_response
            
            splitter = DocumentSplitter(api_key="test", model="gemini-2.5-flash")
            
            # Download PDF locally for processing
            local_pdf = tmp_path / "input.pdf"
            with open(local_pdf, "wb") as f:
                download = input_blob_client.download_blob()
                f.write(download.readall())
            
            # Process
            output_dir = tmp_path / "output"
            results = splitter.split_and_save(str(local_pdf), str(output_dir))
        
        assert results["total_documents"] == 1
        assert results["documents"][0]["doc_type"] == "invoice"
        
        # Step 3: Create and upload results ZIP
        from modules.utils.zip_utils import create_results_zip
        
        zip_path = create_results_zip(str(output_dir), results, f"{correlation_key}_results.zip")
        
        results_blob_client = blob_service_client.get_blob_client(
            "processing-results",
            f"{correlation_key}/results.zip"
        )
        with open(zip_path, "rb") as f:
            results_blob_client.upload_blob(f, overwrite=True)
        
        # Step 4: Send result message
        results_queue = queue_service_client.get_queue_client("processing-tasks-results")
        result_message = {
            "correlationKey": correlation_key,
            "status": "success",
            "resultsBlobUrl": f"{AZURITE_BLOB_ENDPOINT}/processing-results/{correlation_key}/results.zip"
        }
        results_queue.send_message(json.dumps(result_message))
        
        # Verify results
        assert results_blob_client.exists()
        
        messages = list(results_queue.receive_messages(max_messages=1))
        assert len(messages) == 1
        
        received = json.loads(messages[0].content)
        assert received["correlationKey"] == correlation_key
        assert received["status"] == "success"
