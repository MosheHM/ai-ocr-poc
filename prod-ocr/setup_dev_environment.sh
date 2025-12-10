#!/bin/bash
# Setup development environment with Azurite

set -e

echo "=================================================="
echo "Setting up Development Environment"
echo "=================================================="
echo

# Check if Azurite is available
if ! command -v azurite &> /dev/null && ! command -v docker &> /dev/null; then
    echo "ERROR: Neither Azurite nor Docker is installed."
    echo "Please install one of the following:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Azurite (npm): npm install -g azurite"
    exit 1
fi

# Copy configuration files if they don't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env created"
    echo "  Please edit .env and set your GEMINI_API_KEY"
else
    echo "✓ .env already exists"
fi

if [ ! -f local.settings.json ]; then
    echo "Creating local.settings.json from template..."
    cp local.settings.json.example local.settings.json
    echo "✓ local.settings.json created"
    echo "  Please edit local.settings.json and set your GEMINI_API_KEY"
else
    echo "✓ local.settings.json already exists"
fi

echo
echo "=================================================="
echo "Starting Azurite..."
echo "=================================================="
echo

# Start Azurite
if command -v docker &> /dev/null; then
    echo "Starting Azurite using Docker..."
    echo "Container name: azurite-dev"
    echo

    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q '^azurite-dev$'; then
        echo "Azurite container already exists. Restarting..."
        docker restart azurite-dev
    else
        docker run -d \
            --name azurite-dev \
            -p 10000:10000 \
            -p 10001:10001 \
            -p 10002:10002 \
            mcr.microsoft.com/azure-storage/azurite
    fi

    echo "✓ Azurite started (Docker)"
else
    echo "Starting Azurite using npm..."
    echo "Running in background..."
    npx azurite &
    AZURITE_PID=$!
    echo "✓ Azurite started (PID: $AZURITE_PID)"
    echo "  To stop: kill $AZURITE_PID"
fi

echo
echo "Waiting for Azurite to be ready..."
sleep 3

# Create containers and queues
echo
echo "=================================================="
echo "Creating Storage Containers and Queues"
echo "=================================================="
echo

CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=exam/K1SZFPtwoNMlqhKBSwCD/bA==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"

# Check if az CLI is available
if ! command -v az &> /dev/null; then
    echo "WARNING: Azure CLI (az) is not installed."
    echo "Please install Azure CLI to automatically create containers and queues:"
    echo "  https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    echo
    echo "Or use Azure Storage Explorer to manually create:"
    echo "  Containers: dev-input-files, dev-processing-results"
    echo "  Queues: processing-tasks, processing-tasks-results"
else
    echo "Creating blob containers..."
    az storage container create --name dev-input-files \
        --connection-string "$CONNECTION_STRING" || echo "  (container may already exist)"

    az storage container create --name dev-processing-results \
        --connection-string "$CONNECTION_STRING" || echo "  (container may already exist)"

    echo
    echo "Creating queues..."
    az storage queue create --name processing-tasks \
        --connection-string "$CONNECTION_STRING" || echo "  (queue may already exist)"

    az storage queue create --name processing-tasks-results \
        --connection-string "$CONNECTION_STRING" || echo "  (queue may already exist)"

    echo
    echo "✓ Storage resources created"
fi

echo
echo "=================================================="
echo "Development Environment Ready!"
echo "=================================================="
echo
echo "Next steps:"
echo "  1. Edit .env and set your GEMINI_API_KEY"
echo "  2. Edit local.settings.json and set your GEMINI_API_KEY"
echo "  3. Start the Azure Function:"
echo "     func start"
echo
echo "Azurite Endpoints:"
echo "  Blob: http://127.0.0.1:10000/devstoreaccount1"
echo "  Queue: http://127.0.0.1:10001/devstoreaccount1"
echo
echo "To stop Azurite (Docker):"
echo "  docker stop azurite-dev"
echo
echo "=================================================="
