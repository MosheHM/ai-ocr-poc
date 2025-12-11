"""Azure Function for processing document tasks from queue."""
import sys
import os
from pathlib import Path

# Workaround for Azure Functions worker shadowing google package
# Prioritize local .venv site-packages to ensure google-genai is found
try:
    current_dir = Path(__file__).parent
    
    # 1. Try local .venv (Linux/Mac structure)
    venv_site_packages = current_dir / ".venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    if venv_site_packages.exists():
        sys.path.insert(0, str(venv_site_packages))
        logging.info(f"Added to sys.path: {venv_site_packages}")
        
    else:
        # 2. Try local .venv (Windows structure)
        venv_site_packages_win = current_dir / ".venv" / "Lib" / "site-packages"
        if venv_site_packages_win.exists():
            sys.path.insert(0, str(venv_site_packages_win))
            logging.info(f"Added to sys.path: {venv_site_packages_win}")
            
    # 3. Try Azure's .python_packages (Production / --build-native-deps)
    azure_site_packages = current_dir / ".python_packages" / "lib" / "site-packages"
    if azure_site_packages.exists():
        sys.path.insert(0, str(azure_site_packages))
        logging.info(f"Added to sys.path: {azure_site_packages}")
        
except Exception:
    pass

import azure.functions as func
import logging
import json
import os
import tempfile
import secrets
import shutil
from pathlib import Path
from typing import Optional

from modules.azure import AzureStorageClient
from modules.document_splitter.splitter import DocumentSplitter
from modules.utils import create_results_zip
from modules.config import get_app_config, AppConfig
from modules.validators import (
    ValidatedRequest,
    ValidationError,
    ProcessingError,
    ErrorSeverity,
    ConfigurationError,
    validate_pdf_file,
    sanitize_url_for_logging,
    sanitize_error_message
)

app = func.FunctionApp()

_app_config: Optional[AppConfig] = None
_storage_client: Optional[AzureStorageClient] = None
_document_splitter: Optional[DocumentSplitter] = None


