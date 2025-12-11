from azure.storage.queue import QueueClient
import os

CONN_STR = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
QUEUE_NAME = "test-queue"
POISON_QUEUE_NAME = "test-queue-poison"

def check_queue(queue_name):
    print(f"Checking queue: {queue_name}")
    try:
        client = QueueClient.from_connection_string(CONN_STR, queue_name)
        props = client.get_queue_properties()
        count = props.approximate_message_count
        print(f"Message count: {count}")
        
        if count > 0:
            messages = client.peek_messages(max_messages=5)
            for msg in messages:
                print(f" - Message: {msg.content}")
    except Exception as e:
        print(f"Error checking {queue_name}: {e}")

if __name__ == "__main__":
    check_queue(QUEUE_NAME)
    check_queue(POISON_QUEUE_NAME)
