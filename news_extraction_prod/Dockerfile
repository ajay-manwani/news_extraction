# Dockerfile for Cloud Run deployment
FROM python:3.11-slim

# Install system dependencies for audio processing and eSpeak
RUN apt-get update && apt-get install -y \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose the port
EXPOSE 8080

# Run the application with gunicorn for production
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 900 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 main:app