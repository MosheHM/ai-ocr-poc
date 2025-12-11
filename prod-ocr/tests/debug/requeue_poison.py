import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.queue import QueueClient, BinaryBase64DecodePolicy, BinaryBase64EncodePolicy

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

def main():
    # connection_string = os.getenv('DEV_QUEUE_STORAGE_CONNECTION_STRING')
    connection_string = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
    if not connection_string:
        print("Error: DEV_QUEUE_STORAGE_CONNECTION_STRING not set")
        sys.exit(1)

    poison_queue_name = "processing-tasks-poison"
    main_queue_name = "processing-tasks"

    poison_client = QueueClient.from_connection_string(
        conn_str=connection_string,
        queue_name=poison_queue_name
    )

    main_client = QueueClient.from_connection_string(
        conn_str=connection_string,
        queue_name=main_queue_name
    )

    properties = poison_client.get_queue_properties()
    count = properties.approximate_message_count
    print(f"Poison queue has {count} messages.")

    if count == 0:
        print("No messages to requeue.")
        return

    messages = poison_client.receive_messages(max_messages=32)
    for msg in messages:
        print(f"Requeuing message: {msg.id}")
        # Send to main queue
        main_client.send_message(msg.content)
        # Delete from poison queue
        poison_client.delete_message(msg)
        print("Done.")

if __name__ == "__main__":
    main()
