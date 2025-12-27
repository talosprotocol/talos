# Talos Project Makefile

PYTHON=python3
PIP=pip
NPM=npm
NODE_ENV=development

.PHONY: all install dev clean build-ui test

all: install build-ui

# --- Installation ---
install: install-python install-ui

install-python:
	$(PIP) install -e ".[dev]"
	$(PIP) install fastapi uvicorn requests

install-ui:
	cd ui/dashboard && $(NPM) install

# --- Development ---
dev:
	@echo "Starting Talos Development Environment..."
	@# Trap SIGINT to kill all child processes
	@trap 'kill 0' SIGINT; \
	$(PYTHON) -m uvicorn src.api.server:app --reload --port 8000 & \
	cd ui/dashboard && NEXT_PUBLIC_TALOS_DATA_MODE=HTTP $(NPM) run dev & \
	sleep 5 && $(PYTHON) scripts/traffic_gen.py & \
	wait

# --- Testing ---
test: test-python

test-python:
	pytest tests/

# --- Build ---
build-ui:
	cd ui/dashboard && $(NPM) run build

# --- Cleanup ---
clean:
	rm -rf ui/dashboard/.next
	rm -rf ui/dashboard/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
