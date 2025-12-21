"""Example client script to retrieve processing results from Azure Service Bus."""
import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient

load_dotenv(Path(__file__).parent / '.env')


def main():
    """Retrieve processing results from Azure Service Bus queue."""
    parser = argparse.ArgumentParser(
        description='Retrieve document processing results from Azure Service Bus'
    )
    parser.add_argument(
        'correlation_key',
        help='Correlation key of the task to retrieve results for'
    )
    parser.add_argument(
        '--queue',
        help='Name of the results queue',
        default='processing-tasks-results'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        help='Timeout in seconds to wait for results',
        default=30
    )
    parser.add_argument(
        '--max-messages',
        type=int,
        help='Maximum number of messages to check',
        default=10
    )

    args = parser.parse_args()

    # Get Service Bus connection string
    servicebus_conn_str = os.getenv('ServiceBusConnection')
    if not servicebus_conn_str:
        print("Error: ServiceBusConnection not found in environment")
        print("Please set ServiceBusConnection in your .env file")
        sys.exit(1)

    print(f"Looking for results with correlation key: {args.correlation_key}")
    print(f"Checking queue: {args.queue}")
    print(f"Timeout: {args.timeout} seconds")
    print()

    try:
        # Create Service Bus client and receiver
        with ServiceBusClient.from_connection_string(servicebus_conn_str) as client:
            with client.get_queue_receiver(args.queue) as receiver:
                messages_checked = 0
                found = False

                # Receive messages with peek lock (doesn't remove from queue)
                for msg in receiver.receive_messages(
                    max_message_count=args.max_messages,
                    max_wait_time=args.timeout
                ):
                    messages_checked += 1

                    try:
                        # Parse message body
                        body = json.loads(str(msg))

                        # Check if this is the result we're looking for
                        if body.get('correlationKey') == args.correlation_key:
                            found = True
                            print(f"✅ Results found!")
                            print(f"\nStatus: {body.get('status')}")

                            if body.get('status') == 'success':
                                print(f"Results URL: {body.get('resultsBlobUrl')}")
                            else:
                                print(f"Error: {body.get('errorMessage', 'Unknown error')}")

                            print(f"\nFull result:")
                            print(json.dumps(body, indent=2))

                            # Complete (remove) the message from queue
                            receiver.complete_message(msg)
                            break
                        else:
                            # Not our message, abandon it so it goes back to queue
                            receiver.abandon_message(msg)

                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON in message: {e}")
                        receiver.abandon_message(msg)
                        continue
                    except Exception as e:
                        print(f"Warning: Error processing message: {e}")
                        receiver.abandon_message(msg)
                        continue

                if not found:
                    print(f"❌ No results found for correlation key: {args.correlation_key}")
                    print(f"Messages checked: {messages_checked}")
                    print(f"\nPossible reasons:")
                    print(f"  - Task is still processing")
                    print(f"  - Incorrect correlation key")
                    print(f"  - Results were already retrieved")
                    print(f"  - Task failed before sending result")

    except Exception as e:
        print(f"Error connecting to Service Bus: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
