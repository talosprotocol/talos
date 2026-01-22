# =============================================================================
# Talos Protocol Makefile
# =============================================================================
SHELL := /bin/bash

.PHONY: all build test verify dev clean docker-build k8s-manifests

all: build

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
build:
\t@echo "🚀 Building complete ecosystem..."
\t@bash scripts/pre-commit

test:
\t@echo "🧪 Running all tests..."
\t@bash deploy/scripts/run_all_tests.sh

verify:
\t@echo "🔍 Verifying integrity..."
\t@bash scripts/pre-push-validate.sh

dev:
\t@echo "▶️  Starting local stack..."
\t@bash deploy/scripts/start_all.sh

clean:
\t@echo "🧹 Cleaning up..."
\t@bash deploy/scripts/cleanup_all.sh

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
docker-build:
\t@echo "🐳 Building Docker images..."
\t@docker build -f docker/Dockerfile.talos-node -t talos-node:latest .
\t@docker build -f docker/Dockerfile.ucp-connector -t talos-ucp-connector:latest .
\t@echo "✅ Docker images built."

# -----------------------------------------------------------------------------
# Kubernetes
# -----------------------------------------------------------------------------
k8s-manifests:
\t@echo "☸️  Generating K8s manifests..."
\t@kubectl kustomize deploy/k8s/base > deploy/k8s/generated.yaml
\t@echo "✅ Manifests generated at deploy/k8s/generated.yaml"
