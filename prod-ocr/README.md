# Prod OCR Runner

This folder contains a self-contained version of the document splitting workflow so it can be deployed or shared independently of the rest of the repository.

## Structure

- `function_app.py` – Azure Function with queue trigger for processing tasks
- `send_task.py` – Client script for sending tasks to Azure Queue
- `get_results.py` – Client script for retrieving results from Azure Queue
- `modules/` – Core modules including document splitter and Azure storage helpers
- `modules/config.py` – Environment-based configuration management
- `requirements.txt` – Runtime dependencies (exported from uv for Azure Functions tooling)
- `host.json` / `local.settings.json` – Azure Functions configuration
- `.env` – **Not committed**. Copy `.env.example` and configure credentials

## Environment Configuration

The system supports separate development and production environments:

- **Development**: Uses Azurite (local Azure Storage emulator) for zero-cost local testing
- **Production**: Uses real Azure Storage accounts in the cloud

### Queue Storage Support

The system supports using **separate storage accounts** for queue operations (task messages) and blob storage (files). This provides:

- Independent scaling and performance optimization
- Granular cost tracking and management
- Better security boundaries
- Regional flexibility for optimal latency

By default, both services use the same storage account. Configure `QUEUE_STORAGE_*` variables to use a separate account.

For detailed setup instructions, see:
- [Environment Setup Guide](docs/ENVIRONMENT_SETUP.md)
- [Queue Storage Setup Guide](docs/QUEUE_STORAGE_SETUP.md)

### Quick Setup

**Development (Local)**:
```bash
# Copy configuration templates
cp .env.example .env
cp local.settings.json.example local.settings.json

# Edit .env and set GEMINI_API_KEY
# Development storage is pre-configured for Azurite

# Start Azurite (in separate terminal)
docker run -p 10000:10000 -p 10001:10001 mcr.microsoft.com/azure-storage/azurite
```

**Production**:
```bash
# Copy production template
cp local.settings.json.production.example local.settings.json.production

# Edit .env and set:
# - ENVIRONMENT=production
# - PROD_AZURE_STORAGE_ACCOUNT_NAME
# - PROD_AZURE_STORAGE_ACCESS_KEY
# - GEMINI_API_KEY
```

## Usage

### Local Mode (Direct Processing)

Process PDFs directly using Python code:

```python
from modules.document_splitter import split_and_extract_documents

# Split a PDF into separate documents
result = split_and_extract_documents(
    pdf_path="path/to/file.pdf",
    output_dir="split_output"
)

print(f"Found {result['total_documents']} documents")
for doc in result['documents']:
    print(f"  {doc['DOC_TYPE']}: {doc['FILE_PATH']}")
```

Make sure to set `GEMINI_API_KEY` in your `.env` file first.

### Queue Mode (Azure Functions)

This mode enables serverless processing using Azure Functions with queue triggers.

#### Setup

1. Install Azure Functions Core Tools:
```bash
npm install -g azure-functions-core-tools@4
```

2. Configure environment:
```bash
# Edit local.settings.json and set:
# - AzureWebJobsStorage (connection string)
# - GEMINI_API_KEY
```

3. Create Azure resources:
   - Storage Account with two queues: `processing-tasks` and `processing-tasks-results`
   - Two blob containers: `processing-input` and `processing-results`

#### Running Locally

Test the Azure Function locally:

```bash
# Install dependencies
uv sync --extra dev

# Start the function
uv run func start
```

The function will automatically trigger when messages are added to `processing-tasks` queue.

> Keep `requirements.txt` in sync for Azure Functions tooling by running:
> `uv export --format requirements-txt --no-hashes --output requirements.txt`

#### Deploying to Azure

```bash
# Create Function App in Azure
az functionapp create --resource-group <group> --name <app-name> --runtime python --functions-version 4

# Deploy
func azure functionapp publish <app-name>

# Configure app settings
az functionapp config appsettings set --name <app-name> --resource-group <group> --settings "GEMINI_API_KEY=your_key"
```

#### Sending Tasks (Client)

Use the example client to send processing tasks:

```bash
# Upload PDF and send task message
uv run python send_task.py "path/to/document.pdf"

# Custom container and correlation key
uv run python send_task.py "document.pdf" --container=my-input --correlation-key=custom-id-123
```

#### Message Flow

1. **Client**: Uploads PDF to `processing-input` blob container
2. **Client**: Sends task message to `processing-tasks` queue
3. **Azure Function**: Automatically triggered by queue message
4. **Azure Function**: Downloads PDF, processes it, creates ZIP
5. **Azure Function**: Uploads ZIP to `processing-results` container
6. **Azure Function**: Sends result message to `processing-tasks-results` queue

#### Message Structures

**Task Message** (sent to `processing-tasks`):

```json
{
  "correlationKey": "unique-id",
  "pdfBlobUrl": "https://storage.blob.core.windows.net/..."
}
```

**Result Message** (sent to `processing-tasks-results`):

Success:

```json
{
  "correlationKey": "unique-id",
  "status": "success",
  "resultsBlobUrl": "https://storage.blob.core.windows.net/..."
}
```

Failure:

```json
{
  "correlationKey": "unique-id",
  "status": "failure",
  "errorMessage": "Error details..."
}
```
