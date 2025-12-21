import os
from azure.storage.queue import QueueClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path('.env.development'))

connection_string = os.getenv('QUEUE_STORAGE_CONNECTION_STRING')
queue_name = 'processing-tasks-results'

print(f"Peeking queue: {queue_name}")
queue_client = QueueClient.from_connection_string(connection_string, queue_name)

try:
    properties = queue_client.get_queue_properties()
    print(f"Approximate message count: {properties.approximate_message_count}")
    
    messages = queue_client.peek_messages(max_messages=5)
    for msg in messages:
        print(f"Message ID: {msg.id}")
        print(f"Content: {msg.content}")
        print("-" * 20)
        
except Exception as e:
    print(f"Error: {e}")

