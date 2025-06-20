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

# Create results directory
RUN mkdir -p results

# Expose port (Railway will set PORT environment variable)
EXPOSE 8000

# Command to run the application
CMD uvicorn api.company_research_fastapi:app --host 0.0.0.0 --port ${PORT:-8000} 