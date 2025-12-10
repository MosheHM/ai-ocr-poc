# Queue Storage Configuration - Summary

## What Was Added

The system now supports using a **separate Azure Storage account** for queue operations, independent from the blob storage account used for PDF files and results.

## Changes Made

### 1. Configuration Module (`modules/config.py`)

**New Components:**
- `QueueStorageConfig` dataclass - Configuration for queue storage
- `get_queue_storage_config()` function - Load queue storage configuration
- Updated `AppConfig` to include `queue_storage` field

**Behavior:**
- By default, uses the same storage account for blobs and queues
- Falls back gracefully to blob storage credentials if queue storage not specified
- Supports environment-specific configuration (DEV_*/PROD_*)

### 2. Environment Variables

**New Variables Added to `.env.example`:**

Development:
```bash
DEV_QUEUE_STORAGE_ACCOUNT_NAME=devstoreaccount1  # Optional
DEV_QUEUE_STORAGE_ACCESS_KEY=<key>               # Optional
DEV_TASKS_QUEUE=-tasks
DEV_RESULTS_QUEUE=-results
```

Production:
```bash
PROD_QUEUE_STORAGE_ACCOUNT_NAME=yourqueueaccount  # Optional
PROD_QUEUE_STORAGE_ACCESS_KEY=<key>               # Optional
PROD_TASKS_QUEUE=-tasks
PROD_RESULTS_QUEUE=-results
```


### 3. Updated Scripts

**`send_task.py`:**
- Loads both `storage_config` and `queue_storage_config`
- Uses queue storage config for queue operations
- Displays both storage accounts in use

**`get_results.py`:**
- Loads both storage configs
- Uses queue storage config for queue operations
- Shows which storage accounts are being used

**`function_app.py`:**
- Uses `get_app_config()` which includes queue storage
- Logs both blob and queue storage accounts on startup

### 4. Configuration Templates

**`local.settings.json.example`:**
```json
{
  "Values": {
    "QUEUE_STORAGE_ACCOUNT_NAME": "",
    "QUEUE_STORAGE_ACCESS_KEY": "",
    "TASKS_QUEUE": "processing-tasks",
    "RESULTS_QUEUE": "processing-tasks-results"
  }
}
```

**`local.settings.json.production.example`:**
- Added same queue storage variables for production

### 5. Documentation

**New Documentation:**
- `docs/QUEUE_STORAGE_SETUP.md` - Comprehensive guide on queue storage configuration

**Updated Documentation:**
- `docs/ENVIRONMENT_SETUP.md` - Added queue storage section
- `ENVIRONMENT_SETUP_SUMMARY.md` - Added queue storage overview
- `README.md` - Added queue storage support section

## Usage Examples

### Example 1: Same Storage Account (Default)

No additional configuration needed. The system automatically uses blob storage account for queues:

```bash
# .env
ENVIRONMENT=development
DEV_AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
DEV_AZURE_STORAGE_ACCESS_KEY=<key>
```

Output:
```
Using blob storage: devstoreaccount1
Using queue storage: devstoreaccount1
```

### Example 2: Separate Queue Storage Account

Configure separate queue storage:

```bash
# .env
ENVIRONMENT=production
PROD_AZURE_STORAGE_ACCOUNT_NAME=myblobs
PROD_AZURE_STORAGE_ACCESS_KEY=<blob-key>

PROD_QUEUE_STORAGE_ACCOUNT_NAME=myqueues
PROD_QUEUE_STORAGE_ACCESS_KEY=<queue-key>
```

Output:
```
Using blob storage: myblobs
Using queue storage: myqueues
```

### Example 3: Environment-Specific Queues

Different queue names per environment:



## Benefits

### 1. Performance Isolation
- Queue operations don't impact blob storage performance
- Blob operations don't impact queue throughput
- Independent scaling based on workload

### 2. Cost Management
- Track costs separately for messaging vs storage
- Optimize spending per service type
- Use different storage tiers (e.g., Premium queues, Standard blobs)

### 3. Security Boundaries
- Apply different access policies to queues vs blobs
- Separate audit logs
- Different network rules per storage type

### 4. Regional Flexibility
- Place queues near compute resources for low latency
- Place blobs near users for fast access
- Multi-region deployments

### 5. Operational Benefits
- Separate lifecycle policies
- Independent backup/restore
- Different retention policies

## Migration Path

### Step 1: Evaluate Need
Current setup works fine? No changes needed. Consider separate storage when:
- Processing >1,000 messages/minute
- Experiencing throttling
- Need granular cost tracking
- Compliance requires separation

### Step 2: Create Queue Storage (Optional)
```bash
az storage account create \
  --name yourqueueaccount \
  --resource-group your-rg \
  --location eastus \
  --sku Standard_LRS
```

### Step 3: Create Queues
```bash
az storage queue create \
  --name processing-tasks \
  --account-name yourqueueaccount

az storage queue create \
  --name processing-tasks-results \
  --account-name yourqueueaccount
```

### Step 4: Update Configuration
Add queue storage variables to `.env` or `local.settings.json`

### Step 5: Deploy and Verify
Scripts will log which storage accounts they're using

## Backward Compatibility

✅ **Fully backward compatible**

- Existing configurations work without changes
- If queue storage variables not specified, uses blob storage account
- No breaking changes to existing deployments
- Graceful fallback to single storage account

## Testing

Verify your configuration:

```bash
# Run send_task to see which storage accounts are used
python send_task.py path/to/test.pdf

# Expected output shows both accounts
Using blob storage: myblobs
Using queue storage: myqueues
```

Check Azure Function logs:
```
Application configured for production environment:
  blob_storage=myblobs,
  queue_storage=myqueues,
  model=gemini-2.5-flash
```

## Troubleshooting

### Issue: "Queue not found"
**Cause:** Queues don't exist in queue storage account
**Solution:** Create queues in the queue storage account

### Issue: Scripts show same account for both
**Cause:** Queue storage variables not set or empty
**Solution:** This is expected default behavior (not an error)

### Issue: "Authentication failed" for queues only
**Cause:** Queue storage credentials incorrect
**Solution:** Verify `QUEUE_STORAGE_ACCESS_KEY`

### Issue: Blobs work but queues fail
**Cause:** Separate queue storage is configured but has issues
**Solution:** Check queue storage account exists and has correct credentials

## Best Practices

1. **Start Simple**: Use one storage account initially
2. **Monitor First**: Track metrics before deciding to separate
3. **Separate When Needed**: Only separate if you have specific requirements
4. **Document Config**: Keep track of which storage accounts are used
5. **Test Thoroughly**: Verify both accounts work after configuration
6. **Use Managed Identities**: Prefer managed identities over access keys in production
7. **Set Up Alerts**: Monitor queue depth and storage metrics

## Additional Resources

- [Queue Storage Setup Guide](docs/QUEUE_STORAGE_SETUP.md) - Detailed configuration
- [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md) - General environment setup
- [Azure Queue Storage Documentation](https://docs.microsoft.com/azure/storage/queues/)

## Summary

The system now supports optional separate queue storage for:
- ✅ Better performance isolation
- ✅ Granular cost management
- ✅ Enhanced security boundaries
- ✅ Regional flexibility
- ✅ Fully backward compatible
- ✅ Easy to configure
- ✅ Automatic fallback to single account

No changes required to existing deployments - it just works!
