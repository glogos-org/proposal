# Glogos High-Throughput Zone - Dockerfile
# Development build with RocksDB support

FROM python:3.11-slim-bookworm AS builder

# Install build dependencies for RocksDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    librocksdb-dev \
    libsnappy-dev \
    zlib1g-dev \
    libbz2-dev \
    liblz4-dev \
    libzstd-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir python-rocksdb || echo "RocksDB optional, using fallback"


# =============================================================================
# Development image
# =============================================================================

FROM python:3.11-slim-bookworm

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    librocksdb7.8 \
    libsnappy1v5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash glogos

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY zone/ ./src/

# Create data directory
RUN mkdir -p /data && chown -R glogos:glogos /data /app

# Switch to non-root user
USER glogos

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ROCKSDB_PATH=/data/rocksdb \
    BITCOIN_NETWORK=testnet3 \
    BITCOIN_SIMULATION=true \
    PORT=8000 \
    HOST=0.0.0.0

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "src.app"]
