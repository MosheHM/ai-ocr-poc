"""Integration tests for Azure storage operations with mocked Azure SDK."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

from modules.azure.storage import AzureStorageClient, MAX_RETRIES


@pytest.mark.integration
class TestAzureStorageClientDownload:
    """Tests for AzureStorageClient.download_blob with mocked Azure SDK."""

    @pytest.fixture
    def storage_client(self, mocker):
        """Create storage client with mocked BlobServiceClient."""
        mocker.patch('modules.azure.storage.BlobServiceClient')
        return AzureStorageClient("testaccount", "testkey")

    def test_download_blob_success(self, storage_client, tmp_path, mocker):
        """Test successful blob download."""
        local_path = tmp_path / "downloaded.pdf"
        blob_url = "https://testaccount.blob.core.windows.net/container/file.pdf"
        
        # Mock BlobClient.from_blob_url
        mock_blob_client = MagicMock()
        mock_blob_data = MagicMock()
        mock_blob_data.readinto = MagicMock(side_effect=lambda f: f.write(b"PDF content"))
        mock_blob_client.download_blob.return_value = mock_blob_data
        
        mocker.patch(
            'modules.azure.storage.BlobClient.from_blob_url',
            return_value=mock_blob_client
        )
        
        result = storage_client.download_blob(blob_url, str(local_path))
        
        assert result == str(local_path)
        assert local_path.exists()

    def test_download_blob_creates_parent_dirs(self, storage_client, tmp_path, mocker):
        """Test that parent directories are created."""
        local_path = tmp_path / "nested" / "path" / "file.pdf"
        blob_url = "https://testaccount.blob.core.windows.net/container/file.pdf"
        
        mock_blob_client = MagicMock()
        mock_blob_data = MagicMock()
        mock_blob_data.readinto = MagicMock()
        mock_blob_client.download_blob.return_value = mock_blob_data
        
        mocker.patch(
            'modules.azure.storage.BlobClient.from_blob_url',
            return_value=mock_blob_client
        )
        
        storage_client.download_blob(blob_url, str(local_path))
        
        assert local_path.parent.exists()

    def test_download_blob_not_found_raises(self, storage_client, tmp_path, mocker):
        """Test ResourceNotFoundError is raised when blob doesn't exist."""
        local_path = tmp_path / "file.pdf"
        blob_url = "https://testaccount.blob.core.windows.net/container/missing.pdf"
        
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")
        
        mocker.patch(
            'modules.azure.storage.BlobClient.from_blob_url',
            return_value=mock_blob_client
        )
        
        with pytest.raises(ResourceNotFoundError):
            storage_client.download_blob(blob_url, str(local_path))

    def test_download_blob_retries_on_transient_error(self, storage_client, tmp_path, mocker):
        """Test retry logic on transient errors."""
        local_path = tmp_path / "file.pdf"
        blob_url = "https://testaccount.blob.core.windows.net/container/file.pdf"
        
        mock_blob_client = MagicMock()
        mock_blob_data = MagicMock()
        mock_blob_data.readinto = MagicMock()
        
        # Fail twice, then succeed
        mock_blob_client.download_blob.side_effect = [
            ServiceRequestError("Network error"),
            ServiceRequestError("Network error"),
            mock_blob_data
        ]
        
        mocker.patch(
            'modules.azure.storage.BlobClient.from_blob_url',
            return_value=mock_blob_client
        )
        mocker.patch('modules.azure.storage.time.sleep')  # Don't actually sleep
        
        result = storage_client.download_blob(blob_url, str(local_path))
        
        assert result == str(local_path)
        assert mock_blob_client.download_blob.call_count == 3

    def test_download_blob_fails_after_max_retries(self, storage_client, tmp_path, mocker):
        """Test that error is raised after max retries exhausted."""
        local_path = tmp_path / "file.pdf"
        blob_url = "https://testaccount.blob.core.windows.net/container/file.pdf"
        
        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = ServiceRequestError("Network error")
        
        mocker.patch(
            'modules.azure.storage.BlobClient.from_blob_url',
            return_value=mock_blob_client
        )
        mocker.patch('modules.azure.storage.time.sleep')
        
        with pytest.raises(ServiceRequestError):
            storage_client.download_blob(blob_url, str(local_path))
        
        assert mock_blob_client.download_blob.call_count == MAX_RETRIES


