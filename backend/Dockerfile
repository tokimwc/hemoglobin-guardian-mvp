FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && find /usr/local -type d -name __pycache__ -exec rm -r {} + || true

# Final stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Create necessary directories
RUN mkdir -p /app/src /app/credentials

# Copy application code and credentials
COPY ./src/ ./src/
COPY ./credentials/ ./credentials/
COPY ./main.py .
COPY ./requirements.txt .

# Set environment variables
ENV PORT=8080 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    WORKERS=1 \
    TIMEOUT=300 \
    GRACEFUL_TIMEOUT=300 \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    DEBIAN_FRONTEND=noninteractive

# Expose port
EXPOSE ${PORT}

# Health check with retry mechanism
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start command with explicit environment variable usage
CMD ["sh", "-c", "python -m uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKERS} --timeout ${TIMEOUT} --proxy-headers --forwarded-allow-ips=* --lifespan on"] 