from azure.storage.blob import BlobServiceClient
import os

conn_str = "DefaultEndpointsProtocol=http;AccountName=stamitalmisc;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/stamitalmisc;QueueEndpoint=http://127.0.0.1:10001/stamitalmisc;"

try:
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    print("Listing containers...")
    containers = blob_service_client.list_containers()
    for c in containers:
        print(c.name)
    print("Done listing.")
    
    print("Creating container 'test-container'...")
    blob_service_client.create_container("test-container")
    print("Created.")
except Exception as e:
    print(f"Error: {e}")
