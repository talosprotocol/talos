#!/bin/bash
# scripts/run-karate.sh

KARATE_VERSION="1.4.1"
KARATE_JAR="artifacts/karate-${KARATE_VERSION}.jar"
TEST_DIR="tests/karate"

# Ensure artifacts directory exists
mkdir -p artifacts

# Download Karate JAR if missing
if [ ! -f "$KARATE_JAR" ]; then
  echo "Downloading Karate ${KARATE_VERSION}..."
  curl -L -o "$KARATE_JAR" "https://github.com/karatelabs/karate/releases/download/v${KARATE_VERSION}/karate-${KARATE_VERSION}.jar"
fi

# Run Karate tests
echo "Running Karate tests against http://localhost:8000 (Gateway) and http://localhost:8002 (Audit)..."
java -jar "$KARATE_JAR" "$TEST_DIR"
