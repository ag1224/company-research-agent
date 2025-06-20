#!/bin/bash

# Set default port if not provided
PORT=${PORT:-8000}

# Start the FastAPI application
exec uvicorn api.company_research_fastapi:app --host 0.0.0.0 --port $PORT 