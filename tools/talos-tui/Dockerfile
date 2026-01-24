# Build Stage
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy project files
COPY python/ .

# Build wheel
RUN python -m build

# Runtime Stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 talos && \
    chown -R talos:talos /app

USER talos

# Copy artifact from builder
COPY --from=builder --chown=talos:talos /app/dist/*.whl /app/dist/

# Install application
RUN pip install --no-cache-dir /app/dist/*.whl

# Ensure local bin is in PATH
ENV PATH="/home/talos/.local/bin:${PATH}"

# Default configuration env vars
ENV TALOS_GATEWAY_URL="http://gateway:8000"
ENV TALOS_AUDIT_URL="http://audit:8001"

ENTRYPOINT ["talos-tui"]
