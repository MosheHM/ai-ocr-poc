"""Example client script to send a processing task to the queue."""
import os
import sys
import uuid
import json
import base64
import argparse
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.queue import QueueClient

from modules.azure import AzureStorageClient
from modules.config import get_storage_config, get_queue_storage_config
from modules.validators import validate_correlation_key, validate_pdf_file, ValidationError

load_dotenv(Path(__file__).parent / '.env')


def main():
    """Send a processing task to the queue."""
    parser = argparse.ArgumentParser(
        description='Send a document processing task to Azure Queue'
    )
    parser.add_argument(
        'pdf_path',
        help='Path to the PDF file to process'
    )
    parser.add_argument(
        '--container',
        help='Azure Blob container for input PDFs',
        default='ocr-processing-input'
    )
    parser.add_argument(
        '--queue',
        help='Name of the tasks queue',
        default='processing-tasks'
    )
    parser.add_argument(
        '--correlation-key',
        help='Correlation key (default: generated UUID)',
        default=None
    )

    args = parser.parse_args()

    try:
        storage_config = get_storage_config()
        queue_storage_config = get_queue_storage_config()
        print(f"Using blob storage: {storage_config.account_name}")
        print(f"Using queue storage: {queue_storage_config.account_name}")
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set the required environment variables in your .env file")
        sys.exit(1)

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.is_file():
        print(f"Error: Not a file: {pdf_path}")
        sys.exit(1)

    # Generate and validate correlation key
    if args.correlation_key:
        try:
            correlation_key = validate_correlation_key(args.correlation_key)
        except ValidationError as e:
            print(f"Error: Invalid correlation key: {e}")
            sys.exit(1)
    else:
        correlation_key = str(uuid.uuid4())

    try:
        validate_pdf_file(str(pdf_path))
    except ValidationError as e:
        print(f"Error: Invalid PDF file: {e}")
        sys.exit(1)

    print("=" * 60)
    print("SENDING PROCESSING TASK")
    print("=" * 60)
    print(f"Correlation Key: {correlation_key}")
    print(f"PDF File: {pdf_path.name}")
    print(f"File Size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"Container: {args.container}")
    print(f"Queue: {args.queue}")
    print()

    try:
        storage_client = AzureStorageClient(
            storage_config.account_name,
            storage_config.access_key,
            connection_string=storage_config.connection_string
        )

        # Use queue-specific storage config for queue operations
        if queue_storage_config.connection_string:
            queue_client = QueueClient.from_connection_string(
                conn_str=queue_storage_config.connection_string,
                queue_name=args.queue
            )
        else:
            account_url = f"https://{queue_storage_config.account_name}.queue.core.windows.net"
            queue_client = QueueClient(
                account_url=account_url,
                queue_name=args.queue,
                credential=queue_storage_config.access_key
            )

        # Ensure container exists
        try:
            storage_client.blob_service_client.create_container(args.container)
            print(f"Created container '{args.container}'")
        except Exception as e:
            print(f"Container creation warning: {e}")

        # Ensure queue exists
        try:
            queue_client.create_queue()
            print(f"Created queue '{args.queue}'")
        except Exception as e:
            print(f"Queue creation warning: {e}")

        # Upload PDF to Azure Storage
        print(f"Uploading PDF to Azure Storage...")
        blob_name = f"{correlation_key}/{pdf_path.name}"
        pdf_url = storage_client.upload_file(
            args.container,
            blob_name,
            str(pdf_path)
        )
        print(f"PDF uploaded successfully")
        print()

        # Create task message
        task_message = {
            "correlationKey": correlation_key,
            "pdfBlobUrl": pdf_url
        }

        # Encode message to Base64 (required by Azure Functions Queue Trigger)
        message_content = json.dumps(task_message)
        message_bytes = message_content.encode('utf-8')
        base64_message = base64.b64encode(message_bytes).decode('utf-8')

        # Send message to queue
        print(f"Sending task message to queue '{args.queue}'...")
        queue_client.send_message(base64_message)
        print("Task message sent successfully!")
        print()

        print("=" * 60)
        print("TASK SUBMITTED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Correlation Key: {correlation_key}")
        print()
        print("Use this correlation key to retrieve results:")
        print(f"  python get_results.py --correlation-key={correlation_key}")
        print()
        print("Results will appear in the 'processing-tasks-results' queue")
        print("after processing completes.")
        print("=" * 60)

    except Exception as e:
        print()
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
