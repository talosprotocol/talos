# sandbox/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy the repository (use .dockerignore to filter)
COPY . .

# Install Python dependencies for core tools
RUN pip install --no-cache-dir -r requirements.txt || true

# Install SDKs
RUN cd sdks/python && pip install -e . || true
RUN cd sdks/typescript && npm install && npm run build || true

# Set environment variables for the sandbox
ENV TALOS_ENV=sandbox
ENV PYTHONPATH=/app

# Default command: show help
CMD ["python3", "-m", "talos", "--help"]
