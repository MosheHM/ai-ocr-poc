"""Initialize Azure Service Bus queues for document processing."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.servicebus.management import ServiceBusAdministrationClient
from azure.core.exceptions import ResourceExistsError

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


def create_queue_if_not_exists(admin_client, queue_name):
    """Create a Service Bus queue if it doesn't exist."""
    try:
        admin_client.create_queue(queue_name)
        print(f"✅ Created queue: {queue_name}")
        return True
    except ResourceExistsError:
        print(f"ℹ️  Queue already exists: {queue_name}")
        return False
    except Exception as e:
        print(f"❌ Error creating queue {queue_name}: {e}")
        return False


def main():
    """Initialize Service Bus queues."""
    print("Initializing Azure Service Bus queues...")
    print()

    # Get Service Bus connection string
    connection_string = os.getenv('ServiceBusConnection')
    if not connection_string:
        print("❌ Error: ServiceBusConnection not found in environment")
        print("Please set ServiceBusConnection in your .env file")
        print()
        print("Example:")
        print('  ServiceBusConnection="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<key>"')
        sys.exit(1)

    # Get queue names from environment
    tasks_queue = os.getenv('TASKS_QUEUE', 'processing-tasks')
    results_queue = os.getenv('RESULTS_QUEUE', 'processing-tasks-results')

    print(f"Tasks queue: {tasks_queue}")
    print(f"Results queue: {results_queue}")
    print()

    try:
        # Create Service Bus administration client
        with ServiceBusAdministrationClient.from_connection_string(connection_string) as admin_client:
            # Create queues
            created_count = 0

            if create_queue_if_not_exists(admin_client, tasks_queue):
                created_count += 1

            if create_queue_if_not_exists(admin_client, results_queue):
                created_count += 1

            print()
            if created_count > 0:
                print(f"✅ Successfully created {created_count} queue(s)")
            else:
                print("✅ All queues already exist")

            # List all queues
            print()
            print("Current Service Bus queues:")
            for queue in admin_client.list_queues():
                print(f"  - {queue.name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Common issues:")
        print("  - Invalid Service Bus connection string")
        print("  - Insufficient permissions (need Manage permission)")
        print("  - Service Bus namespace doesn't exist")
        sys.exit(1)


if __name__ == '__main__':
    main()
