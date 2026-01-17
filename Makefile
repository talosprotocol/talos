# Talos Project Makefile (Monorepo)

PYTHON=python3
PIP=pip
NPM=npm
GATEWAY_DIR=deploy/repos/talos-ai-gateway
DASHBOARD_DIR=deploy/repos/talos-dashboard

.PHONY: all install dev clean build-ui test

all: install build-ui

# --- Installation ---
install: install-python install-ui

install-python:
	@echo "Installing Gateway dependencies..."
	cd $(GATEWAY_DIR) && $(PIP) install -r requirements.txt
	cd $(GATEWAY_DIR) && $(PIP) install -e .

install-ui:
	@echo "Installing Dashboard dependencies..."
	cd $(DASHBOARD_DIR) && $(NPM) install

# --- Development ---
dev:
	@echo "Starting Development Stack (via start.sh)..."
	./start.sh

# --- Testing ---
test: test-gateway

test-gateway:
	@echo "Running Gateway Tests..."
	cd $(GATEWAY_DIR) && pytest tests/

# --- Build ---
build-ui:
	cd $(DASHBOARD_DIR) && $(NPM) run build

# --- Cleanup ---
clean:
	rm -rf $(DASHBOARD_DIR)/.next
	rm -rf $(DASHBOARD_DIR)/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

