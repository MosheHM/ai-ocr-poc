# Architecture Guide

This document describes the system architecture, design decisions, and component interactions for the AI Document Processing System.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [Design Decisions](#design-decisions)
5. [Scalability Considerations](#scalability-considerations)

---

## System Architecture

### High-Level Architecture

```
                                    ┌──────────────────────────────────────┐
                                    │          Google Cloud                │
                                    │    ┌─────────────────────────┐       │
                                    │    │   Gemini 2.5 Flash      │       │
                                    │    │   AI Model              │       │
                                    │    └───────────▲─────────────┘       │
                                    │                │                     │
                                    └────────────────┼─────────────────────┘
                                                     │ API Call
                                                     │
┌────────────────────────────────────────────────────┼─────────────────────────────────────┐
│                              Microsoft Azure                                              │
│  ┌─────────────────────┐   ┌──────────────────────┴───────────────────────────────────┐  │
│  │   Azure Queues      │   │                 Azure Functions                          │  │
│  │                     │   │  ┌─────────────────────────────────────────────────────┐ │  │
│  │ ┌─────────────────┐ │   │  │              process_pdf_file                       │ │  │
│  │ │processing-tasks │─┼───┼─▶│                                                     │ │  │
│  │ │  (input queue)  │ │   │  │  1. Validate message                               │ │  │
│  │ └─────────────────┘ │   │  │  2. Download PDF from blob                         │ │  │
│  │                     │   │  │  3. Send to Gemini AI                               │ │  │
│  │ ┌─────────────────┐ │   │  │  4. Parse AI response                               │ │  │
│  │ │processing-tasks │◀┼───┼──│  5. Split PDF into documents                        │ │  │
│  │ │   -results      │ │   │  │  6. Create ZIP package                              │ │  │
│  │ │ (output queue)  │ │   │  │  7. Upload results                                  │ │  │
│  │ └─────────────────┘ │   │  │  8. Send result message                             │ │  │
│  └─────────────────────┘   │  └─────────────────────────────────────────────────────┘ │  │
│                            └──────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Azure Blob Storage                                         │ │
│  │  ┌─────────────────────────┐         ┌─────────────────────────────────────────────┐│ │
│  │  │    processing-input     │         │           processing-results                ││ │
│  │  │  (PDF upload container) │         │  (ZIP results container)                    ││ │
│  │  │                         │         │                                             ││ │
│  │  │  /{correlationKey}/     │         │  /{correlationKey}/                         ││ │
│  │  │      document.pdf       │         │      {correlationKey}_results.zip           ││ │
│  │  └─────────────────────────┘         └─────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Azure Function** | Serverless compute for document processing | Python 3.9+, Azure Functions v4 |
| **Input Queue** | Task message ingestion | Azure Queue Storage |
| **Output Queue** | Result message delivery | Azure Queue Storage |
| **Input Container** | PDF file storage | Azure Blob Storage |
| **Results Container** | Processed results storage | Azure Blob Storage |
| **AI Engine** | Document analysis and extraction | Google Gemini 2.5 Flash |

---

## Component Design

### Module Structure

```
prod-ocr/
├── function_app.py           # Azure Function entry point
├── send_task.py              # Client: send processing tasks
├── get_results.py            # Client: retrieve results
├── host.json                 # Azure Functions host config
├── local.settings.json       # Local dev settings
├── requirements.txt          # Python dependencies
│
└── modules/
    ├── __init__.py           # Package exports (DocumentSplitter)
    │
    ├── document_splitter/
    │   ├── __init__.py
    │   └── splitter.py       # DocumentSplitter class + UNIFIED_EXTRACTION_PROMPT
    │
    ├── azure/
    │   ├── __init__.py
    │   └── storage.py        # AzureStorageClient class
    │
    ├── validators/
    │   ├── __init__.py
    │   ├── errors.py         # Custom exceptions (ValidationError, ProcessingError, etc.)
    │   └── input_validator.py # Validation functions + ValidatedRequest class
    │
    └── utils/
        ├── __init__.py
        ├── pdf_utils.py      # PDF operations (extract_pdf_pages, combine_pdf_pages)
        └── zip_utils.py      # ZIP packaging (create_results_zip)
```

### Component Responsibilities

#### 1. Function App (`function_app.py`)

**Responsibilities:**
- Queue trigger handling
- Request validation and orchestration
- Error handling and logging
- Result message generation
- Resource lifecycle management

**Key Features:**
- Singleton pattern for clients (lazy initialization)
- Secure temporary directory creation
- Automatic cleanup on completion/failure
- Severity-based error handling

#### 2. Document Splitter (`modules/document_splitter/splitter.py`)

**Responsibilities:**
- AI model communication
- PDF content analysis
- Document boundary detection
- Data extraction and parsing
- PDF file splitting

**Key Features:**
- Single API call for entire PDF (efficiency)
- JSON response cleaning and parsing
- Configurable model and timeout
- Document count limiting

#### 3. Azure Storage Client (`modules/azure/storage.py`)

**Responsibilities:**
- Blob upload/download operations
- Retry logic with exponential backoff
- Error handling and logging

**Key Features:**
- 3 retry attempts with exponential backoff
- Sanitized logging (no sensitive data)
- Support for file and bytes upload

#### 4. Validators (`modules/validators/`)

**Responsibilities:**
- Input validation and sanitization
- Security enforcement
- Error message sanitization

**Key Features:**
- Correlation key whitelist validation
- Blob URL domain validation
- PDF size and page limits
- Path traversal prevention

---

## Data Flow

### Message Flow Sequence

```
┌────────┐    ┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
│ Client │    │  Blob   │    │   Queue   │    │ Function │    │ Gemini  │
└───┬────┘    └────┬────┘    └─────┬─────┘    └────┬─────┘    └────┬────┘
    │              │               │               │               │
    │ Upload PDF   │               │               │               │
    │─────────────▶│               │               │               │
    │              │               │               │               │
    │ Send Task    │               │               │               │
    │──────────────┼──────────────▶│               │               │
    │              │               │               │               │
    │              │               │  Trigger      │               │
    │              │               │──────────────▶│               │
    │              │               │               │               │
    │              │  Download PDF │               │               │
    │              │◀──────────────┼───────────────│               │
    │              │               │               │               │
    │              │               │               │  Analyze PDF  │
    │              │               │               │──────────────▶│
    │              │               │               │               │
    │              │               │               │  JSON Result  │
    │              │               │               │◀──────────────│
    │              │               │               │               │
    │              │  Upload ZIP   │               │               │
    │              │◀──────────────┼───────────────│               │
    │              │               │               │               │
    │              │               │  Result Msg   │               │
    │              │               │◀──────────────│               │
    │              │               │               │               │
    │ Poll Results │               │               │               │
    │──────────────┼──────────────▶│               │               │
    │              │               │               │               │
    │ Get Result   │               │               │               │
    │◀─────────────┼───────────────│               │               │
    │              │               │               │               │
```

### Processing Pipeline

```
Input PDF ─────────────────────────────────────────────────────▶ Results ZIP
    │                                                               ▲
    ▼                                                               │
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───┴───────────┐
│   Validate    │───▶│   Download    │───▶│   Process     │───▶│   Package     │
│   Request     │    │   PDF         │    │   with AI     │    │   Results     │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
  • Parse JSON         • Fetch from         • Send to           • Split PDFs
  • Validate key         blob storage         Gemini AI         • Create JSON
  • Validate URL       • Validate PDF       • Parse response    • Create ZIP
  • Security checks    • Save to temp       • Detect docs       • Upload ZIP
```

---

## Design Decisions

### 1. Single AI API Call Architecture

**Decision:** Process entire PDF in one Gemini API call instead of page-by-page.

**Rationale:**
- Better context for document boundary detection
- Reduced API latency and costs
- More accurate multi-page document handling
- Simpler error handling

**Trade-offs:**
- Larger payload per request
- Higher memory usage
- Potential timeout for very large documents

### 2. Queue-Based Async Processing

**Decision:** Use Azure Queue Storage for task management.

**Rationale:**
- Decouples client from processing
- Built-in retry with visibility timeout
- Automatic scaling based on queue depth
- Guaranteed message delivery

**Trade-offs:**
- Added complexity vs. synchronous API
- Message size limits (64KB)
- Eventually consistent results

### 3. Serverless Architecture

**Decision:** Azure Functions with Consumption plan.

**Rationale:**
- Automatic scaling to zero
- Pay-per-execution pricing
- Built-in queue trigger support
- Managed infrastructure

**Trade-offs:**
- Cold start latency
- 10-minute execution limit
- Limited local state

### 4. Correlation Key Pattern

**Decision:** Use correlation keys for request/response linking.

**Rationale:**
- Enables async result retrieval
- Supports idempotent operations
- Facilitates logging and debugging
- Works with queue-based flow

### 5. ZIP Packaging for Results

**Decision:** Package all outputs in a single ZIP file.

**Rationale:**
- Single download for all results
- Preserves file relationships
- Includes metadata JSON
- Efficient transfer

---

## Scalability Considerations

### Horizontal Scaling

| Component | Scaling Method | Limit |
|-----------|---------------|-------|
| Azure Function | Automatic (queue depth) | Consumption: 200 instances |
| Queue Storage | Built-in | 20K messages/sec |
| Blob Storage | Built-in | 60 Gbps egress |
| Gemini API | Rate limiting | Depends on tier |

### Bottlenecks and Mitigations

| Bottleneck | Impact | Mitigation |
|------------|--------|------------|
| Gemini API rate limits | Processing delays | Request queuing, backoff |
| PDF download time | Increased latency | Parallel processing |
| ZIP creation | Memory pressure | Streaming compression |
| Large PDFs | Timeout risk | Page limit (500), size limit (10GB) |

### Performance Tuning

```json
// host.json queue settings
{
  "extensions": {
    "queues": {
      "batchSize": 1,           // Process one at a time (AI-bound)
      "maxDequeueCount": 3,     // Retry 3 times
      "visibilityTimeout": "00:05:00",  // 5 min per attempt
      "maxPollingInterval": "00:00:02"  // Poll every 2 sec
    }
  },
  "functionTimeout": "00:10:00"  // 10 min max execution
}
```

### Recommended Configurations

| Scenario | Batch Size | Timeout | Max Instances |
|----------|------------|---------|---------------|
| Low volume | 1 | 10 min | 10 |
| High volume | 1 | 10 min | 50 |
| Large documents | 1 | 10 min | 20 |
| Mixed workload | 1 | 10 min | 30 |
