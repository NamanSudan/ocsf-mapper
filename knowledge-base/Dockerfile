FROM python:3.9-slim

WORKDIR /app

# Install system dependencies and upgrade pip
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8082", "--workers", "4", "--access-logfile", "-", "app:app"] 