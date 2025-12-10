# Environment Setup Guide

This guide explains how to set up separate development and production environments for the AI Document Processing System.

## Overview

The system supports two distinct environments:

- **Development**: Uses local Azurite emulator for Azure Storage
- **Production**: Uses real Azure Storage accounts in the cloud

## Quick Start

### Development Environment (Local)

1. **Start Azurite** (Azure Storage Emulator):
   ```bash
   # Using Docker
   docker run -p 10000:10000 -p 10001:10001 mcr.microsoft.com/azure-storage/azurite

   # Or using npm/npx
   npx azurite
   ```

2. **Copy configuration templates**:
   ```bash
   cp .env.example .env
   cp local.settings.json.example local.settings.json
   ```

3. **Edit `.env` file**:
   ```bash
   ENVIRONMENT=development
   GEMINI_API_KEY=your-gemini-api-key-here

   # Development settings are pre-configured for Azurite
   # No need to change DEV_AZURE_STORAGE_* values
   ```

4. **Create blob containers** (one-time setup):
   ```bash
   # Install Azure CLI or use Azure Storage Explorer
   az storage container create --name dev-input-files \
     --connection-string "UseDevelopmentStorage=true"

   az storage container create --name dev-processing-results \
     --connection-string "UseDevelopmentStorage=true"

   az storage queue create --name processing-tasks \
     --connection-string "UseDevelopmentStorage=true"

   az storage queue create --name processing-tasks-results \
     --connection-string "UseDevelopmentStorage=true"
   ```

5. **Run Azure Functions locally**:
   ```bash
   func start
   ```

### Production Environment (Azure Cloud)

1. **Create Azure Storage Account**:
   ```bash
   # Using Azure CLI
   az storage account create \
     --name yourprodstorageaccount \
     --resource-group your-resource-group \
     --location eastus \
     --sku Standard_LRS
   ```

2. **Get storage credentials**:
   ```bash
   # Get account key
   az storage account keys list \
     --account-name yourprodstorageaccount \
     --query '[0].value' -o tsv
   ```

3. **Copy production configuration template**:
   ```bash
   cp local.settings.json.production.example local.settings.json.production
   ```

4. **Edit production configuration**:
   - Update `local.settings.json.production` with your Azure Storage credentials
   - Update `.env` with production values

5. **Create production containers**:
   ```bash
   az storage container create --name input-files \
     --account-name yourprodstorageaccount

   az storage container create --name processing-results \
     --account-name yourprodstorageaccount

   az storage queue create --name processing-tasks \
     --account-name yourprodstorageaccount

   az storage queue create --name processing-tasks-results \
     --account-name yourprodstorageaccount
   ```

## Queue Storage Configuration

The system supports using a separate Azure Storage account for queue operations (task messages), independent from blob storage (files). This provides:

- **Independent scaling** of messaging and file storage
- **Cost management** and tracking per service
- **Security boundaries** between storage types
- **Performance isolation**

By default, the system uses the same storage account for both blobs and queues. To use a separate queue storage account, configure the `QUEUE_STORAGE_*` variables.

See [Queue Storage Setup Guide](QUEUE_STORAGE_SETUP.md) for detailed configuration instructions.

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Current environment (`development` or `production`) | `development` |
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_TIMEOUT_SECONDS` | API timeout in seconds | `300` |

### Development Environment

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV_AZURE_STORAGE_ACCOUNT_NAME` | Azurite account name | `devstoreaccount1` |
| `DEV_AZURE_STORAGE_ACCESS_KEY` | Azurite access key | *Pre-configured* |
| `DEV_AZURE_STORAGE_CONNECTION_STRING` | Azurite connection string | *Pre-configured* |
| `DEV_INPUT_CONTAINER` | Input files container | `dev-input-files` |
| `DEV_RESULTS_CONTAINER` | Results container | `dev-processing-results` |

### Production Environment

| Variable | Description | Default |
|----------|-------------|---------|
| `PROD_AZURE_STORAGE_ACCOUNT_NAME` | Azure Storage account name | *Required* |
| `PROD_AZURE_STORAGE_ACCESS_KEY` | Azure Storage access key | *Required* |
| `PROD_AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string | *Optional* |
| `PROD_INPUT_CONTAINER` | Input files container | `input-files` |
| `PROD_RESULTS_CONTAINER` | Results container | `processing-results` |

### Queue Storage (Optional - Separate Account)

For development:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEV_QUEUE_STORAGE_ACCOUNT_NAME` | Queue storage account name | Same as blob storage |
| `DEV_QUEUE_STORAGE_ACCESS_KEY` | Queue storage access key | Same as blob storage |
| `DEV_TASKS_QUEUE` | Tasks queue name | `tasks` |
| `DEV_RESULTS_QUEUE` | Results queue name | `results` |

