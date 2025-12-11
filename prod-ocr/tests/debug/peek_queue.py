from azure.storage.queue import QueueClient
import os

conn_str = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
queue_name = "processing-tasks-poison"

try:
    queue_client = QueueClient.from_connection_string(conn_str, queue_name)
    properties = queue_client.get_queue_properties()
    print(f"Queue '{queue_name}' exists. Approximate message count: {properties.approximate_message_count}")
    
    messages = queue_client.peek_messages()
    for msg in messages:
        print(f"Message: {msg.content}")

except Exception as e:
    print(f"Error: {e}")
