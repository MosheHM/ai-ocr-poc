# Documentation Index

Welcome to the AI Document Processing System documentation.

## Documentation Structure

```
docs/
├── README.md                 # This file - documentation index
├── PROJECT_OVERVIEW.md       # System overview and capabilities
├── API_REFERENCE.md          # Complete API documentation
├── ARCHITECTURE.md           # System design and data flow
├── DEPLOYMENT.md             # Setup and deployment guide
├── DEVELOPMENT.md            # Development workflow
│
├── function_app.md           # Main Azure Function documentation
│
├── scripts/
│   └── README.md             # Client scripts (send_task, get_results)
│
└── modules/
    ├── README.md             # Modules overview
    ├── document_splitter/
    │   └── README.md         # DocumentSplitter class docs
    ├── azure/
    │   └── README.md         # AzureStorageClient docs
    ├── validators/
    │   └── README.md         # Validation & error classes
    └── utils/
        └── README.md         # PDF & ZIP utilities
```

## Quick Links

### High-Level Documentation

| Document | Description |
|----------|-------------|
| [Project Overview](./PROJECT_OVERVIEW.md) | System capabilities, architecture diagrams |
| [Architecture Guide](./ARCHITECTURE.md) | System design, component details, data flow |
| [Deployment Guide](./DEPLOYMENT.md) | Setup, configuration, deployment |
| [Development Guide](./DEVELOPMENT.md) | Dev workflow, code standards, debugging |

### Code Documentation (mirrors project structure)

| Path | Description |
|------|-------------|
| [function_app.md](./function_app.md) | Azure Function entry point |
| [scripts/](./scripts/) | Client scripts (send_task, get_results) |
| [modules/](./modules/) | Core modules index |
| [modules/document_splitter/](./modules/document_splitter/) | AI document processing |
| [modules/azure/](./modules/azure/) | Azure Storage client |
| [modules/validators/](./modules/validators/) | Input validation & errors |
| [modules/utils/](./modules/utils/) | PDF & ZIP utilities |

## Getting Started

### For Users

1. Read the [Project Overview](./PROJECT_OVERVIEW.md) to understand system capabilities
2. Follow the [Deployment Guide](./DEPLOYMENT.md) to set up the system
3. Use the [scripts documentation](./scripts/) to send tasks and get results

### For Developers

1. Start with [Development Guide](./DEVELOPMENT.md) for environment setup
2. Study the [Architecture Guide](./ARCHITECTURE.md) for system design
3. Browse [modules/](./modules/) for code-level documentation

## Quick Reference

### Send a Processing Task
```bash
python send_task.py "document.pdf"
```

### Retrieve Results
```bash
python get_results.py --correlation-key=<key>
```

### Run Azure Function Locally
```bash
func start
```

### Deploy to Azure
```bash
func azure functionapp publish <app-name>
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `AZURE_STORAGE_ACCOUNT_NAME` | ✅ | Azure Storage account name |
| `AZURE_STORAGE_ACCESS_KEY` | ✅ | Azure Storage access key |

## Support

For issues and questions:
- Review the [Deployment Guide](./DEPLOYMENT.md#troubleshooting) troubleshooting section
- Check the [Development Guide](./DEVELOPMENT.md#debugging) debugging section
