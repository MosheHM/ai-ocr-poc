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

    def __init__(self, account_name: str, access_key: str, connection_string: str = None):
        """Initialize Azure Storage client.

        Args:
            account_name: Azure Storage account name
            access_key: Azure Storage access key
            connection_string: Optional connection string (overrides account_name/key)
        """
        self.account_name = account_name
        self.access_key = access_key
        
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
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
        if not path:
            return ""

        try:
            # Handle both Unix and Windows path separators
            # Use the rightmost separator (/ or \) to extract filename
            if '/' in path or '\\' in path:
                parts = path.replace('\\', '/').split('/')
                return parts[-1] if parts[-1] else ""
            return path
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

        try:
            tmp_client = BlobClient.from_blob_url(blob_url)
            container_name = tmp_client.container_name
            blob_name = tmp_client.blob_name
        except Exception:
            container_name = None
            blob_name = None

        for attempt in range(MAX_RETRIES):
            try:
                if container_name and blob_name:
                    blob_client = self.blob_service_client.get_blob_client(
                        container=container_name,
                        blob=blob_name
                    )
                else:
                    blob_client = BlobClient.from_blob_url(blob_url, credential=self.access_key)

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

            except ResourceNotFoundError as e:
                # If container not found, try to create it
                if "ContainerNotFound" in str(e):
                    try:
                        logger.info(f"Container {container_name} not found, creating it...")
                        self.blob_service_client.create_container(container_name)
                        # Retry the upload immediately
                        continue
                    except Exception as create_error:
                        logger.error(f"Failed to create container {container_name}: {create_error}")
                        raise e
                else:
                    raise e

            except Exception as e:
                logger.error(f"Unexpected error uploading file: {type(e).__name__}: {e}")
                raise

        raise AzureError("Upload failed after all retries")
