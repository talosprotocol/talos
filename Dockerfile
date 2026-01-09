# Talos Protocol
# Multi-stage production Dockerfile

# ================================
# Stage 1: Builder
# ================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ================================
# Stage 2: Production
# ================================
FROM python:3.11-slim as production

LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Security: Create non-root user
RUN groupadd -r talos && useradd -r -g talos talos

# Copy Python packages from builder
COPY --from=builder /root/.local /home/talos/.local

# Copy application code
COPY src/ ./src/
COPY talos/ ./talos/
COPY examples/ ./examples/
COPY pyproject.toml .
COPY README.md .

# Set permissions
RUN chown -R talos:talos /app

# Environment
ENV PATH=/home/talos/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER talos

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core.blockchain import Blockchain; print('OK')"

# Default command: Run P2P node
EXPOSE 8765 8468

CMD ["python", "-m", "src.server.server"]

# ================================
# Development Stage (optional)
# ================================
FROM production as development

USER root

# Install dev dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov

USER talos

CMD ["pytest", "tests/", "-v"]
