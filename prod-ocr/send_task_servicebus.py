"""Example client script to send a processing task to Azure Service Bus."""
import os
import sys
import uuid
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from modules.azure import AzureStorageClient
from modules.config import get_storage_config
from modules.validators import validate_correlation_key, validate_pdf_file, ValidationError

load_dotenv(Path(__file__).parent / '.env')


def main():
    """Send a processing task to Azure Service Bus queue."""
    parser = argparse.ArgumentParser(
        description='Send a document processing task to Azure Service Bus'
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

    # Get Service Bus connection string
    servicebus_conn_str = os.getenv('ServiceBusConnection')
    if not servicebus_conn_str:
        print("Error: ServiceBusConnection not found in environment")
        print("Please set ServiceBusConnection in your .env file")
        sys.exit(1)

    try:
        storage_config = get_storage_config()
        print(f"Using blob storage: {storage_config.account_name}")
        print(f"Using Service Bus queue: {args.queue}")
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

    # Upload PDF to blob storage
    print(f"\nUploading PDF to blob storage...")
    storage_client = AzureStorageClient(
        storage_config.account_name,
        storage_config.access_key,
        storage_config.connection_string
    )

    blob_name = f"{correlation_key}/{pdf_path.name}"
    pdf_blob_url = storage_client.upload_file(
        args.container,
        blob_name,
        str(pdf_path)
    )
    print(f"PDF uploaded: {pdf_blob_url}")

    # Send message to Service Bus
    print(f"\nSending task to Service Bus queue '{args.queue}'...")

    message_body = {
        "correlationKey": correlation_key,
        "pdfBlobUrl": pdf_blob_url
    }

    try:
        # Create Service Bus client and sender
        with ServiceBusClient.from_connection_string(servicebus_conn_str) as client:
            with client.get_queue_sender(args.queue) as sender:
                # Create message
                message = ServiceBusMessage(
                    body=json.dumps(message_body),
                    content_type="application/json",
                    correlation_id=correlation_key
                )

                # Send message
                sender.send_messages(message)

        print(f"✅ Task sent successfully!")
        print(f"\nDetails:")
        print(f"  Correlation Key: {correlation_key}")
        print(f"  PDF Blob URL: {pdf_blob_url}")
        print(f"  Queue: {args.queue}")
        print(f"\nTo check results, run:")
        print(f"  python get_results_servicebus.py {correlation_key}")

    except Exception as e:
        print(f"Error sending message to Service Bus: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
