"""Azure Blob Storage operations with retry logic."""
import logging
import os
import time
from pathlib import Path
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import (
    AzureError,
    ServiceRequestError,
    ServiceResponseError,
    ResourceNotFoundError
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class AzureStorageClient:
    """Client for Azure Blob Storage operations with automatic retry."""

    def __init__(self, account_name: str, access_key: str):
        """Initialize Azure Storage client.

        Args:
            account_name: Azure Storage account name
            access_key: Azure Storage access key
        """
        account_url = f"https://{account_name}.blob.core.windows.net"

        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=access_key
        )

    def _sanitize_path_for_logging(self, path: str) -> str:
        """Sanitize file path for logging (show only filename).

        Args:
            path: Full file path

        Returns:
            Sanitized path with only filename
        """
        try:
            return Path(path).name
        except Exception:
            return "***REDACTED***"

    def download_blob(self, blob_url: str, local_path: str) -> str:
        """Download a blob from Azure Storage with retry logic.

        Args:
            blob_url: URL to the blob
            local_path: Local file path to save the downloaded blob

        Returns:
            Path to the downloaded file

        Raises:
            ResourceNotFoundError: If blob doesn't exist
            AzureError: If download fails after retries
        """
        local_path_obj = Path(local_path)
        local_path_obj.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(MAX_RETRIES):
            try:
                blob_client = BlobClient.from_blob_url(blob_url)

                logger.info(
                    f"Downloading blob (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{self._sanitize_path_for_logging(local_path)}"
                )

                with open(local_path_obj, 'wb') as f:
                    blob_data = blob_client.download_blob()
                    blob_data.readinto(f)

                file_size = local_path_obj.stat().st_size
                logger.info(
                    f"Successfully downloaded blob: "
                    f"{self._sanitize_path_for_logging(local_path)} "
                    f"({file_size / (1024*1024):.2f} MB)"
                )

                return str(local_path_obj)

            except ResourceNotFoundError:
                logger.error(f"Blob not found: {blob_url[:100]}...")
                raise

            except (ServiceRequestError, ServiceResponseError) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"Failed to download blob after {MAX_RETRIES} attempts: {e}"
                    )
                    raise

                wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Download failed (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {wait_time}s: {type(e).__name__}"
                )
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error downloading blob: {type(e).__name__}: {e}")
                raise

        raise AzureError("Download failed after all retries")

    def upload_file(
        self,
        container_name: str,
        blob_name: str,
        file_path: str,
        overwrite: bool = True
    ) -> str:
        """Upload a file to Azure Blob Storage with retry logic.

        Args:
            container_name: Name of the blob container
            blob_name: Name for the blob
            file_path: Path to the local file to upload
            overwrite: Whether to overwrite existing blob

        Returns:
            URL of the uploaded blob

        Raises:
            FileNotFoundError: If local file doesn't exist
            AzureError: If upload fails after retries
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = file_path_obj.stat().st_size

        for attempt in range(MAX_RETRIES):
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )

                logger.info(
                    f"Uploading file (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{self._sanitize_path_for_logging(file_path)} "
                    f"({file_size / (1024*1024):.2f} MB) "
                    f"to {container_name}/{blob_name[:50]}"
                )

                with open(file_path_obj, 'rb') as f:
                    blob_client.upload_blob(f, overwrite=overwrite)

                blob_url = blob_client.url
                logger.info(
                    f"Successfully uploaded file to {container_name}/{blob_name[:50]}"
                )

                return blob_url

            except (ServiceRequestError, ServiceResponseError) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"Failed to upload file after {MAX_RETRIES} attempts: {e}"
                    )
                    raise

                wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Upload failed (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {wait_time}s: {type(e).__name__}"
                )
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error uploading file: {type(e).__name__}: {e}")
                raise

        raise AzureError("Upload failed after all retries")

    def upload_bytes(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        overwrite: bool = True
    ) -> str:
        """Upload bytes data to Azure Blob Storage with retry logic.

        Args:
            container_name: Name of the blob container
            blob_name: Name for the blob
            data: Bytes data to upload
            overwrite: Whether to overwrite existing blob

        Returns:
            URL of the uploaded blob

        Raises:
            AzureError: If upload fails after retries
        """
        data_size = len(data)

        for attempt in range(MAX_RETRIES):
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name
                )

                logger.info(
                    f"Uploading bytes (attempt {attempt + 1}/{MAX_RETRIES}): "
                    f"{data_size / (1024*1024):.2f} MB "
                    f"to {container_name}/{blob_name[:50]}"
                )

                blob_client.upload_blob(data, overwrite=overwrite)

                blob_url = blob_client.url
                logger.info(
                    f"Successfully uploaded bytes to {container_name}/{blob_name[:50]}"
                )

                return blob_url

            except (ServiceRequestError, ServiceResponseError) as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"Failed to upload bytes after {MAX_RETRIES} attempts: {e}"
                    )
                    raise

                wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                logger.warning(
                    f"Upload failed (attempt {attempt + 1}/{MAX_RETRIES}), "
                    f"retrying in {wait_time}s: {type(e).__name__}"
                )
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error uploading bytes: {type(e).__name__}: {e}")
                raise

        raise AzureError("Upload failed after all retries")
