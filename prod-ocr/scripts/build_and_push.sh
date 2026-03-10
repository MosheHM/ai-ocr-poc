#!/bin/bash

set -euo pipefail

# Default variables
IMAGE_NAME="prod-ocr"
DOCKER_USERNAME="cramital.azurecr.io"
ACR_NAME="cramital"

# Optional env vars for constrained tenants/subscriptions
#   AZURE_TENANT_ID=<tenant-guid>
#   AZURE_SUBSCRIPTION_ID=<subscription-guid-or-name>
AZURE_TENANT_ID="${AZURE_TENANT_ID:-}"
AZURE_SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"

ensure_azure_login() {
    local login_args=(--use-device-code)

    if [ -n "$AZURE_TENANT_ID" ]; then
        login_args+=(--tenant "$AZURE_TENANT_ID")
    fi

    # Force a token refresh check to catch expired/invalid refresh tokens.
    if ! az account get-access-token --output none >/dev/null 2>&1; then
        echo "Azure session is missing/expired. Starting device-code login..."
        az login "${login_args[@]}"
    fi

    if [ -n "$AZURE_SUBSCRIPTION_ID" ]; then
        az account set --subscription "$AZURE_SUBSCRIPTION_ID"
    fi
}

# Check if version is provided
if [ -z "${1:-}" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1"
    echo "Optional: AZURE_TENANT_ID=<tenant> AZURE_SUBSCRIPTION_ID=<sub> $0 <version>"
    exit 1
fi

VERSION="$1"
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"

echo "Building Docker image: $FULL_IMAGE_NAME..."
docker build -t "$IMAGE_NAME:$VERSION" .

echo "Tagging image..."
docker tag "$IMAGE_NAME:$VERSION" "$FULL_IMAGE_NAME"

echo "Logging in to Azure Container Registry..."
ensure_azure_login

if ! az acr login --name "$ACR_NAME"; then
    echo "ACR login failed."
    echo "If your org enforces sign-in frequency, re-run with device code and explicit tenant/subscription:"
    echo "  AZURE_TENANT_ID=<tenant-guid> AZURE_SUBSCRIPTION_ID=<subscription-id> $0 $VERSION"
    exit 1
fi

echo "Pushing image to Azure Container Registry..."
docker push "$FULL_IMAGE_NAME"

echo "Done! Image pushed to $FULL_IMAGE_NAME"
