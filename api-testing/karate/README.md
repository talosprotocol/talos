# Talos Karate API Tests

This directory contains additional Karate API tests for Talos core and backend
services.

## Prerequisites
- Java JRE/JDK 8 or higher
- `karate.jar` (the `run-karate.sh` script downloads it into `.cache/` if
  missing)

## Structure
- `gateway.feature`: Tests for the main Gateway service (`services/gateway`).
- `ai_gateway.feature`: Tests for the AI Gateway service (`services/ai-gateway`).
- `audit.feature`: Tests for the Audit service (`services/audit`).
- `configuration.feature`: Tests for the Configuration service (`services/configuration`).
- `api_validation.feature`: General API schema and contract validation.

## Running Tests
To run all tests:
```bash
api-testing/karate/run-karate.sh
```

To run a specific feature:
```bash
java -jar api-testing/karate/.cache/karate-1.4.1.jar api-testing/karate/ai_gateway.feature
```

## Service Mapping (Local Dev)
- **Gateway**: http://localhost:8000
- **AI Gateway**: http://localhost:8001
- **Audit**: http://localhost:8002
- **Configuration**: http://localhost:8003
