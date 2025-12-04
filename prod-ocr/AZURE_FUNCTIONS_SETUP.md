# Azure Functions Setup Guide

Quick setup guide for deploying the document processing system as an Azure Function.

## Prerequisites

- Azure subscription
- Azure CLI installed
- Azure Functions Core Tools v4
- Python 3.9 or later
- Google Gemini API key

## Local Development Setup

### 1. Install Azure Functions Core Tools

```bash
npm install -g azure-functions-core-tools@4
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Local Settings

Edit `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=<storage-account>;AccountKey=<key>;EndpointSuffix=core.windows.net",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "RESULTS_CONTAINER": "processing-results",
    "AZURE_STORAGE_ACCOUNT_NAME": "<storage-account>",
    "AZURE_STORAGE_ACCESS_KEY": "<key>"
  }
}
```

Note: `AzureWebJobsStorage` is still required for the Azure Functions runtime. The `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCESS_KEY` are used by the application code.

### 4. Run Locally

```bash
func start
```

The function will:
- Listen to `processing-tasks` queue
- Process messages automatically when they arrive
- Send results to `processing-tasks-results` queue

### 5. Test with Client Scripts

In another terminal:

```bash
# Send a task
python send_task.py "path/to/document.pdf"

# Check results
python get_results.py --correlation-key=<key-from-previous-command>
```

## Azure Deployment

### 1. Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="ocr-processing-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="ocrprocessingstorage"
FUNCTION_APP="ocr-processor-func"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Get connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

# Create queues
az storage queue create --name processing-tasks --connection-string "$STORAGE_CONNECTION"
az storage queue create --name processing-tasks-results --connection-string "$STORAGE_CONNECTION"

# Create blob containers
az storage container create --name processing-input --connection-string "$STORAGE_CONNECTION"
az storage container create --name processing-results --connection-string "$STORAGE_CONNECTION"

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --os-type Linux \
  --consumption-plan-location $LOCATION
```

### 2. Configure Function App Settings

```bash
# Set Gemini API key
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "GEMINI_API_KEY=your-gemini-api-key"

# Set model (optional, defaults to gemini-2.5-flash)
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "GEMINI_MODEL=gemini-2.5-flash"

# Set results container (optional, defaults to processing-results)
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "RESULTS_CONTAINER=processing-results"

# Set Azure Storage credentials for application code
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT"

# Get storage access key
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "AZURE_STORAGE_ACCESS_KEY=$STORAGE_KEY"
```

### 3. Deploy Function

```bash
func azure functionapp publish $FUNCTION_APP
```

### 4. Monitor Function

```bash
# View logs
func azure functionapp logstream $FUNCTION_APP

# Or in Azure Portal:
# Function App → Functions → process_pdf_file → Monitor
```

## Client Configuration for Production

Update your client scripts to use the production storage credentials:

```bash
# In .env file
AZURE_STORAGE_ACCOUNT_NAME="<storage-account-name>"
AZURE_STORAGE_ACCESS_KEY="<storage-access-key>"
```

Then use the client scripts as normal:

```bash
python send_task.py "document.pdf"
python get_results.py --correlation-key=<key>
```

## Message Format

### Input Message (processing-tasks queue)

```json
{
  "correlationKey": "unique-identifier",
  "pdfBlobUrl": "https://ocrprocessingstorage.blob.core.windows.net/processing-input/file.pdf"
}
```

### Output Message (processing-tasks-results queue)

Success:
```json
{
  "correlationKey": "unique-identifier",
  "status": "success",
  "resultsBlobUrl": "https://ocrprocessingstorage.blob.core.windows.net/processing-results/results.zip"
}
```

Failure:
```json
{
  "correlationKey": "unique-identifier",
  "status": "failure",
  "errorMessage": "Error description"
}
```

## Scaling Configuration

### Consumption Plan (Default)
- Automatic scaling based on queue length
- Cost-effective for variable workloads
- Cold start ~5-10 seconds

### Premium Plan (For Higher Performance)
```bash
az functionapp plan create \
  --resource-group $RESOURCE_GROUP \
  --name ocr-premium-plan \
  --location $LOCATION \
  --sku EP1 \
  --is-linux

# Update function to use premium plan
az functionapp update \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --plan ocr-premium-plan
```

Benefits:
- No cold starts
- Faster execution
- VNet integration available

## Monitoring and Troubleshooting

### Application Insights

Enable Application Insights for detailed monitoring:

```bash
az monitor app-insights component create \
  --app ocr-processor-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app ocr-processor-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY"
```

### View Logs

```bash
# Stream logs in real-time
az webapp log tail --name $FUNCTION_APP --resource-group $RESOURCE_GROUP

# Or use Function Core Tools
func azure functionapp logstream $FUNCTION_APP
```

### Common Issues

**Function not triggering:**
- Check queue exists: `az storage queue list --connection-string "$STORAGE_CONNECTION"`
- Verify AzureWebJobsStorage setting
- Check Application Insights for errors

**Processing failures:**
- Check GEMINI_API_KEY is set correctly
- Verify blob container permissions
- Review function logs for specific errors

**Timeout issues:**
- Increase function timeout in host.json:
  ```json
  {
    "functionTimeout": "00:10:00"
  }
  ```

## Cost Optimization

- Use Consumption plan for variable workloads
- Set appropriate queue batch size in host.json
- Enable Application Insights sampling to reduce logging costs
- Consider Azure Storage lifecycle policies for old blobs

## Security Best Practices

1. **Store secrets in Azure Key Vault:**
```bash
az keyvault create --name ocr-keyvault --resource-group $RESOURCE_GROUP --location $LOCATION
az keyvault secret set --vault-name ocr-keyvault --name gemini-api-key --value "your-key"

# Reference in Function App
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "GEMINI_API_KEY=@Microsoft.KeyVault(SecretUri=https://ocr-keyvault.vault.azure.net/secrets/gemini-api-key/)"
```

2. **Enable Managed Identity for blob access**
3. **Use private endpoints for storage account**
4. **Enable Azure Defender for Storage**
