# Use the official Python image.
FROM python:3.11-slim


# Set the working directory.
WORKDIR /app

# Add a build argument for cache busting
ARG CACHE_BUST=1
ENV BUILD_DATE="2025-12-29-CHECK-DEPLOYMENT"

# Copy shared library and setup file
# Copy the setup file and the shared library
COPY setup.py /app/
COPY shared /app/shared

# Install the shared library
RUN pip install --upgrade pip && pip install /app/.

# Copy the agent-specific code and install its requirements
COPY agents/ingestion-agent/. /app
RUN pip install -r requirements.txt


# Run the function.
# The functions-framework will start a web server on the port specified by the PORT environment variable.
CMD exec functions-framework --target=ingestion_analysis_agent --port=$PORT
