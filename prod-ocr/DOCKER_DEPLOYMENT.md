# Docker Deployment Guide for DevOps

## Overview
This document provides instructions for building, running, and deploying the prod-ocr Azure Functions Docker image.

## Prerequisites
- Docker 20.10+ installed
- Access to Azure Container Registry (ACR) or Docker Hub

## Build the Docker Image

```bash
# Build the image
docker build -t prod-ocr:latest .

# Build with a specific tag
docker build -t prod-ocr:v1.0.0 .
```

## Run Locally

### Required Environment Variables
Create a `.env` file or pass these variables:

```env
GEMINI_API_KEY=your-gemini-api-key
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCESS_KEY=your-access-key
AzureWebJobsStorage=your-connection-string
```

### Run the Container

```bash
# Run with environment file
docker run -d \
  --name prod-ocr \
  -p 80:80 \
  --env-file .env \
  prod-ocr:latest

# Run with individual environment variables
docker run -d \
  --name prod-ocr \
  -p 80:80 \
  -e GEMINI_API_KEY=your-key \
  -e AZURE_STORAGE_ACCOUNT_NAME=your-account \
  -e AZURE_STORAGE_ACCESS_KEY=your-key \
  -e AzureWebJobsStorage="your-connection-string" \
  prod-ocr:latest
```

## Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name <your-acr-name>

# Tag the image
docker tag prod-ocr:latest <your-acr-name>.azurecr.io/prod-ocr:latest
docker tag prod-ocr:latest <your-acr-name>.azurecr.io/prod-ocr:v1.0.0

# Push to ACR
docker push <your-acr-name>.azurecr.io/prod-ocr:latest
docker push <your-acr-name>.azurecr.io/prod-ocr:v1.0.0
```

## Deploy to Azure Functions (Container)

### Using Azure CLI

```bash
# Create a Function App with container deployment
az functionapp create \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --storage-account <storage-account> \
  --plan <app-service-plan> \
  --deployment-container-image-name <your-acr-name>.azurecr.io/prod-ocr:latest

# Configure app settings
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings \
    GEMINI_API_KEY=your-key \
    AZURE_STORAGE_ACCOUNT_NAME=your-account \
    AZURE_STORAGE_ACCESS_KEY=your-key
```

## Docker Compose (Development)

Use `docker-compose.yml` for local development with Azurite:

```bash
docker-compose up -d
```

## Health Check

The container includes a health check endpoint:
```bash
curl http://localhost:80/api/health
```

## Troubleshooting

### View Logs
```bash
docker logs prod-ocr
docker logs -f prod-ocr  # Follow logs
```

### Enter Container Shell
```bash
docker exec -it prod-ocr /bin/bash
```

### Check Container Status
```bash
docker ps -a
docker inspect prod-ocr
```

## Image Details
- **Base Image**: `mcr.microsoft.com/azure-functions/python:4-python3.12`
- **Package Manager**: uv (fast Python package installer)
- **Python Version**: 3.12
- **Exposed Port**: 80
