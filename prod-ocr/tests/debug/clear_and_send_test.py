from azure.storage.queue import QueueClient
import os

# Hardcoded for debugging
CONN_STR = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
POISON_QUEUE = "processing-tasks-poison"
MAIN_QUEUE = "processing-tasks"

def clear_queues():
    qc_poison = QueueClient.from_connection_string(CONN_STR, POISON_QUEUE)
    qc_main = QueueClient.from_connection_string(CONN_STR, MAIN_QUEUE)

    try:
        qc_poison.clear_messages()
        print(f"Cleared {POISON_QUEUE}")
    except Exception as e:
        print(f"Error clearing {POISON_QUEUE}: {e}")

    try:
        qc_main.clear_messages()
        print(f"Cleared {MAIN_QUEUE}")
    except Exception as e:
        print(f"Error clearing {MAIN_QUEUE}: {e}")

    # Send simple test message
    try:
        qc_main.send_message("test")
        print(f"Sent 'test' to {MAIN_QUEUE}")
    except Exception as e:
        print(f"Error sending to {MAIN_QUEUE}: {e}")

if __name__ == "__main__":
    clear_queues()
