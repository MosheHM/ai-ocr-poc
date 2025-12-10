# Queue Storage Configuration Guide

This guide explains how to configure a separate Azure Storage account for queue operations, independent from blob storage.

## Overview

The system supports using separate storage accounts for:

- **Blob Storage**: Stores PDF files and processing results (input/output files)
- **Queue Storage**: Manages task messages and result notifications

### Why Separate Storage Accounts?

Using separate storage accounts provides several benefits:

1. **Independent Scaling**: Scale blob and queue services independently based on load
2. **Cost Management**: Monitor and control costs separately for storage vs messaging
3. **Security Boundaries**: Apply different access policies to blobs vs queues
4. **Performance Isolation**: Queue operations don't impact blob storage performance
5. **Regional Flexibility**: Place queues closer to compute resources, blobs closer to users

## Configuration

### Default Behavior

By default, if queue storage variables are not specified, the system uses the same storage account for both blobs and queues.

### Development Environment

For development (Azurite), you typically use the same storage account:

```bash
# .env
ENVIRONMENT=development

# Blob storage (Azurite)
DEV_AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
DEV_AZURE_STORAGE_ACCESS_KEY=example/K1SZFPtwoNMlqhKBSwCD/bA==

# Queue storage defaults to same account if not specified
# Uncomment to use a separate account (e.g., separate Azurite instance)
# DEV_QUEUE_STORAGE_ACCOUNT_NAME=devstoreaccount1
# DEV_QUEUE_STORAGE_ACCESS_KEY=example/K1SZFPtwoNMlqhKBSwCD/bA==
```

### Production Environment with Separate Queue Storage

To use a separate queue storage account in production:

```bash
# .env
ENVIRONMENT=production

# Blob storage account
PROD_AZURE_STORAGE_ACCOUNT_NAME=yourprodblobs
PROD_AZURE_STORAGE_ACCESS_KEY=blob-storage-key
PROD_INPUT_CONTAINER=input-files
PROD_RESULTS_CONTAINER=processing-results

# Queue storage account (separate)
PROD_QUEUE_STORAGE_ACCOUNT_NAME=yourprodqueues
PROD_QUEUE_STORAGE_ACCESS_KEY=queue-storage-key
PROD_TASKS_QUEUE=tasks
PROD_RESULTS_QUEUE=tasks-results
```

### Azure Functions Configuration

Update `local.settings.json` for local development:

```json
{
  "Values": {
    "ENVIRONMENT": "production",

    "AZURE_STORAGE_ACCOUNT_NAME": "yourprodblobs",
    "AZURE_STORAGE_ACCESS_KEY": "blob-storage-key",
    "INPUT_CONTAINER": "input-files",
    "RESULTS_CONTAINER": "processing-results",

    "QUEUE_STORAGE_ACCOUNT_NAME": "yourprodqueues",
    "QUEUE_STORAGE_ACCESS_KEY": "queue-storage-key",
    "TASKS_QUEUE": "-tasks",
    "RESULTS_QUEUE": "-results"
  }
}
```

For deployed Azure Functions, configure these in Application Settings in the Azure Portal.

## Setting Up Separate Queue Storage

### Step 1: Create Queue Storage Account

```bash
# Create a dedicated storage account for queues
az storage account create \
  --name yourprodqueues \
  --resource-group your-resource-group \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Get the account key
az storage account keys list \
  --account-name yourprodqueues \
  --query '[0].value' -o tsv
```

### Step 2: Create Queues

```bash
# Get connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --name yourprodqueues \
  --query connectionString -o tsv)

# Create queues
az storage queue create \
  --name processing-tasks \
  --connection-string "$CONNECTION_STRING"

az storage queue create \
  --name processing-tasks-results \
  --connection-string "$CONNECTION_STRING"
```

### Step 3: Configure Application

Update your `.env` or `local.settings.json` with the queue storage credentials (see examples above).

### Step 4: Verify Configuration

Run the send_task script to verify both storage accounts are being used:

```bash
python send_task.py path/to/test.pdf
```

You should see output like:
```
Using blob storage: yourprodblobs
Using queue storage: yourprodqueues
```

## Environment Variables Reference

### Queue Storage Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QUEUE_STORAGE_ACCOUNT_NAME` | Queue storage account name | Same as blob storage |
| `QUEUE_STORAGE_ACCESS_KEY` | Queue storage access key | Same as blob storage |
| `QUEUE_STORAGE_CONNECTION_STRING` | Full connection string (optional) | Generated from account/key |
| `TASKS_QUEUE` | Name of tasks queue | `-tasks` |
| `RESULTS_QUEUE` | Name of results queue | `-results` |

### Environment-Specific Variables

