# Use an official lightweight Python image.
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory in the container
WORKDIR /app

# Copy local code to the container image.
COPY agents/price-research-agent/ .
COPY shared/ ./shared/

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ./shared

# Run the functions-framework
RUN pip install functions-framework
CMD exec functions-framework --target=price_research_handler --port=8080
