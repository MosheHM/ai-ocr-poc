# Client Scripts

Command-line scripts for interacting with the document processing system.

## Files

| Script | Description |
|--------|-------------|
| `send_task.py` | Upload PDF and send task to processing queue |
| `get_results.py` | Poll results queue and download processed files |

---

## send_task.py

Upload a PDF to Azure Storage and send a processing task to the queue.

### Usage (get_results.py)

```bash
uv run python send_task.py <pdf_path> [options]
```

### Arguments (get_results.py)

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `pdf_path` | ✅ | - | Path to PDF file to process |
| `--container` | ❌ | processing-input | Blob container for uploads |
| `--queue` | ❌ | processing-tasks | Queue name for tasks |
| `--correlation-key` | ❌ | Generated UUID | Custom correlation key |

### Examples (get_results.py)

```bash
# Basic usage (generates correlation key)
uv run python send_task.py "document.pdf"

# Custom correlation key
uv run python send_task.py "document.pdf" --correlation-key=task-2024-001

# Custom container
uv run python send_task.py "document.pdf" --container=my-uploads
```

### Output (get_results.py)

```text
============================================================
SENDING PROCESSING TASK
============================================================
Correlation Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890
PDF File: document.pdf
File Size: 2.45 MB
Container: processing-input
Queue: processing-tasks

Uploading PDF to Azure Storage...
PDF uploaded successfully

Sending task message to queue 'processing-tasks'...
Task message sent successfully!

============================================================
TASK SUBMITTED SUCCESSFULLY!
============================================================
Correlation Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890

Use this correlation key to retrieve results:
  python get_results.py --correlation-key=a1b2c3d4-e5f6-7890-abcd-ef1234567890
  uv run python get_results.py --correlation-key=a1b2c3d4-e5f6-7890-abcd-ef1234567890
============================================================
```

### What It Does (get_results.py)

1. Validates the PDF file (size, pages, format)
2. Validates/generates correlation key
3. Uploads PDF to blob storage: `{container}/{correlationKey}/{filename}`
4. Sends task message to queue with `correlationKey` and `pdfBlobUrl`

---

## get_results.py

Poll the results queue and optionally download processed files.

### Usage

```bash
uv run python get_results.py [options]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--correlation-key` | ❌ | - | Filter by specific task |
| `--queue` | ❌ | processing-tasks-results | Results queue name |
| `--download` | ❌ | - | Directory to download ZIP files |
| `--max-messages` | ❌ | 10 | Max messages to check |

### Examples

```bash
# Check all results
uv run python get_results.py

# Filter by correlation key
uv run python get_results.py --correlation-key=a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Download results
uv run python get_results.py --correlation-key=task-001 --download=./results

# Check more messages
uv run python get_results.py --max-messages=50
```

### Output

```
============================================================
CHECKING RESULTS QUEUE
============================================================
Queue: processing-tasks-results
Filtering by correlation key: a1b2c3d4...

============================================================
RESULT #1
============================================================
Correlation Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Status: success

Results ZIP URL: https://storage.blob.core.windows.net/...

Downloading to: ./results/a1b2c3d4-e5f6-7890-abcd-ef1234567890_results.zip
Download complete!

Message removed from queue

============================================================
Found 1 result(s)
============================================================
```

### What It Does

1. Connects to results queue
2. Receives messages (with visibility timeout)
3. Filters by correlation key (if provided)
4. Displays result status (success/failure)
5. Optionally downloads ZIP file
6. Deletes processed messages from queue

---

## Environment Variables

Both scripts require:

```bash
# .env file
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
AZURE_STORAGE_ACCESS_KEY=your_access_key
```

Scripts automatically load from `.env` file in the project directory.

---

## Message Flow

```text
send_task.py                          Azure                          get_results.py
     │                                  │                                  │
     │  1. Upload PDF                   │                                  │
     │─────────────────────────────────▶│ Blob Storage                     │
     │                                  │                                  │
     │  2. Send task message            │                                  │
     │─────────────────────────────────▶│ processing-tasks queue           │
     │                                  │                                  │
     │                                  │  3. Function processes           │
     │                                  │                                  │
     │                                  │  4. Result message               │
     │                                  │◀─────────────────────────────────│
     │                                  │ processing-tasks-results queue   │
     │                                  │                                  │
     │                                  │  5. Poll results                 │
     │                                  │─────────────────────────────────▶│
     │                                  │                                  │
     │                                  │  6. Download ZIP                 │
     │                                  │─────────────────────────────────▶│
  ```