For production:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROD_QUEUE_STORAGE_ACCOUNT_NAME` | Queue storage account name | Same as blob storage |
| `PROD_QUEUE_STORAGE_ACCESS_KEY` | Queue storage access key | Same as blob storage |
| `PROD_TASKS_QUEUE` | Tasks queue name | `tasks` |
| `PROD_RESULTS_QUEUE` | Results queue name | `results` |

Generic (applies if environment-specific not set):

| Variable | Description |
|----------|-------------|
| `QUEUE_STORAGE_ACCOUNT_NAME` | Queue storage account name |
| `QUEUE_STORAGE_ACCESS_KEY` | Queue storage access key |
| `TASKS_QUEUE` | Tasks queue name |
| `RESULTS_QUEUE` | Results queue name |

### Backward Compatibility

The system also supports non-prefixed variables for backward compatibility:

- `AZURE_STORAGE_ACCOUNT_NAME`
- `AZURE_STORAGE_ACCESS_KEY`
- `INPUT_CONTAINER`
- `RESULTS_CONTAINER`

These will be used as fallback values if environment-specific variables are not set.

## Configuration Files

### `.env` File

The `.env` file is used for:
- Local Python scripts (`send_task.py`, `get_results.py`)
- Environment variable loading via `python-dotenv`

Example development `.env`:
```bash
ENVIRONMENT=development
GEMINI_API_KEY=your-api-key-here

# Development uses Azurite (pre-configured)
DEV_INPUT_CONTAINER=dev-input-files
DEV_RESULTS_CONTAINER=dev--results
```

Example production `.env`:
```bash
ENVIRONMENT=production
GEMINI_API_KEY=your-api-key-here

PROD_AZURE_STORAGE_ACCOUNT_NAME=yourprodaccount
PROD_AZURE_STORAGE_ACCESS_KEY=your-access-key-here
PROD_INPUT_CONTAINER=input-files
PROD_RESULTS_CONTAINER=-results
```

### `local.settings.json` File

The `local.settings.json` file is used by Azure Functions Core Tools for local development.

Development configuration (`local.settings.json`):
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ENVIRONMENT": "development",
    "GEMINI_API_KEY": "your-api-key-here",
    "AZURE_STORAGE_ACCOUNT_NAME": "devstoreaccount1",
    "AZURE_STORAGE_ACCESS_KEY": "example/K1SZFPtwoNMlqhKBSwCD/bA==",
    "INPUT_CONTAINER": "dev-input-files",
    "RESULTS_CONTAINER": "dev--results"
  }
}
```

Production configuration (`local.settings.json.production`):
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT;...",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ENVIRONMENT": "production",
    "GEMINI_API_KEY": "your-api-key-here",
    "AZURE_STORAGE_ACCOUNT_NAME": "yourprodaccount",
    "AZURE_STORAGE_ACCESS_KEY": "your-access-key-here",
    "INPUT_CONTAINER": "input-files",
    "RESULTS_CONTAINER": "-results"
  }
}
```

## Switching Between Environments

### Method 1: Change ENVIRONMENT variable

Simply update the `ENVIRONMENT` variable in your `.env` or `local.settings.json`:

```bash
# .env or local.settings.json
ENVIRONMENT=development  # or production
```

The system will automatically load the appropriate configuration.

### Method 2: Use different configuration files

Maintain separate configuration files and swap them:

```bash
# Switch to production
cp local.settings.json.production local.settings.json

# Switch to development
cp local.settings.json.example local.settings.json
```

## Azure Functions Deployment

When deploying to Azure Functions, configure environment variables in the Azure Portal:

1. Navigate to your Function App
2. Go to **Configuration** → **Application settings**
3. Add the following settings:

```
ENVIRONMENT=production
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=300

AZURE_STORAGE_ACCOUNT_NAME=yourprodaccount
AZURE_STORAGE_ACCESS_KEY=your-access-key-here

INPUT_CONTAINER=input-files
RESULTS_CONTAINER=processing-results
```

**Note**: `AzureWebJobsStorage` is automatically configured by Azure Functions.

## Troubleshooting

### Issue: "Storage account not found" in development

**Solution**: Make sure Azurite is running:
```bash
docker ps | grep azurite
# or
npx azurite --version
```

### Issue: "Container does not exist"

**Solution**: Create the required containers:
```bash
# Development
az storage container create --name dev-input-files \
  --connection-string "UseDevelopmentStorage=true"

# Production
az storage container create --name input-files \
  --account-name yourprodaccount
```

### Issue: "Invalid credentials" in production

**Solution**: Verify your storage credentials:
```bash
az storage account keys list --account-name yourprodaccount
```

### Issue: Environment not switching

**Solution**: Restart the Azure Functions runtime or Python process to reload environment variables.

## Best Practices

1. **Never commit credentials**: Keep `.env` and `local.settings.json` in `.gitignore`

2. **Use separate storage accounts**: Use distinct Azure Storage accounts for dev/test/prod

3. **Container naming**: Use clear prefixes (`dev-`, `test-`, `prod-`) for containers

4. **Access control**: Use different access keys or SAS tokens per environment

5. **Monitoring**: Enable Azure Monitor for production environments

6. **Cost management**: Use Azurite for development to avoid Azure costs

7. **Testing**: Always test in development before deploying to production

## Additional Resources

- [Azurite Documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)
- [Azure Functions Local Development](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-local)
- [Azure Storage Security](https://learn.microsoft.com/en-us/azure/storage/common/storage-security-guide)
