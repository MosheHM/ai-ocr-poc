# Service Bus Quick Start Guide

## TL;DR - What Changed

✅ **Dependencies**: Added `azure-servicebus>=7.11.0`
✅ **Triggers**: `queue_trigger` → `service_bus_queue_trigger`
✅ **Connection**: `AzureWebJobsStorage` → `ServiceBusConnection`
✅ **New Scripts**: `send_task_servicebus.py`, `get_results_servicebus.py`

## Quick Setup (5 Steps)

### 1. Create Service Bus in Azure

```bash
# Azure CLI
az servicebus namespace create --name <your-app>-sb --resource-group <rg> --sku Standard
az servicebus queue create --namespace-name <your-app>-sb --name processing-tasks
az servicebus queue create --namespace-name <your-app>-sb --name processing-tasks-results

# Get connection string
az servicebus namespace authorization-rule keys list \
  --namespace-name <your-app>-sb \
  --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv
```

### 2. Update Configuration

**local.settings.json** (add this):
```json
"ServiceBusConnection": "Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<key>"
```

**Azure App Settings** (add this):
```
Name: ServiceBusConnection
Value: Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=<key>
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# or
uv sync
```

### 4. Test Locally

```bash
# Start function
func start

# Send test (new terminal)
python send_task_servicebus.py path/to/test.pdf

# Get results (new terminal)
python get_results_servicebus.py <correlation-key>
```

### 5. Deploy

```bash
git add .
git commit -m "feat: Migrate to Azure Service Bus"
git push

# Deploy using your method (Docker, func deploy, etc.)
```

## Files Modified

| File | Change |
|------|--------|
| `requirements.txt` | Added `azure-servicebus>=7.11.0` |
| `function_app.py` | Changed to Service Bus triggers |
| `local.settings.json` | Added `ServiceBusConnection` |
| NEW: `send_task_servicebus.py` | Service Bus message sender |
| NEW: `get_results_servicebus.py` | Service Bus result retriever |
| NEW: `scripts/admin/init_servicebus_queues.py` | Queue setup script |
| NEW: `docs/SERVICE_BUS_MIGRATION.md` | Full migration guide |

## Key Differences from Queue Storage

### Sending Messages

**Before (Queue Storage)**:
```python
from azure.storage.queue import QueueClient

queue = QueueClient.from_connection_string(conn_str, "processing-tasks")
queue.send_message(json.dumps(message))
```

**After (Service Bus)**:
```python
from azure.servicebus import ServiceBusClient, ServiceBusMessage

with ServiceBusClient.from_connection_string(conn_str) as client:
    with client.get_queue_sender("processing-tasks") as sender:
        message = ServiceBusMessage(body=json.dumps(data))
        sender.send_messages(message)
```

### Function Trigger

**Before (Queue Storage)**:
```python
@app.queue_trigger(
    arg_name="msg",
    queue_name="processing-tasks",
    connection="AzureWebJobsStorage")
def process(msg: func.QueueMessage):
    body = msg.get_body()
```

**After (Service Bus)**:
```python
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="processing-tasks",
    connection="ServiceBusConnection")
def process(msg: func.ServiceBusMessage):
    body = msg.get_body()
```

## Testing Commands

```bash
# Initialize queues
python scripts/admin/init_servicebus_queues.py

# Send task
python send_task_servicebus.py samples/test.pdf

# Get results
python get_results_servicebus.py <correlation-key>

# Check queue status (use Azure Portal or SDK)
```

## Monitoring

**Azure Portal** → Service Bus Namespace → Queues → Select Queue → Metrics

Watch for:
- 📈 Active Messages (should be low if processing is working)
- ⚠️ Dead-letter Messages (investigate if > 0)
- 📊 Incoming vs Outgoing Messages (should be balanced)

## Rollback (If Needed)

1. Revert `function_app.py` changes
2. Use old `send_task.py` and `get_results.py`
3. Redeploy

## Need Help?

- 📖 Full guide: `docs/SERVICE_BUS_MIGRATION.md`
- 🔍 Azure docs: https://docs.microsoft.com/azure/service-bus-messaging/
- 🐛 Check dead-letter queue if messages fail
- 📊 Monitor metrics in Azure Portal

## Benefits You Get

✅ **Reliability**: Messages guaranteed not to be lost
✅ **Dead-letter Queue**: Failed messages preserved for investigation
✅ **Larger Messages**: 256KB vs 64KB
✅ **Better Ordering**: FIFO with sessions
✅ **Duplicate Detection**: Automatic
✅ **Advanced Features**: Scheduled messages, transactions, etc.
