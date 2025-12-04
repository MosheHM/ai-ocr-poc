"""Example client script to retrieve processing results from the queue."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.queue import QueueClient

from modules.azure import AzureStorageClient
from modules.validators import validate_correlation_key, ValidationError

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Queue configuration
VISIBILITY_TIMEOUT_SECONDS = 300  # 5 minutes


def main():
    """Retrieve processing results from the results queue."""
    parser = argparse.ArgumentParser(
        description='Retrieve processing results from Azure Queue'
    )
    parser.add_argument(
        '--correlation-key',
        help='Correlation key to filter results (optional)',
        default=None
    )
    parser.add_argument(
        '--queue',
        help='Name of the results queue',
        default='processing-tasks-results'
    )
    parser.add_argument(
        '--download',
        help='Download results ZIP to this directory',
        default=None
    )
    parser.add_argument(
        '--max-messages',
        type=int,
        help='Maximum number of messages to check',
        default=10
    )

    args = parser.parse_args()

    # Validate required environment variables
    storage_account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    storage_access_key = os.getenv('AZURE_STORAGE_ACCESS_KEY')

    if not storage_account_name or not storage_access_key:
        print("Error: AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCESS_KEY environment variables not set")
        print("Please set them in your .env file")
        sys.exit(1)

    # Validate correlation key if provided
    if args.correlation_key:
        try:
            args.correlation_key = validate_correlation_key(args.correlation_key)
        except ValidationError as e:
            print(f"Error: Invalid correlation key: {e}")
            sys.exit(1)

    print("=" * 60)
    print("CHECKING RESULTS QUEUE")
    print("=" * 60)
    print(f"Queue: {args.queue}")
    if args.correlation_key:
        print(f"Filtering by correlation key: {args.correlation_key[:8]}...")
    print()

    try:
        # Initialize clients
        # Create queue client using account URL
        account_url = f"https://{storage_account_name}.queue.core.windows.net"
        queue_client = QueueClient(
            account_url=account_url,
            queue_name=args.queue,
            credential=storage_access_key
        )
        storage_client = AzureStorageClient(storage_account_name, storage_access_key) if args.download else None

        # Check messages
        found_count = 0
        for i in range(args.max_messages):
            messages = queue_client.receive_messages(
                messages_per_page=1,
                visibility_timeout=VISIBILITY_TIMEOUT_SECONDS
            )

            message = None
            for msg in messages:
                message = msg
                break

            if message is None:
                if found_count == 0:
                    print("No messages in queue")
                break

            try:
                result = json.loads(message.content)

                # Extract correlation key
                correlation_key = result.get('correlationKey')
                if not correlation_key:
                    print(f"Warning: Message missing correlationKey, skipping")
                    continue

                # Filter by correlation key if specified
                if args.correlation_key and correlation_key != args.correlation_key:
                    continue

                found_count += 1
                print("=" * 60)
                print(f"RESULT #{found_count}")
                print("=" * 60)
                print(f"Correlation Key: {correlation_key}")
                print(f"Status: {result.get('status')}")
                print()

                if result.get('status') == "success":
                    results_url = result.get('resultsBlobUrl')
                    if results_url:
                        print(f"Results ZIP URL: {results_url[:80]}...")

                        if args.download and storage_client:
                            download_dir = Path(args.download)
                            download_dir.mkdir(parents=True, exist_ok=True)
                            zip_filename = f"{correlation_key}_results.zip"
                            zip_path = download_dir / zip_filename

                            print(f"\nDownloading to: {zip_path}")
                            try:
                                # Update visibility timeout before download
                                queue_client.update_message(
                                    message.id,
                                    message.pop_receipt,
                                    visibility_timeout=VISIBILITY_TIMEOUT_SECONDS
                                )

                                storage_client.download_blob(results_url, str(zip_path))
                                print("Download complete!")

                            except Exception as e:
                                print(f"Error downloading results: {e}")
                                # Don't delete message on download error
                                continue

                else:
                    error_msg = result.get('errorMessage', 'Unknown error')
                    print(f"Error: {error_msg}")

                print()

                # Delete message after successful processing
                try:
                    queue_client.delete_message(message.id, message.pop_receipt)
                    print("Message removed from queue")
                except Exception as e:
                    print(f"Warning: Failed to delete message: {e}")

                print()

                # If we found the specific correlation key, we're done
                if args.correlation_key and correlation_key == args.correlation_key:
                    break

            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in message: {e}")
                continue

            except Exception as e:
                print(f"Error processing message: {e}")
                continue

        print("=" * 60)
        if found_count == 0:
            if args.correlation_key:
                print(f"No results found for correlation key: {args.correlation_key[:8]}...")
            else:
                print("No results found in queue")
        else:
            print(f"Found {found_count} result(s)")
        print("=" * 60)

    except Exception as e:
        print()
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
