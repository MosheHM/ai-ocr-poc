# Setup development environment with Azurite (PowerShell)

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setting up Development Environment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host

# Check if Docker is available
$dockerAvailable = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
$azuriteAvailable = $null -ne (Get-Command azurite -ErrorAction SilentlyContinue)

if (-not $dockerAvailable -and -not $azuriteAvailable) {
    Write-Host "ERROR: Neither Azurite nor Docker is installed." -ForegroundColor Red
    Write-Host "Please install one of the following:"
    Write-Host "  - Docker: https://docs.docker.com/get-docker/"
    Write-Host "  - Azurite (npm): npm install -g azurite"
    exit 1
}

# Copy configuration files if they don't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ .env created" -ForegroundColor Green
    Write-Host "  Please edit .env and set your GEMINI_API_KEY"
} else {
    Write-Host "✓ .env already exists" -ForegroundColor Green
}

if (-not (Test-Path local.settings.json)) {
    Write-Host "Creating local.settings.json from template..." -ForegroundColor Yellow
    Copy-Item local.settings.json.example local.settings.json
    Write-Host "✓ local.settings.json created" -ForegroundColor Green
    Write-Host "  Please edit local.settings.json and set your GEMINI_API_KEY"
} else {
    Write-Host "✓ local.settings.json already exists" -ForegroundColor Green
}

Write-Host
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Starting Azurite..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host

# Start Azurite
if ($dockerAvailable) {
    Write-Host "Starting Azurite using Docker..." -ForegroundColor Yellow
    Write-Host "Container name: azurite-dev"
    Write-Host

    # Check if container already exists
    $containerExists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^azurite-dev$"

    if ($containerExists) {
        Write-Host "Azurite container already exists. Restarting..." -ForegroundColor Yellow
        docker restart azurite-dev | Out-Null
    } else {
        docker run -d `
            --name azurite-dev `
            -p 10000:10000 `
            -p 10001:10001 `
            -p 10002:10002 `
            mcr.microsoft.com/azure-storage/azurite | Out-Null
    }

    Write-Host "✓ Azurite started (Docker)" -ForegroundColor Green
} else {
    Write-Host "Starting Azurite using npm..." -ForegroundColor Yellow
    Write-Host "Running in background..."
    Start-Process -FilePath "npx" -ArgumentList "azurite" -WindowStyle Hidden
    Write-Host "✓ Azurite started" -ForegroundColor Green
}

Write-Host
Write-Host "Waiting for Azurite to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Create containers and queues
Write-Host
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Creating Storage Containers and Queues" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host

$connectionString = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=exam/bA==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"

# Check if az CLI is available
$azCliAvailable = $null -ne (Get-Command az -ErrorAction SilentlyContinue)

if (-not $azCliAvailable) {
    Write-Host "WARNING: Azure CLI (az) is not installed." -ForegroundColor Yellow
    Write-Host "Please install Azure CLI to automatically create containers and queues:"
    Write-Host "  https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    Write-Host
    Write-Host "Or use Azure Storage Explorer to manually create:"
    Write-Host "  Containers: ocr-processing-input, ocr-processing-result"
    Write-Host "  Queues: processing-tasks, processing-tasks-results"
} else {
    Write-Host "Creating blob containers..." -ForegroundColor Yellow

    try {
        az storage container create --name ocr-processing-input --connection-string $connectionString 2>&1 | Out-Null
    } catch {
        Write-Host "  (container may already exist)" -ForegroundColor Gray
    }

    try {
        az storage container create --name ocr-processing-result --connection-string $connectionString 2>&1 | Out-Null
    } catch {
        Write-Host "  (container may already exist)" -ForegroundColor Gray
    }

    Write-Host
    Write-Host "Creating queues..." -ForegroundColor Yellow

    try {
        az storage queue create --name processing-tasks --connection-string $connectionString 2>&1 | Out-Null
    } catch {
        Write-Host "  (queue may already exist)" -ForegroundColor Gray
    }

    try {
        az storage queue create --name processing-tasks-results --connection-string $connectionString 2>&1 | Out-Null
    } catch {
        Write-Host "  (queue may already exist)" -ForegroundColor Gray
    }

    Write-Host
    Write-Host "✓ Storage resources created" -ForegroundColor Green
}

Write-Host
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Development Environment Ready!" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host
Write-Host "Next steps:"
Write-Host "  1. Edit .env and set your GEMINI_API_KEY"
Write-Host "  2. Edit local.settings.json and set your GEMINI_API_KEY"
Write-Host "  3. Start the Azure Function:"
Write-Host "     func start"
Write-Host
Write-Host "Azurite Endpoints:" -ForegroundColor Yellow
Write-Host "  Blob: http://127.0.0.1:10000/devstoreaccount1"
Write-Host "  Queue: http://127.0.0.1:10001/devstoreaccount1"
Write-Host
Write-Host "To stop Azurite (Docker):" -ForegroundColor Yellow
Write-Host "  docker stop azurite-dev"
Write-Host
Write-Host "==================================================" -ForegroundColor Cyan
