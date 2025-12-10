# Environment Setup Summary

## What Was Created

A complete separate development and production blob storage environment configuration system.

### New Files Created

1. **Configuration Module** (`modules/config.py`)
   - Environment-aware configuration management
   - Automatic environment detection
   - Support for dev/prod environments
   - Backward compatibility with existing configurations

2. **Configuration Templates**
   - `.env.example` - Updated with dev/prod environment variables
   - `local.settings.json.example` - Development Azure Functions config
   - `local.settings.json.production.example` - Production Azure Functions config

3. **Documentation**
   - `docs/ENVIRONMENT_SETUP.md` - Comprehensive environment setup guide
   - `README.md` - Updated with environment configuration section

4. **Setup Scripts**
   - `setup_dev_environment.sh` - Bash script for Linux/Mac
   - `setup_dev_environment.ps1` - PowerShell script for Windows

### Modified Files

1. **`function_app.py`**
   - Uses new `get_app_config()` for environment-aware configuration
   - Automatic environment detection
   - Logs current environment on startup

2. **`send_task.py`**
   - Uses `get_storage_config()` for environment-aware storage
   - Displays current storage account being used

3. **`get_results.py`**
   - Uses `get_storage_config()` for environment-aware storage
   - Displays current storage account being used

4. **`modules/__init__.py`**
   - Exports config module functions and types

## How It Works

### Environment Variables

The system uses an `ENVIRONMENT` variable to switch between configurations:

```bash
ENVIRONMENT=development  # Uses DEV_* variables and Azurite
ENVIRONMENT=production   # Uses PROD_* variables and Azure Cloud
```

### Configuration Hierarchy

1. Environment-specific variables (e.g., `DEV_AZURE_STORAGE_ACCOUNT_NAME`, `PROD_QUEUE_STORAGE_ACCOUNT_NAME`)
2. Generic variables (e.g., `AZURE_STORAGE_ACCOUNT_NAME`, `QUEUE_STORAGE_ACCOUNT_NAME`)
3. Default values (e.g., `devstoreaccount1` for development)

### Queue Storage Support

The system now supports **separate storage accounts** for queue operations:

- **Blob Storage**: Stores PDF files and processing results
- **Queue Storage**: Manages task messages (can be same or different account)

**Benefits of Separate Queue Storage:**
- Independent scaling and performance
- Granular cost tracking
- Better security boundaries
- Regional flexibility

**Default Behavior:** If queue storage variables are not specified, the system uses the same storage account for both blobs and queues.

See [Queue Storage Setup Guide](docs/QUEUE_STORAGE_SETUP.md) for detailed configuration.

### Development Environment

- **Storage**: Azurite (local emulator)
- **Account**: `devstoreaccount1` (pre-configured)
- **Containers**: `dev-input-files`, `dev-processing-results`
- **Cost**: Free (local only)

### Production Environment

- **Storage**: Azure Cloud Storage Account
- **Account**: Your Azure Storage account
- **Containers**: `input-files`, `processing-results`
- **Cost**: Pay-per-use (Azure pricing)

## Quick Start

### Option 1: Automatic Setup (Recommended)

**Linux/Mac**:
```bash
cd prod-ocr
./setup_dev_environment.sh
```

**Windows**:
```powershell
cd prod-ocr
.\setup_dev_environment.ps1
```

### Option 2: Manual Setup

1. **Copy configuration files**:
   ```bash
   cp .env.example .env
   cp local.settings.json.example local.settings.json
   ```

2. **Edit `.env`** and set:
   ```bash
   ENVIRONMENT=development
   GEMINI_API_KEY=your-api-key-here
   ```

3. **Start Azurite**:
   ```bash
   docker run -p 10000:10000 -p 10001:10001 mcr.microsoft.com/azure-storage/azurite
   ```

