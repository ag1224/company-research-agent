# Docker Build Guide

## 🐳 Building Docker Image for Company Research API

This guide will help you build and run the Company Research API as a Docker container.

## Prerequisites

### 1. Install Docker Desktop

**For macOS:**
1. Download Docker Desktop from: https://docs.docker.com/desktop/install/mac/
2. Install and start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

**For Windows:**
1. Download Docker Desktop from: https://docs.docker.com/desktop/install/windows/
2. Install and start Docker Desktop
3. Verify installation in PowerShell/CMD

**For Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

## 🏗️ Building the Docker Image

### 1. Basic Build
```bash
# Build the image with a tag
docker build -t company-research-api .

# Build with version tag
docker build -t company-research-api:v1.0.0 .
```

### 2. Build with Build Arguments (Optional)
```bash
# Build with custom Python version
docker build --build-arg PYTHON_VERSION=3.11 -t company-research-api .
```

### 3. Build for Multi-platform (Optional)
```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t company-research-api .
```

## 🚀 Running the Docker Container

### 1. Run with Environment Variables
```bash
# Create .env file first (copy from .env.example)
cp .env.example .env
# Edit .env with your actual API keys

# Run with environment file
docker run -d \
  --name company-research-api \
  --env-file .env \
  -p 8000:8000 \
  company-research-api
```

### 2. Run with Individual Environment Variables
```bash
docker run -d \
  --name company-research-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_openai_key \
  -e APOLLO_API_KEY=your_apollo_key \
  -e CORESIGNAL_API_KEY=your_coresignal_key \
  -e TAVILY_API_KEY=your_tavily_key \
  company-research-api
```

### 3. Run with Volume Mounts (for file persistence)
```bash
docker run -d \
  --name company-research-api \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/service_account.json:/app/service_account.json \
  company-research-api
```

### 4. Run Interactively (for debugging)
```bash
docker run -it \
  --env-file .env \
  -p 8000:8000 \
  company-research-api bash
```

## 🐳 Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  company-research-api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./results:/app/results
      - ./service_account.json:/app/service_account.json:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Run with Docker Compose:
```bash
# Build and start
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

## 🛠️ Docker Management Commands

### Image Management:
```bash
# List images
docker images

# Remove image
docker rmi company-research-api

# Remove unused images
docker image prune
```

### Container Management:
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Stop container
docker stop company-research-api

# Remove container
docker rm company-research-api

# View logs
docker logs company-research-api

# Follow logs
docker logs -f company-research-api

# Execute command in running container
docker exec -it company-research-api bash
```

### System Cleanup:
```bash
# Remove all stopped containers, unused networks, images, and build cache
docker system prune -a

# Remove volumes (be careful!)
docker volume prune
```

## 🧪 Testing the Docker Container

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. API Documentation
Open: http://localhost:8000/docs

### 3. Test API Endpoint
```bash
curl -X POST "http://localhost:8000/multi-source-research" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "OpenAI",
    "domain": "openai.com",
    "save_to_file": true,
    "return_data": true
  }'
```

## 📁 Current Dockerfile Analysis

Your `Dockerfile` includes:
- ✅ Python 3.11 base image
- ✅ System dependencies (pandoc, texlive, etc.)
- ✅ Python dependencies installation
- ✅ Application code copy
- ✅ Port exposure (8000)
- ✅ Startup command

## 🔧 Optimization Tips

### 1. Multi-stage Build (for smaller images)
```dockerfile
# Builder stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
WORKDIR /app
COPY . .
CMD ["uvicorn", "api.company_research_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Layer Caching
```bash
# Build with cache mount
docker build --cache-from company-research-api:latest -t company-research-api .
```

### 3. Reduce Image Size
```bash
# Check image size
docker images company-research-api

# Use alpine base image for smaller size (in Dockerfile)
FROM python:3.11-alpine
```

## 🚨 Troubleshooting

### Common Issues:

1. **Build fails due to missing system dependencies**:
   ```bash
   # Check build logs
   docker build --no-cache -t company-research-api .
   ```

2. **Container exits immediately**:
   ```bash
   # Check logs
   docker logs company-research-api
   
   # Run interactively
   docker run -it --env-file .env company-research-api bash
   ```

3. **API keys not working**:
   ```bash
   # Check environment variables in container
   docker exec company-research-api env | grep API_KEY
   ```

4. **Port conflicts**:
   ```bash
   # Use different port
   docker run -p 3000:8000 company-research-api
   ```

5. **Volume mount issues**:
   ```bash
   # Check file permissions
   ls -la results/
   
   # Fix permissions
   chmod 755 results/
   ```

## 🚀 Production Considerations

1. **Use specific version tags**:
   ```bash
   docker build -t company-research-api:1.0.0 .
   ```

2. **Use health checks**:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8000/health || exit 1
   ```

3. **Set resource limits**:
   ```bash
   docker run --memory=2g --cpus=1.0 company-research-api
   ```

4. **Use secrets for API keys**:
   ```bash
   # Docker secrets (Docker Swarm)
   echo "your_api_key" | docker secret create openai_key -
   ```

Your Docker image is ready to build! 🐳 