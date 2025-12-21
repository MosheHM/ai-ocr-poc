# Environment Setup Guide

This guide explains how to set up separate development and production environments for the AI Document Processing System.

## Overview

The system supports two distinct environments with **environment-specific configuration files**:

- **Development**: Uses local Azurite emulator for Azure Storage (`.env.development`)
- **Production**: Uses real Azure Storage accounts in the cloud (`.env.production`)

## New Configuration Approach

The system now uses environment-specific files instead of prefixed variables:

- **`.env.development`** - Development configuration (Azurite)
- **`.env.production`** - Production configuration (Azure Cloud)
- **`ENVIRONMENT`** variable - Determines which file to load

### Key Benefits

✅ Cleaner variable names (no `DEV_` or `PROD_` prefixes)
✅ Easy environment switching (change one variable)
✅ Better organization (separate files per environment)
✅ Standard industry practice

## Quick Start

### Development Environment (Local)

1. **Start Azurite** (Azure Storage Emulator):
   ```bash
   # Using Docker
   docker run -p 10000:10000 -p 10001:10001 mcr.microsoft.com/azure-storage/azurite

   # Or using npm/npx
   npx azurite
   ```

2. **Create environment configuration**:
   ```bash
   # Copy the development template
   cp .env.development .env.development.local

   # Or create a minimal .env file to set environment
   echo "ENVIRONMENT=development" > .env
   ```

3. **Edit `.env.development`** (or `.env.development.local`):
   ```bash
   # Gemini AI Configuration
   GEMINI_API_KEY=your-gemini-api-key-here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_TIMEOUT_SECONDS=300

   # Azure Blob Storage (Azurite - already configured)
   AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
   AZURE_STORAGE_ACCESS_KEY=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPtwoNMlqhKBSwCD/bA==

   # Containers
   INPUT_CONTAINER=dev-input-files
   RESULTS_CONTAINER=dev-processing-results

   # Queue Names
   TASKS_QUEUE=processing-tasks
   RESULTS_QUEUE=processing-tasks-results
   ```

4. **Create blob containers** (one-time setup):
   ```bash
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

3. **Create production configuration**:
   ```bash
   # Copy the production template
   cp .env.production .env.production.local

   # Create .env file to specify production environment
   echo "ENVIRONMENT=production" > .env
   ```

4. **Edit `.env.production`** (or `.env.production.local`):
   ```bash
   # Gemini AI Configuration
   GEMINI_API_KEY=your-production-gemini-api-key
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_TIMEOUT_SECONDS=300

   # Azure Blob Storage (Production)
   AZURE_STORAGE_ACCOUNT_NAME=yourprodstorageaccount
   AZURE_STORAGE_ACCESS_KEY=your-storage-access-key
   AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=yourprodstorageaccount;AccountKey=your-storage-key;EndpointSuffix=core.windows.net

   # Containers
   INPUT_CONTAINER=input-files
   RESULTS_CONTAINER=processing-results

   # Queue Names
   TASKS_QUEUE=processing-tasks
   RESULTS_QUEUE=processing-tasks-results
   ```

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

By default, the system uses the same storage account for both blobs and queues. To use a separate queue storage account, configure the `QUEUE_STORAGE_*` variables in your environment file.

See [Queue Storage Setup Guide](QUEUE_STORAGE_SETUP.md) for detailed configuration instructions.

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Current environment (`development` or `production`) | `development` |
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_TIMEOUT_SECONDS` | API timeout in seconds | `300` |

### Storage Configuration (All Environments)

These variables are defined in `.env.development` or `.env.production`:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure Storage account name | Yes |
| `AZURE_STORAGE_ACCESS_KEY` | Azure Storage access key | Yes |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage connection string | Optional |
| `INPUT_CONTAINER` | Input files container | Yes |
| `RESULTS_CONTAINER` | Results container | Yes |

### Queue Storage (Optional - Separate Account)

If using a separate storage account for queues:

| Variable | Description | Default |
|----------|-------------|---------|
| `QUEUE_STORAGE_ACCOUNT_NAME` | Queue storage account name | Same as blob storage |
| `QUEUE_STORAGE_ACCESS_KEY` | Queue storage access key | Same as blob storage |
| `QUEUE_STORAGE_CONNECTION_STRING` | Queue storage connection string | Same as blob storage |
| `TASKS_QUEUE` | Tasks queue name | *Required* |
| `RESULTS_QUEUE` | Results queue name | *Required* |

## Configuration Files

### Environment-Specific Files (NEW)

- **`.env.development`** - Development configuration (checked into git as template)
- **`.env.production`** - Production configuration (checked into git as template)
- **`.env.development.local`** - Your local development overrides (not in git)
- **`.env.production.local`** - Your local production overrides (not in git)
- **`.env`** - Sets `ENVIRONMENT` variable (not in git)

### `.env` File (Environment Selector)