4. **Create containers** (if Azure CLI is installed):
   ```bash
   CONNECTION_STRING="UseDevelopmentStorage=true"
   az storage container create --name dev-input-files --connection-string "$CONNECTION_STRING"
   az storage container create --name dev-processing-results --connection-string "$CONNECTION_STRING"
   az storage queue create --name processing-tasks --connection-string "$CONNECTION_STRING"
   az storage queue create --name processing-tasks-results --connection-string "$CONNECTION_STRING"
   ```

5. **Start the function**:
   ```bash
   func start
   ```

## Switching Environments

### Method 1: Change ENVIRONMENT Variable

Simply update `.env` or `local.settings.json`:

```bash
# Development
ENVIRONMENT=development

# Production
ENVIRONMENT=production
```

### Method 2: Use Different Config Files

```bash
# Use development config
cp local.settings.json.example local.settings.json

# Use production config
cp local.settings.json.production.example local.settings.json
```

## Testing the Setup

### Test Development Environment

```bash
# Send a test task
uv run python send_task.py "path/to/test.pdf"

# Check for results
uv run python get_results.py --correlation-key=<key-from-above>
```

### Verify Environment

The scripts will display which storage account they're using:

```
Using devstoreaccount1 storage account  # Development
Using yourprodaccount storage account   # Production
```

## Configuration Reference

### Development Variables

```bash
ENVIRONMENT=development
DEV_AZURE_STORAGE_ACCOUNT_NAME=devstoreaccount1
DEV_AZURE_STORAGE_ACCESS_KEY=<azurite-default-key>
DEV_INPUT_CONTAINER=dev-input-files
DEV_RESULTS_CONTAINER=dev-processing-results
```

### Production Variables

```bash
ENVIRONMENT=production
PROD_AZURE_STORAGE_ACCOUNT_NAME=your-prod-account
PROD_AZURE_STORAGE_ACCESS_KEY=your-prod-key
PROD_INPUT_CONTAINER=input-files
PROD_RESULTS_CONTAINER=processing-results
```

### Queue Storage Variables (Optional)

To use a separate storage account for queues:

**Development:**
```bash
DEV_QUEUE_STORAGE_ACCOUNT_NAME=devstoreaccount1
DEV_QUEUE_STORAGE_ACCESS_KEY=<key>
DEV_TASKS_QUEUE=-tasks
DEV_RESULTS_QUEUE=-tasks-results
```

**Production:**
```bash
PROD_QUEUE_STORAGE_ACCOUNT_NAME=your-queue-account
PROD_QUEUE_STORAGE_ACCESS_KEY=your-queue-key
PROD_TASKS_QUEUE=-tasks
PROD_RESULTS_QUEUE=-results
```

**Generic (if environment-specific not set):**
```bash
QUEUE_STORAGE_ACCOUNT_NAME=your-queue-account
QUEUE_STORAGE_ACCESS_KEY=your-queue-key
TASKS_QUEUE=-tasks
RESULTS_QUEUE=-results
```

## Benefits

1. **Zero-cost development** - Use Azurite locally instead of Azure Cloud
2. **Environment isolation** - Dev and prod data never mix
3. **Easy switching** - Change environments with one variable
4. **Backward compatible** - Old configurations still work
5. **Type-safe** - Configuration module provides type hints
6. **Clear logging** - Logs show which environment is active

## Troubleshooting

See the [full Environment Setup Guide](docs/ENVIRONMENT_SETUP.md) for detailed troubleshooting.

### Common Issues

1. **"Storage account not found"**
   - Make sure Azurite is running: `docker ps | grep azurite`

2. **"Container does not exist"**
   - Run the setup script or manually create containers

3. **"Invalid credentials"**
   - Verify your Azure Storage credentials in production

4. **Environment not switching**
   - Restart the Azure Functions runtime to reload env vars

## Next Steps

1. Read the [full Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)
2. Test the development environment with a sample PDF
3. Set up production environment when ready to deploy
4. Configure CI/CD pipelines with environment-specific variables

## Support

For issues or questions:
1. Check the [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)
2. Review Azure Functions logs: `func start --verbose`
3. Check Azurite logs: `docker logs azurite-dev`
