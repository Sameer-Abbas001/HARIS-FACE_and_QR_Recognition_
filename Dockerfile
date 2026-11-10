# ==============================================================================
# HARIS - High-Accuracy Recognition & Identity System
# Production Dockerfile for AWS EC2 & Containerized Deployment
# Creator & Lead Developer: Sameer Abbas
# ==============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install required system libraries for OpenCV headless, fonts, and health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install Python packages using pre-compiled binary wheels (avoids OOM on 1GB EC2)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy the full project codebase
COPY . /app/

# Ensure data directories exist
RUN mkdir -p /app/data/classifiers /app/data/qrcodes

EXPOSE 5000

CMD ["python", "web_app.py"]