def get_config() -> AppConfig:
    """Get or create application configuration singleton.

    Returns:
        Application configuration

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _app_config

    if _app_config is None:
        try:
            _app_config = get_app_config()
            logging.info(
                f"Application configured for {_app_config.environment} environment: "
                f"blob_storage={_app_config.storage.account_name}, "
                f"queue_storage={_app_config.queue_storage.account_name}, "
                f"model={_app_config.gemini_model}"
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to load application configuration: {e}")

    return _app_config



def get_storage_client() -> AzureStorageClient:
    """Get or create storage client singleton.

    Returns:
        Initialized storage client

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _storage_client

    if _storage_client is None:
        config = get_config()

        try:
            _storage_client = AzureStorageClient(
                config.storage.account_name,
                config.storage.access_key
            )
            _storage_client.blob_service_client.get_service_properties()
            logging.info(
                f"Storage client initialized for {config.environment} environment: "
                f"{config.storage.account_name}"
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize storage client: {e}")

    return _storage_client


def get_document_splitter() -> DocumentSplitter:
    """Get or create document splitter singleton.

    Returns:
        Initialized document splitter

    Raises:
        ConfigurationError: If configuration is invalid
    """
    global _document_splitter

    if _document_splitter is None:
        config = get_config()

        try:
            _document_splitter = DocumentSplitter(
                config.gemini_api_key,
                config.gemini_model,
                config.gemini_timeout_seconds
            )
            logging.info(
                f"Document splitter initialized for {config.environment} environment: "
                f"model={config.gemini_model}, timeout={config.gemini_timeout_seconds}s"
            )
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize document splitter: {e}")

    return _document_splitter


def create_secure_temp_dir() -> Path:
    """Create temporary directory with secure permissions.

    Returns:
        Path to secure temporary directory

    Raises:
        ProcessingError: If directory creation fails
    """
    try:
        temp_base = Path(tempfile.gettempdir())
        random_suffix = secrets.token_hex(16)
        temp_dir = temp_base / f"docproc_{random_suffix}"

        temp_dir.mkdir(mode=0o700, parents=True, exist_ok=False)

        return temp_dir
    except Exception as e:
        raise ProcessingError(
            f"Failed to create temporary directory: {e}",
            ErrorSeverity.TRANSIENT,
            e
        )


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Safely cleanup temporary directory.

    Args:
        temp_dir: Directory to remove
    """
    try:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=False)
            logging.debug(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logging.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


def download_pdf(
    storage_client: AzureStorageClient,
    blob_url: str,
    destination: Path
) -> Path:
    """Download PDF from blob storage and validate.

    Args:
        storage_client: Azure storage client
        blob_url: URL to PDF blob
        destination: Local path to save PDF

    Returns:
        Path to downloaded PDF file

    Raises:
        ProcessingError: If download or validation fails
    """
    try:
        logging.info(f"Downloading PDF from: {sanitize_url_for_logging(blob_url)}")
        storage_client.download_blob(blob_url, str(destination))

        validate_pdf_file(str(destination))

        file_size = os.path.getsize(destination)
        logging.info(f"PDF downloaded successfully: {file_size / (1024*1024):.2f} MB")

        return destination

    except ValidationError as e:
        raise ProcessingError(str(e), ErrorSeverity.PERMANENT, e)
    except Exception as e:
        raise ProcessingError(
            f"Failed to download PDF: {sanitize_error_message(str(e))}",
            ErrorSeverity.TRANSIENT,
            e
        )


def process_pdf(
    document_splitter: DocumentSplitter,
    pdf_path: Path,
    output_dir: Path
) -> dict:
    """Extract and split documents from PDF.

    Args:
        document_splitter: Document splitter instance
        pdf_path: Path to PDF file
        output_dir: Directory for output files

    Returns:
        Processing results dictionary

    Raises:
        ProcessingError: If processing fails
    """
    try:
        output_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        logging.info("Starting document extraction and splitting")
        results = document_splitter.split_and_save(str(pdf_path), str(output_dir))

        doc_count = results.get('total_documents', 0)
        logging.info(f"Successfully processed {doc_count} documents")

        return results

    except ValidationError as e:
        raise ProcessingError(str(e), ErrorSeverity.PERMANENT, e)
    except Exception as e:
        raise ProcessingError(
            f"Failed to process PDF: {sanitize_error_message(str(e))}",
            ErrorSeverity.TRANSIENT,
            e
        )


def package_results(
    output_dir: Path,
    results: dict,
    correlation_key: str
) -> Path:
    """Create ZIP file from processing results.

    Args:
        output_dir: Directory containing output files
        results: Processing results dictionary
        correlation_key: Correlation key for naming

    Returns:
        Path to created ZIP file

    Raises:
        ProcessingError: If ZIP creation fails
    """
    try:
        logging.info("Creating results ZIP file")
        zip_filename = f"{correlation_key}_results.zip"
        zip_path = Path(create_results_zip(str(output_dir), results, zip_filename))

        zip_size = os.path.getsize(zip_path)
        logging.info(f"Results ZIP created: {zip_size / (1024*1024):.2f} MB")

        return zip_path

    except Exception as e:
        raise ProcessingError(
            f"Failed to create results ZIP: {sanitize_error_message(str(e))}",
            ErrorSeverity.TRANSIENT,
            e
        )


def upload_results(
    storage_client: AzureStorageClient,
    zip_path: Path,
    correlation_key: str,
    container: str
) -> str:
    """Upload results ZIP to blob storage.

    Args:
        storage_client: Azure storage client
        zip_path: Path to ZIP file
        correlation_key: Correlation key for blob path
        container: Blob container name

    Returns:
        URL of uploaded blob

    Raises:
        ProcessingError: If upload fails
    """
    try:
        logging.info("Uploading results ZIP to Azure Storage")
        blob_name = f"{correlation_key}/{zip_path.name}"
        zip_url = storage_client.upload_file(container, blob_name, str(zip_path))

        logging.info(f"Results uploaded to: {sanitize_url_for_logging(zip_url)}")

        return zip_url

    except Exception as e:
        raise ProcessingError(
            f"Failed to upload results: {sanitize_error_message(str(e))}",
            ErrorSeverity.TRANSIENT,
            e
        )


def send_success_result(
    output_queue: func.Out[str],
    correlation_key: str,
    results_url: str
) -> None:
    """Send success result message to output queue.

    Args:
        output_queue: Output queue binding
        correlation_key: Correlation key
        results_url: URL to results blob
    """
    result = {
        "correlationKey": correlation_key,
        "status": "success",
        "resultsBlobUrl": results_url
    }
    output_queue.set(json.dumps(result))
    logging.info(f"Success result sent for: {correlation_key[:8]}...")


def send_error_result(
    output_queue: func.Out[str],
    correlation_key: str,
    error_message: str
) -> None:
    """Send error result message to output queue.

    Args:
        output_queue: Output queue binding
        correlation_key: Correlation key
        error_message: Error description
    """
    result = {
        "correlationKey": correlation_key,
        "status": "failure",
        "errorMessage": sanitize_error_message(error_message)
    }
    output_queue.set(json.dumps(result))
    logging.error(f"Error result sent for: {correlation_key[:8]}...")


config = get_config()


@app.queue_trigger(
    arg_name="msg",
    queue_name=config.queue_storage.tasks_queue,
    connection="AzureWebJobsStorage")
@app.queue_output(
    arg_name="outputQueue",
    queue_name=config.queue_storage.results_queue,
    connection="AzureWebJobsStorage")
def process_pdf_file(msg: func.QueueMessage, outputQueue: func.Out[str]) -> None:
    """Process PDF document from queue trigger.

    This function orchestrates the document processing pipeline:
    1. Validate input message
    2. Download PDF from blob storage
    3. Extract and split documents
    4. Package results as ZIP
    5. Upload results to blob storage
    6. Send result message to output queue

    Args:
        msg: Queue message with correlationKey and pdfBlobUrl
        outputQueue: Output binding for results queue

    Raises:
        ConfigurationError: If required configuration is missing
        ProcessingError: If processing fails (may be re-raised for retry)
    """
    logging.info("Processing queue message")

    temp_dir: Optional[Path] = None
    correlation_key = "UNKNOWN"

    try:
        storage_client = get_storage_client()
        document_splitter = get_document_splitter()

        validated_request = ValidatedRequest.from_queue_message(
            msg.get_body(),
            config.storage.input_container
        )
        correlation_key = validated_request.correlation_key

        logging.info(f"Processing correlation key: {correlation_key[:8]}...")

        temp_dir = create_secure_temp_dir()

        pdf_path = download_pdf(
            storage_client,
            validated_request.pdf_blob_url,
            temp_dir / f"{secrets.token_hex(8)}.pdf"
        )

        results = process_pdf(
            document_splitter,
            pdf_path,
            temp_dir / "output"
        )

        zip_path = package_results(
            temp_dir / "output",
            results,
            correlation_key
        )

        zip_url = upload_results(
            storage_client,
            zip_path,
            correlation_key,
            config.storage.results_container
        )

        send_success_result(outputQueue, correlation_key, zip_url)

        logging.info(f"Successfully processed task: {correlation_key[:8]}...")

    except ConfigurationError as e:
        logging.critical(f"Configuration error: {e}")
        send_error_result(outputQueue, correlation_key, str(e))
        raise

    except ValidationError as e:
        logging.error(f"Validation error for {correlation_key[:8]}...: {e}")
        send_error_result(outputQueue, correlation_key, str(e))

    except ProcessingError as e:
        if e.severity == ErrorSeverity.CRITICAL:
            logging.critical(
                f"Critical error for {correlation_key[:8]}...: {e}",
                exc_info=e.original
            )
            send_error_result(outputQueue, correlation_key, str(e))
            raise

        elif e.severity == ErrorSeverity.TRANSIENT:
            logging.warning(
                f"Transient error for {correlation_key[:8]}...: {e}"
            )
            send_error_result(outputQueue, correlation_key, str(e))
            raise

        else:
            logging.error(f"Permanent error for {correlation_key[:8]}...: {e}")
            send_error_result(outputQueue, correlation_key, str(e))

    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logging.exception(f"Unexpected error for {correlation_key[:8]}...: {sanitized_error}")
        send_error_result(outputQueue, correlation_key, sanitized_error)
        raise

    finally:
        if temp_dir:
            cleanup_temp_dir(temp_dir)
