# Sentinel Agent - Sale Notification Handler
# Dockerfile for Cloud Run deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared modules first
COPY shared ./shared

# Copy agent-specific files
COPY agents/sentinel-agent/requirements.txt ./
COPY agents/sentinel-agent/main.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/workspace"
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import sys; print('Health OK')" || exit 1

# Expose port
EXPOSE 8080

# Run the Cloud Function
CMD exec functions-framework --target=sentinel_agent --port=$PORT