The `.env` file is used to select which environment to load:

```bash
# For development
ENVIRONMENT=development

# For production
ENVIRONMENT=production
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
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_TIMEOUT_SECONDS": "300",

    "AZURE_STORAGE_ACCOUNT_NAME": "devstoreaccount1",
    "AZURE_STORAGE_ACCESS_KEY": "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPtwoNMlqhKBSwCD/bA==",

    "INPUT_CONTAINER": "dev-input-files",
    "RESULTS_CONTAINER": "dev-processing-results",

    "TASKS_QUEUE": "processing-tasks",
    "RESULTS_QUEUE": "processing-tasks-results"
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

    "GEMINI_API_KEY": "your-production-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_TIMEOUT_SECONDS": "300",

    "AZURE_STORAGE_ACCOUNT_NAME": "yourprodaccount",
    "AZURE_STORAGE_ACCESS_KEY": "your-access-key-here",

    "INPUT_CONTAINER": "input-files",
    "RESULTS_CONTAINER": "processing-results",

    "TASKS_QUEUE": "processing-tasks",
    "RESULTS_QUEUE": "processing-tasks-results"
  }
}
```

## Switching Between Environments

### Method 1: Change ENVIRONMENT variable (Recommended)

Simply update the `ENVIRONMENT` variable in your `.env` file:

```bash
# .env file
ENVIRONMENT=development  # or production
```

The system will automatically load the corresponding `.env.{environment}` file.

### Method 2: Use different configuration files

Maintain separate configuration files and swap them:

```bash
# Switch to production
cp local.settings.json.production local.settings.json

# Switch to development
cp local.settings.json.example local.settings.json
```

### Method 3: Set environment variable directly

```bash
# Linux/Mac
export ENVIRONMENT=production
python your_script.py

# Windows PowerShell
$env:ENVIRONMENT="production"
python your_script.py

# Windows CMD
set ENVIRONMENT=production
python your_script.py
```

## How It Works

When the `modules.config` module is imported:

1. It loads the base `.env` file (if exists) to get the `ENVIRONMENT` variable
2. Determines the environment (defaults to `development` if not set)
3. Loads the environment-specific file `.env.{environment}`
4. All configuration functions (`get_storage_config()`, etc.) use the loaded variables

This happens automatically - you don't need to manually load the files.

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

TASKS_QUEUE=processing-tasks
RESULTS_QUEUE=processing-tasks-results
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

**Solution**:
1. Check that the `ENVIRONMENT` variable is set correctly
2. Verify the corresponding `.env.{environment}` file exists
3. Restart the Azure Functions runtime or Python process to reload environment variables

### Issue: Configuration not loading

**Solution**:
1. Ensure `python-dotenv` is installed: `pip install python-dotenv`
2. Check that `.env.{environment}` file exists and is readable
3. Verify the file paths are correct
4. Check the logs for any warnings about missing files

## Best Practices

1. **Never commit credentials**: Keep `.env`, `.env.*.local`, and `local.settings.json` in `.gitignore`

2. **Use `.local` suffix for personal overrides**:
   - `.env.development.local` overrides `.env.development`
   - Keeps your personal settings separate from team defaults

3. **Use separate storage accounts**: Use distinct Azure Storage accounts for dev/test/prod

4. **Container naming**: Use clear prefixes (`dev-`, `test-`, `prod-`) for containers

5. **Access control**: Use different access keys or SAS tokens per environment

6. **Monitoring**: Enable Azure Monitor for production environments

7. **Cost management**: Use Azurite for development to avoid Azure costs

8. **Testing**: Always test in development before deploying to production

9. **Environment-specific files**: Check in template files (`.env.development`, `.env.production`) but not actual credentials

## Migration from Old Approach

If you're migrating from the old prefix-based approach (`DEV_*`, `PROD_*` variables):

1. **Backup your current `.env` file**:
   ```bash
   cp .env .env.backup
   ```

2. **Create environment-specific files**:
   ```bash
   # Extract development config
   grep "^DEV_" .env.backup | sed 's/^DEV_//' > .env.development

   # Extract production config
   grep "^PROD_" .env.backup | sed 's/^PROD_//' > .env.production

   # Add shared config to both files
   grep "^GEMINI_" .env.backup >> .env.development
   grep "^GEMINI_" .env.backup >> .env.production
   ```

3. **Create simple .env file**:
   ```bash
   echo "ENVIRONMENT=development" > .env
   ```

4. **Test the new configuration**:
   ```bash
   python -c "from modules.config import get_app_config; print(get_app_config())"
   ```

5. **Remove old backup once verified**:
   ```bash
   rm .env.backup
   ```

## Additional Resources

- [Azurite Documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)
- [Azure Functions Local Development](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-local)
- [Azure Storage Security](https://learn.microsoft.com/en-us/azure/storage/common/storage-security-guide)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
