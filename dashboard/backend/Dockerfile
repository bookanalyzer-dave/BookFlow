FROM python:3.11-slim

WORKDIR /app

# Copy the setup file and the shared library
COPY setup.py /app/
COPY shared /app/shared

# Install the shared library
RUN pip install --upgrade pip && pip install --no-cache-dir /app/.

# Copy the backend-specific code and install its requirements
COPY dashboard/backend/. /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]