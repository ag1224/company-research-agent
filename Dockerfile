# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Ensure Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for PDF generation and other packages
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn

# Copy the entire application
COPY . .

# Create results directory with proper permissions for Railway volumes
RUN mkdir -p results && chmod 755 results

# Create placeholder for service account (will be mounted as volume in Railway)
RUN touch service_account.json && chmod 644 service_account.json

# Expose port (Railway will set PORT environment variable)
EXPOSE 8000

# Make start.sh executable and use it as the command
RUN chmod +x start.sh
CMD ["./start.sh"] 