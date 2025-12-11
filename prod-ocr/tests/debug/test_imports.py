import azure.functions as func
import logging
import json

print("Imports successful")

msg_content = '{"correlationKey": "b1d8a313-dd31-4454-bce5-bfe8d6b02375", "pdfBlobUrl": "http://127.0.0.1:10000/devstoreaccount1/ocr-processing-input/b1d8a313-dd31-4454-bce5-bfe8d6b02375/82914024_ORG_u0mmub58pk2eayin8fw1gw00000000.PDF"}'

try:
    msg = func.QueueMessage(body=msg_content)
    print(f"QueueMessage created: {msg.get_body().decode('utf-8')}")
except Exception as e:
    print(f"Error creating QueueMessage: {e}")
