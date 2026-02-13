FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY agents/ambassador-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libraries
COPY shared/ ./shared/

# Copy agent code and platform modules
COPY agents/ambassador-agent/main.py .
COPY agents/ambassador-agent/platforms/ ./platforms/

# Install shared package
RUN pip install -e ./shared/

# Set environment variables for Cloud Functions
ENV FUNCTIONS_FRAMEWORK_DEBUG=true
ENV PORT=8080

# Expose port
EXPOSE 8080

# Use functions-framework to run the function
CMD exec functions-framework --target=handle_listing_request --source=main.py --port=$PORT