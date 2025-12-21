import os
from azure.storage.queue import QueueServiceClient
from modules.config import get_queue_storage_config

try:
    config = get_queue_storage_config()
    print(f"Connecting to: {config.account_name}")
    
    if config.connection_string:
        service_client = QueueServiceClient.from_connection_string(config.connection_string)
    else:
        # Fallback for managed identity or other auth (not used here)
        print("No connection string found.")
        exit(1)

    print("Listing queues:")
    queues = service_client.list_queues()
    for queue in queues:
        print(f" - {queue.name}")

except Exception as e:
    print(f"Error: {e}")
