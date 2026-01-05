# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run uvicorn with host 0.0.0.0 and port from environment variable
# Cloud Run will automatically set the PORT environment variable
# The /health endpoint is available for Cloud Run health checks
# 这种写法会自动解析 $PORT 环境变量
CMD uvicorn main:app --host 0.0.0.0 --port $PORT

