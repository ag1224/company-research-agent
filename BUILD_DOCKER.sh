#!/bin/bash

# Company Research API - Docker Build Script

echo "🐳 Building Company Research API Docker Image..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t company-research-api:latest .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo "📊 Image details:"
    docker images company-research-api:latest
    
    echo ""
    echo "🚀 To run the container:"
    echo "docker-compose up -d"
    echo ""
    echo "🧪 To test the API:"
    echo "curl http://localhost:8000/health"
else
    echo "❌ Docker build failed!"
    exit 1
fi 