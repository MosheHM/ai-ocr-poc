# Deployment Guide

This guide covers setup, configuration, and deployment of the AI Document Processing System.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Azure Resource Setup](#azure-resource-setup)
4. [Configuration](#configuration)
5. [Deployment to Azure](#deployment-to-azure)
6. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Runtime environment |
| Azure Functions Core Tools | 4.x | Local development and deployment |
| Azure CLI | 2.x | Azure resource management |
| uv | Latest | Python dependency management |

### Required Accounts

- **Azure Subscription** - For hosting Azure Functions and Storage
- **Google Cloud Account** - For Gemini AI API access

### Installation Commands

```bash
# Python (download from python.org or use pyenv)
python --version  # Should be 3.9 or higher

# Azure Functions Core Tools
npm install -g azure-functions-core-tools@4

# Azure CLI
# Windows: winget install -e --id Microsoft.AzureCLI
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify installations
func --version
az --version
```

---

## Local Development Setup

### 1. Clone and Setup

```bash
# Navigate to project directory
cd prod-ocr

# Install dependencies (creates .venv automatically)
uv sync --extra dev

# Optional: activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2. Configure Environment

Create a `.env` file for local mode:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_STORAGE_ACCESS_KEY=your_storage_access_key
```

Update `local.settings.json` for Azure Functions mode:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=<name>;AccountKey=<key>;EndpointSuffix=core.windows.net",
    "AZURE_STORAGE_ACCOUNT_NAME": "<storage_account_name>",
    "AZURE_STORAGE_ACCESS_KEY": "<storage_access_key>",
    "GEMINI_API_KEY": "<your_gemini_api_key>",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_TIMEOUT_SECONDS": "300",
    "RESULTS_CONTAINER": "processing-results"
  }
}
```

### 3. Run Locally

```bash
# Azure Functions mode (with local storage emulator)
func start

# Or use Python API directly
python -c "from modules.document_splitter import DocumentSplitter; print('Ready')"
```

---

## Azure Resource Setup

### 1. Create Resource Group

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "<subscription-id>"

# Create resource group
az group create \
  --name rg-document-processing \
  --location westeurope
```

### 2. Create Storage Account

```bash
# Create storage account
az storage account create \
  --name stdocprocessing \
  --resource-group rg-document-processing \
  --location westeurope \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string
az storage account show-connection-string \
  --name stdocprocessing \
  --resource-group rg-document-processing \
  --output tsv
```

### 3. Create Queues

```bash
# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --account-name stdocprocessing \
  --resource-group rg-document-processing \
  --query '[0].value' -o tsv)

# Create input queue
az storage queue create \
  --name processing-tasks \
  --account-name stdocprocessing \
  --account-key $STORAGE_KEY

# Create output queue
az storage queue create \
  --name processing-tasks-results \
  --account-name stdocprocessing \
  --account-key $STORAGE_KEY
```

### 4. Create Blob Containers

```bash
# Create input container
az storage container create \
  --name processing-input \
  --account-name stdocprocessing \
  --account-key $STORAGE_KEY

# Create results container
az storage container create \
  --name processing-results \
  --account-name stdocprocessing \
  --account-key $STORAGE_KEY
```

### 5. Create Function App

```bash
# Create Function App
az functionapp create \
  --name func-document-processing \
  --resource-group rg-document-processing \
  --storage-account stdocprocessing \
  --consumption-plan-location westeurope \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `AZURE_STORAGE_ACCOUNT_NAME` | ✅ | Azure Storage account name |
| `AZURE_STORAGE_ACCESS_KEY` | ✅ | Azure Storage access key |
| `AzureWebJobsStorage` | ✅ | Full connection string (Functions runtime) |
| `GEMINI_MODEL` | ❌ | Model name (default: gemini-2.5-flash) |
| `GEMINI_TIMEOUT_SECONDS` | ❌ | API timeout (default: 300) |
| `RESULTS_CONTAINER` | ❌ | Results container (default: processing-results) |

### Configure App Settings in Azure

```bash
# Set Gemini API key
az functionapp config appsettings set \
  --name func-document-processing \
  --resource-group rg-document-processing \
  --settings "GEMINI_API_KEY=<your_api_key>"

# Set storage credentials
az functionapp config appsettings set \
  --name func-document-processing \
  --resource-group rg-document-processing \
  --settings \
    "AZURE_STORAGE_ACCOUNT_NAME=stdocprocessing" \
    "AZURE_STORAGE_ACCESS_KEY=<your_access_key>"

# Set optional settings
az functionapp config appsettings set \
  --name func-document-processing \
  --resource-group rg-document-processing \
  --settings \
    "GEMINI_MODEL=gemini-2.5-flash" \
    "GEMINI_TIMEOUT_SECONDS=300" \
    "RESULTS_CONTAINER=processing-results"
```

### Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Click "Get API Key"
4. Create new key or use existing
5. Copy the API key

---

## Deployment to Azure

### Method 1: Azure Functions Core Tools

```bash
# Deploy from project directory
cd prod-ocr

# Publish to Azure
func azure functionapp publish func-document-processing
```

### Method 2: VS Code Extension

1. Install "Azure Functions" extension
2. Sign in to Azure
3. Right-click on project folder
4. Select "Deploy to Function App..."
5. Choose function app

### Method 3: GitHub Actions (CI/CD)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Azure Function

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install uv
      run: python -m pip install uv

    - name: Install dependencies
      working-directory: prod-ocr
      run: uv sync --frozen

    - name: Export requirements for Azure Functions packaging
      working-directory: prod-ocr
      run: uv export --format requirements-txt --no-hashes --output requirements.txt
    
    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: func-document-processing
        package: prod-ocr
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

---

## Post-Deployment Verification

### 1. Check Function Status

```bash
# List functions
az functionapp function list \
  --name func-document-processing \
  --resource-group rg-document-processing

# Check app status
az functionapp show \
  --name func-document-processing \
  --resource-group rg-document-processing \
  --query "state"
```

### 2. View Logs

```bash
# Stream live logs
func azure functionapp logstream func-document-processing

# Or via Azure CLI
az functionapp log tail \
  --name func-document-processing \
  --resource-group rg-document-processing
```

### 3. Test End-to-End

```bash
# Configure .env with Azure credentials
cd prod-ocr

# Send a test task
uv run python send_task.py "test_document.pdf"

# Wait for processing (check logs)

# Retrieve results
uv run python get_results.py --correlation-key=<key_from_send_task>
```

### 4. Monitor in Azure Portal

1. Go to Azure Portal
2. Navigate to Function App
3. Click "Monitor" in left menu
4. View invocations, errors, and performance

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Function not triggering | Queue connection | Verify `AzureWebJobsStorage` setting |
| Gemini API errors | Invalid key | Check `GEMINI_API_KEY` setting |
| Timeout errors | Large PDF | Increase `GEMINI_TIMEOUT_SECONDS` |
| Blob not found | Wrong container | Verify `ALLOWED_INPUT_CONTAINERS` |
| Permission denied | Storage access | Check storage access key |

### Useful Commands

```bash
# View all app settings
az functionapp config appsettings list \
  --name func-document-processing \
  --resource-group rg-document-processing

# Restart function app
az functionapp restart \
  --name func-document-processing \
  --resource-group rg-document-processing

# Check queue message count
az storage queue show \
  --name processing-tasks \
  --account-name stdocprocessing \
  --query "approximateMessageCount"
```

---

## Security Checklist

- [ ] API keys stored in Azure Key Vault (production)
- [ ] Storage account uses private endpoints
- [ ] Function App uses managed identity
- [ ] HTTPS enforced for all connections
- [ ] Minimum necessary permissions configured
- [ ] Logging does not expose sensitive data
- [ ] Input validation enabled
