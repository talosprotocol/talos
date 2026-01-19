# Universal Makefile Interface
all: install lint test build conformance

install:
	pip install -e .[dev]

typecheck:
	# Enforce type checking (Gradual initially, Strict for core later)
	mypy src tests

lint:
	# Style + Types (Fail on error)
	ruff check .
	mypy src tests

format:
	# Auto-fix style
	ruff format .
	ruff check --fix .

test:
	# Unit tests (Must include happy paths)
	pytest tests

coverage:
	# Run coverage report
	@if ! pip show pytest-cov > /dev/null; then \
		echo "Installing pytest-cov..."; \
		pip install pytest-cov; \
	fi
	pytest --cov=src --cov-report=term-missing tests

coverage-check:
	# Enforce threshold (Fail if < 80%)
	pytest --cov=src --cov-fail-under=80 tests

conformance:
	# Run conformance vectors
	# Usage: make conformance RELEASE_SET=v1.1.0.json
	@set_val="$(RELEASE_SET)"; \
	if [ -z "$$set_val" ]; then \
		echo "Defaulting to RELEASE_SET=v1.1.0.json"; \
		set_val="v1.1.0.json"; \
	fi; \
	talos-sdk --vectors ../talos-contracts/test_vectors/sdk/release_sets/$$set_val --report conformance.xml

build:
	python -m build

clean:
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
