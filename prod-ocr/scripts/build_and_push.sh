#!/bin/bash

# Default variables
IMAGE_NAME="prod-ocr"
DOCKER_USERNAME="cramital.azurecr.io"

# Check if version is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1"
    exit 1
fi

VERSION=$1
FULL_IMAGE_NAME="$DOCKER_USERNAME/$IMAGE_NAME:$VERSION"

echo "Building Docker image: $FULL_IMAGE_NAME..."
docker build -t $IMAGE_NAME:$VERSION .

if [ $? -eq 0 ]; then
    echo "Tagging image..."
    docker tag $IMAGE_NAME:$VERSION $FULL_IMAGE_NAME

    if [ $? -eq 0 ]; then

        #check if logged in to azure container registry
        echo "Logging in to Azure Container Registry..."
        if ! az acr login --name cramital &> /dev/null; then
            echo "Not logged in. Please log in to Azure."
            az login
        fi
        az acr login --name cramital

        echo "Pushing image to Docker Hub..."
        docker push $FULL_IMAGE_NAME
        
        if [ $? -eq 0 ]; then
            echo "Done! Image pushed to $FULL_IMAGE_NAME"
        else
            echo "Failed to push image."
            exit 1
        fi
    else
        echo "Failed to tag image."
        exit 1
    fi
else
    echo "Failed to build image."
    exit 1
fi
