import sys
import os
from azure.storage.queue import QueueClient
from azure.core.exceptions import ResourceExistsError
from modules.config import get_queue_storage_config

def create_queues():
    print("Initializing queues based on project configuration...")
    
    try:
        # Load configuration using the project's config module
        # This will automatically load .env and .env.development
        config = get_queue_storage_config()
        
        if not config.connection_string:
            print("❌ Error: No connection string found in configuration.")
            return

        queues_to_create = [
            config.tasks_queue,
            config.results_queue,
            f"{config.tasks_queue}-poison"
        ]

        print(f"Using connection string for account: {config.account_name}")

        for queue_name in queues_to_create:
            try:
                client = QueueClient.from_connection_string(config.connection_string, queue_name)
                client.create_queue()
                print(f"✅ Created queue: {queue_name}")
            except ResourceExistsError:
                print(f"ℹ️  Queue already exists: {queue_name}")
            except Exception as e:
                print(f"❌ Failed to create queue {queue_name}: {e}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")

if __name__ == "__main__":
    create_queues()