@pytest.mark.integration
class TestAzureStorageClientUpload:
    """Tests for AzureStorageClient.upload_file with mocked Azure SDK."""

    @pytest.fixture
    def storage_client(self, mocker):
        """Create storage client with mocked BlobServiceClient."""
        mock_service = mocker.patch('modules.azure.storage.BlobServiceClient')
        client = AzureStorageClient("testaccount", "testkey")
        return client

    def test_upload_file_success(self, storage_client, sample_pdf_file, mocker):
        """Test successful file upload."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://testaccount.blob.core.windows.net/results/file.pdf"
        storage_client.blob_service_client.get_blob_client.return_value = mock_blob_client
        
        result = storage_client.upload_file(
            "results", 
            "test/file.pdf", 
            str(sample_pdf_file)
        )
        
        assert result == mock_blob_client.url
        mock_blob_client.upload_blob.assert_called_once()

    def test_upload_file_not_found_raises(self, storage_client):
        """Test FileNotFoundError when local file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            storage_client.upload_file("container", "blob", "/nonexistent/file.pdf")

    def test_upload_file_retries_on_error(self, storage_client, sample_pdf_file, mocker):
        """Test retry logic on upload errors."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://testaccount.blob.core.windows.net/results/file.pdf"
        mock_blob_client.upload_blob.side_effect = [
            ServiceRequestError("Network error"),
            None  # Success on second try
        ]
        storage_client.blob_service_client.get_blob_client.return_value = mock_blob_client
        mocker.patch('modules.azure.storage.time.sleep')
        
        result = storage_client.upload_file("results", "file.pdf", str(sample_pdf_file))
        
        assert result == mock_blob_client.url
        assert mock_blob_client.upload_blob.call_count == 2

    def test_upload_file_overwrites_by_default(self, storage_client, sample_pdf_file):
        """Test that overwrite=True is passed by default."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://test.blob.core.windows.net/c/b"
        storage_client.blob_service_client.get_blob_client.return_value = mock_blob_client
        
        storage_client.upload_file("container", "blob", str(sample_pdf_file))
        
        # Check overwrite=True was passed
        call_kwargs = mock_blob_client.upload_blob.call_args[1]
        assert call_kwargs.get("overwrite") == True


@pytest.mark.integration
class TestAzureStorageClientUploadBytes:
    """Tests for AzureStorageClient.upload_bytes with mocked Azure SDK."""

    @pytest.fixture
    def storage_client(self, mocker):
        """Create storage client with mocked BlobServiceClient."""
        mocker.patch('modules.azure.storage.BlobServiceClient')
        return AzureStorageClient("testaccount", "testkey")

    def test_upload_bytes_success(self, storage_client):
        """Test successful bytes upload."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://testaccount.blob.core.windows.net/results/data"
        storage_client.blob_service_client.get_blob_client.return_value = mock_blob_client
        
        data = b"Test data content"
        result = storage_client.upload_bytes("results", "data.bin", data)
        
        assert result == mock_blob_client.url
        mock_blob_client.upload_blob.assert_called_once_with(data, overwrite=True)

    def test_upload_bytes_retries_on_error(self, storage_client, mocker):
        """Test retry logic on upload errors."""
        mock_blob_client = MagicMock()
        mock_blob_client.url = "https://test.blob.core.windows.net/c/b"
        mock_blob_client.upload_blob.side_effect = [
            ServiceRequestError("Error"),
            ServiceRequestError("Error"),
            None
        ]
        storage_client.blob_service_client.get_blob_client.return_value = mock_blob_client
        mocker.patch('modules.azure.storage.time.sleep')
        
        result = storage_client.upload_bytes("container", "blob", b"data")
        
        assert result == mock_blob_client.url
        assert mock_blob_client.upload_blob.call_count == 3
