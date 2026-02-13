# Use the official Python image.
FROM python:3.11-slim

# Set the working directory.
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY agents/condition-assessor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared library and the agent code
# This assumes the build context is the project root directory
COPY shared/ ./shared/
COPY agents/condition-assessor/ ./

# Add the app directory to the PYTHONPATH to ensure 'shared' can be imported
ENV PYTHONPATH /app

# Run the function.
# The functions-framework will start a web server on the port specified by the PORT environment variable.
CMD exec functions-framework --target=assess_condition_handler --port=$PORT