For development (`ENVIRONMENT=development`):
- `DEV_QUEUE_STORAGE_ACCOUNT_NAME`
- `DEV_QUEUE_STORAGE_ACCESS_KEY`
- `DEV_QUEUE_STORAGE_CONNECTION_STRING`
- `DEV_TASKS_QUEUE`
- `DEV_RESULTS_QUEUE`

For production (`ENVIRONMENT=production`):
- `PROD_QUEUE_STORAGE_ACCOUNT_NAME`
- `PROD_QUEUE_STORAGE_ACCESS_KEY`
- `PROD_QUEUE_STORAGE_CONNECTION_STRING`
- `PROD_TASKS_QUEUE`
- `PROD_RESULTS_QUEUE`

## Use Cases

### Use Case 1: High Queue Throughput

If your queue operations are very frequent, separate them to avoid throttling blob operations:

```bash
# Production: High-throughput queue storage
PROD_AZURE_STORAGE_ACCOUNT_NAME=yourprodblobs
PROD_QUEUE_STORAGE_ACCOUNT_NAME=yourprodqueues  # Separate account

# Configure queue storage with Premium performance tier
az storage account create \
  --name yourprodqueues \
  --sku Premium_LRS \
  --kind BlockBlobStorage
```

### Use Case 2: Multi-Region Deployment

Place queues in the same region as your compute resources for lower latency:

```bash
# Blob storage in US East (near users)
PROD_AZURE_STORAGE_ACCOUNT_NAME=yourblobs-eastus

# Queue storage in US West (near Azure Functions)
PROD_QUEUE_STORAGE_ACCOUNT_NAME=yourqueues-westus
```

### Use Case 3: Cost Optimization

Use different storage tiers for blobs and queues:

```bash
# Premium blob storage for fast file access
az storage account create \
  --name yourprodblobs \
  --sku Premium_LRS

# Standard queue storage (cheaper, sufficient for messages)
az storage account create \
  --name yourprodqueues \
  --sku Standard_LRS
```

### Use Case 4: Security and Compliance

Apply different access policies:

```bash
# Blob storage: Restricted access, lifecycle policies, immutable storage
# Queue storage: More permissive for application, separate audit logs

# Configure different network rules
az storage account update \
  --name yourprodblobs \
  --default-action Deny \
  --bypass AzureServices

az storage account update \
  --name yourprodqueues \
  --default-action Allow
```

## Monitoring and Troubleshooting

### Check Storage Account in Use

The scripts will log which storage accounts they're using:

```bash
# send_task.py output
Using blob storage: yourprodblobs
Using queue storage: yourprodqueues

# Function logs
Application configured for production environment:
  blob_storage=yourprodblobs,
  queue_storage=yourprodqueues,
  model=gemini-2.5-flash
```

### Common Issues

**Issue: "Queue not found" error**

Solution: Ensure queues exist in the queue storage account:
```bash
az storage queue list \
  --account-name yourprodqueues
```

**Issue: "Authentication failed" for queue operations**

Solution: Verify queue storage credentials:
```bash
# Test queue access
az storage queue exists \
  --name processing-tasks \
  --account-name yourprodqueues \
  --account-key <your-key>
```

**Issue: Queue operations work but blob operations fail**

Solution: This confirms separate accounts are working. Check blob storage credentials separately.

## Performance Considerations

### Queue Storage Limits

- **Standard**: 2,000 messages/second per queue
- **Premium**: 100,000 messages/second per queue

### When to Use Separate Accounts

Use separate queue storage when:
- Processing >1,000 messages/minute
- Blob operations are experiencing throttling
- You need different SLAs for messaging vs storage
- Compliance requires isolation of message data
- You want granular cost tracking

### When to Use Same Account

Use same account when:
- Processing <100 messages/minute
- Simplicity is more important than optimization
- Development/testing environments
- Cost optimization is primary concern
- You're not experiencing throttling

## Best Practices

1. **Start with same account**: Use one storage account initially, separate later if needed
2. **Monitor metrics**: Track queue and blob operations to identify bottlenecks
3. **Use managed identities**: Avoid access keys in production when possible
4. **Set up alerts**: Configure Azure Monitor alerts for queue depth and throttling
5. **Document configuration**: Keep track of which accounts are used in each environment
6. **Test failover**: Verify behavior when queue storage is unavailable
7. **Implement retry logic**: Handle transient failures gracefully

## Migration

### Migrating from Single to Separate Storage

1. Create new queue storage account
2. Create queues in new account
3. Update configuration with new queue credentials
4. Deploy updated configuration
5. Verify queue operations use new account
6. Monitor for issues
7. Clean up old queues after validation

No data migration needed - queues are ephemeral message stores.

## Additional Resources

- [Azure Queue Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/queues/)
- [Storage Account Overview](https://docs.microsoft.com/en-us/azure/storage/common/storage-account-overview)
- [Performance and Scalability Checklist](https://docs.microsoft.com/en-us/azure/storage/common/storage-performance-checklist)
