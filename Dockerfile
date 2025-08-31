# Multi-stage Dockerfile for Synthetic Data MCP Platform
# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml poetry.lock* ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Stage 2: Production
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r synthetic && useradd -r -g synthetic synthetic

# Set working directory
WORKDIR /app

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R synthetic:synthetic /app

# Security: Drop privileges
USER synthetic

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SYNTHETIC_DATA_HOME=/app \
    SYNTHETIC_DATA_LOG_LEVEL=INFO \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Run the application
CMD ["python", "-m", "synthetic_data_mcp.server"]