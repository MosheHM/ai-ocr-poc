import os
import json
from pathlib import Path
from azure.storage.queue import QueueClient

# Load local settings
def load_settings():
    settings = {}
    settings_path = Path(__file__).parent.parent.parent / 'local.settings.json'
    if settings_path.exists():
        with open(settings_path, 'r') as f:
            data = json.load(f)
            settings = data.get('Values', {})
    return settings

settings = load_settings()
conn_str = settings.get('AzureWebJobsStorage', 'UseDevelopmentStorage=true')

queue_names = ["processing-tasks", "processing-tasks-poison"]

for queue_name in queue_names:
    queue_client = QueueClient.from_connection_string(conn_str, queue_name)
    try:
        properties = queue_client.get_queue_properties()
        print(f"Queue '{queue_name}' has {properties.approximate_message_count} messages.")

        if properties.approximate_message_count > 0:
            print("Peeking messages:")
            peeked_messages = queue_client.peek_messages(max_messages=5)
            for msg in peeked_messages:
                print(f"Message ID: {msg.id}")
                print(f"Content: {msg.content}")
    except Exception as e:
        print(f"Error checking queue {queue_name}: {e}")
