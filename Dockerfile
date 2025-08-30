FROM python:3.11-slim

# Install essential system dependencies for audio and TTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak \
    espeak-data \
    libespeak1 \
    sox \
    libsox-fmt-mp3 \
    portaudio19-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libgthread-2.0-0 \
    alsa-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create directories for data persistence
RUN mkdir -p /app/data /app/config

# Expose ports
EXPOSE 8080 8081

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PULSE_SERVER=unix:/tmp/pulse-socket

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "src/main.py"]