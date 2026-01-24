.PHONY: setup install test lint clean run build

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
TALOS_TUI = $(VENV)/bin/talos-tui

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

install:
	$(PIP) install -e .

test:
	$(PYTHON) -m pytest tests/unit tests/integration tests/architecture

test-cov:
	$(PYTHON) -m pytest --cov=talos_tui --cov-report=term-missing tests/

perf:
	$(PYTHON) tests/test_perf_budget.py

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/mypy src/talos_tui

clean:
	rm -rf dist/ build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

build: clean
	$(PYTHON) -m build

run:
	$(TALOS_TUI)
