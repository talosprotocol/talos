# =============================================================================
# Talos Protocol Makefile
# =============================================================================
SHELL := /bin/bash
TEST_ARGS ?= --ci

.PHONY: all build test verify dev clean docker-build k8s-manifests help
.PHONY: test-all build-all-sdks docker-build-all docker-push-all ci

all: build

# -----------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help:
	@echo "Talos Protocol - Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  make build          - Build complete ecosystem"
	@echo "  make test           - Run the root test runner (default: --ci)"
	@echo "  make test-all       - Run the root test runner in --full mode"
	@echo "  make verify         - Verify integrity"
	@echo "  make dev            - Start local stack"
	@echo "  make clean          - Clean up"
	@echo ""
	@echo "SDKs:"
	@echo "  make build-all-sdks - Build all SDKs"
	@echo "  make test-sdks      - Test all SDKs"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build       - Build core Docker images"
	@echo "  make docker-build-all   - Build all Docker images (including SDKs)"
	@echo "  make docker-push-all    - Push all Docker images"
	@echo "  make docker-dev-up      - Start SDK development environment"
	@echo "  make docker-dev-down    - Stop SDK development environment"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-manifests  - Generate K8s manifests"
	@echo "  make k8s-deploy     - Deploy to Kubernetes"
	@echo "  make k8s-delete     - Remove from Kubernetes"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci             - Full CI pipeline"
	@echo ""
	@echo "Examples:"
	@echo '  make test TEST_ARGS="--only talos-contracts"'
	@echo '  make test TEST_ARGS="--only category:sdk --changed"'

# -----------------------------------------------------------------------------
# Development
# -----------------------------------------------------------------------------
build:
	@echo "🚀 Building complete ecosystem..."
	@bash scripts/pre-commit

test:
	@echo "🧪 Running all tests..."
	@bash deploy/scripts/run_all_tests.sh $(TEST_ARGS)

test-all:
	@echo "🧪 Running full test suite..."
	@bash deploy/scripts/run_all_tests.sh --full

verify:
	@echo "🔍 Verifying integrity..."
	@bash scripts/pre-push-validate.sh

dev:
	@echo "▶️  Starting local stack..."
	@bash deploy/scripts/start_all.sh

clean:
	@echo "🧹 Cleaning up..."
	@bash deploy/scripts/cleanup_all.sh

# -----------------------------------------------------------------------------
# SDK Builds
# -----------------------------------------------------------------------------
build-all-sdks:
	@echo "🔨 Building all SDKs..."
	@cd sdks/go && make build
	@cd sdks/java && make build
	@cd sdks/rust && make build
	@cd sdks/python && make build
	@cd sdks/typescript && make build
	@echo "✅ All SDKs built"

test-sdks:
	@echo "🧪 Testing all SDKs..."
	@bash deploy/scripts/run_all_tests.sh --ci --only category:sdk
	@echo "✅ All SDK tests passed"

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
docker-build:
	@echo "🐳 Building Docker images..."
	@docker build -f docker/Dockerfile.talos-node -t talos-node:latest .
	@docker build -f docker/Dockerfile.ucp-connector -t talos-ucp-connector:latest .
	@echo "✅ Docker images built."

docker-build-all:
	@echo "🐳 Building all Docker images (SDKs + Services)..."
	@echo "Building SDK tool images..."
	@./scripts/docker_build_sdk_tool.sh --sdk all --tag latest
	@echo "Building service images..."
	@make docker-build
	@echo "✅ All Docker images built"

docker-build-sdks:
	@echo "🐳 Building SDK tool images..."
	@./scripts/docker_build_sdk_tool.sh --sdk all --tag ${TAG}

docker-build-sdk:
	@echo "🐳 Building ${SDK} SDK tool image..."
	@./scripts/docker_build_sdk_tool.sh --sdk ${SDK} --tag ${TAG}

docker-push-all:
	@echo "📤 Pushing all Docker images..."
	@cd sdks/go && make docker-push
	@cd sdks/java && make docker-push
	@cd sdks/rust && make docker-push
	@echo "✅ All Docker images pushed"

docker-dev-up:
	@echo "🐳 Starting SDK development environment..."
	@cd sdks && docker-compose -f docker-compose.dev.yml --profile sdks up -d
	@echo "✅ SDK development environment started"

docker-dev-down:
	@echo "🛑 Stopping SDK development environment..."
	@cd sdks && docker-compose -f docker-compose.dev.yml down
	@echo "✅ SDK development environment stopped"

# -----------------------------------------------------------------------------
# Kubernetes
# -----------------------------------------------------------------------------
k8s-manifests:
	@echo "☸️  Generating K8s manifests..."
	@kubectl kustomize deploy/k8s/base > deploy/k8s/generated.yaml
	@echo "✅ Manifests generated at deploy/k8s/generated.yaml"

k8s-deploy:
	@echo "☸️  Deploying to Kubernetes..."
	@kubectl apply -f deploy/k8s/generated.yaml
	@echo "✅ Deployed to Kubernetes"

k8s-delete:
	@echo "🗑️  Removing from Kubernetes..."
	@kubectl delete -f deploy/k8s/generated.yaml
	@kubectl delete -f deploy/k8s/generated.yaml
	@echo "✅ Removed from Kubernetes"

verify-manifests:
	@echo "🔍 Verifying K8s manifests..."
	@kubectl kustomize deploy/k8s/base > deploy/k8s/generated_check.yaml
	@if grep -q ":latest" deploy/k8s/generated_check.yaml; then echo "❌ Access Denied: ':latest' tag found in manifests"; exit 1; fi
	@if grep -q "image: [^:]*$$" deploy/k8s/generated_check.yaml; then echo "❌ Access Denied: Untagged image found in manifests"; exit 1; fi
	@echo "✅ Manifests clean (no :latest, no untagged images)"
	@rm deploy/k8s/generated_check.yaml

# -----------------------------------------------------------------------------
# CI/CD
# -----------------------------------------------------------------------------
ci:
	@echo "🚀 Running full CI pipeline..."
	@make build-all-sdks
	@make test-all
	@make docker-build-all
	@echo "✅ CI pipeline completed successfully"
