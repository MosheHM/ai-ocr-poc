# AI Document Processing System - Project Overview

## Executive Summary

The **AI Document Processing System** is an enterprise-grade solution for automated document extraction and classification. Built on Azure Functions and Google Gemini AI, it processes multi-document PDFs, automatically detects document boundaries, classifies document types, extracts structured data, and splits documents into separate files.

---

## Key Capabilities

| Feature | Description |
|---------|-------------|
| **AI-Powered Analysis** | Uses Google Gemini 2.5 Flash for intelligent document understanding |
| **Multi-Document Detection** | Automatically identifies boundaries between merged documents |
| **Document Classification** | Classifies into Invoice, OBL, HAWB, or Packing List types |
| **Structured Data Extraction** | Extracts type-specific fields with confidence scoring |
| **PDF Splitting** | Generates separate PDF files for each detected document |
| **Serverless Architecture** | Azure Functions for automatic scaling and cost optimization |
| **Queue-Based Processing** | Asynchronous task handling with Azure Queue Storage |

---

## Supported Document Types

### 1. Invoice
- Invoice number, date (16-digit format), currency, INCOTERMS
- Invoice amount, customer ID

### 2. OBL (Ocean Bill of Lading)
- Customer name, weight, volume, INCOTERMS

### 3. HAWB (House Air Waybill)
- Customer name, currency, carrier, HAWB number, pieces, weight

### 4. Packing List
- Customer name, pieces count, total weight

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI Document Processing System                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │   Client    │───▶│  Azure Blob     │    │     Azure Functions         │  │
│  │  Scripts    │    │  Storage        │    │  ┌─────────────────────┐   │  │
│  │             │    │  ┌───────────┐  │    │  │  Queue Trigger      │   │  │
│  │ send_task   │    │  │processing │  │    │  │  process_pdf_file   │   │  │
│  │ get_results │    │  │  -input   │  │───▶│  └─────────┬───────────┘   │  │
│  └─────────────┘    │  └───────────┘  │    │            │               │  │
│                     │  ┌───────────┐  │    │            ▼               │  │
│                     │  │processing │  │◀───│  ┌─────────────────────┐   │  │
│                     │  │ -results  │  │    │  │ DocumentSplitter    │   │  │
│                     │  └───────────┘  │    │  │ (Gemini AI)         │   │  │
│                     └─────────────────┘    │  └─────────────────────┘   │  │
│                                            └─────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Azure Queue Storage                             │  │
│  │  ┌─────────────────────┐         ┌─────────────────────────────────┐  │  │
│  │  │  processing-tasks   │────────▶│  processing-tasks-results       │  │  │
│  │  │  (Input Queue)      │         │  (Output Queue)                 │  │  │
│  │  └─────────────────────┘         └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Processing Workflow

```
1. Client uploads PDF      ──▶  Azure Blob Storage (processing-input)
           │
           ▼
2. Task message sent       ──▶  Azure Queue (processing-tasks)
           │
           ▼
3. Azure Function triggered ──▶  Downloads PDF from blob
           │
           ▼
4. Gemini AI Analysis      ──▶  Document detection & classification
           │
           ▼
5. PDF Splitting           ──▶  Individual PDFs + JSON results
           │
           ▼
6. Results packaging       ──▶  ZIP file created
           │
           ▼
7. Upload results          ──▶  Azure Blob Storage (processing-results)
           │
           ▼
8. Result message sent     ──▶  Azure Queue (processing-tasks-results)
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Runtime** | Python 3.9+ |
| **AI Model** | Google Gemini 2.5 Flash |
| **Serverless Platform** | Azure Functions v4 |
| **Storage** | Azure Blob Storage |
| **Messaging** | Azure Queue Storage |
| **PDF Processing** | pypdf library |

---

## Deployment Options

### 1. Local Mode (Development)

Direct processing using Python API.

```python
from modules.document_splitter import DocumentSplitter

splitter = DocumentSplitter(api_key="your_key")
result = splitter.split_and_save("document.pdf", "output/")
```

### 2. Azure Functions Mode (Production)
Serverless queue-based processing with automatic scaling.

```bash
# Local testing
func start

# Azure deployment
func azure functionapp publish <app-name>
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Max PDF Size** | 10 GB |
| **Max Pages** | 500 pages |
| **Max Output Documents** | 100 per PDF |
| **Function Timeout** | 10 minutes |
| **Retry Attempts** | 3 (with exponential backoff) |
| **API Timeout** | 300 seconds (Gemini) |

---

## Security Features

- ✅ HTTPS-only blob URLs
- ✅ Input validation with strict whitelisting
- ✅ Path traversal prevention
- ✅ Sensitive data sanitization in logs
- ✅ Secure temporary directory handling
- ✅ Container allowlist enforcement

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Detailed API documentation
- [Architecture Guide](./ARCHITECTURE.md) - System design details
- [Deployment Guide](./DEPLOYMENT.md) - Setup and deployment instructions
- [Development Guide](./DEVELOPMENT.md) - Contributing and development setup
