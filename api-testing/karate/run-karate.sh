#!/bin/bash
set -euo pipefail

# Helper script to run Karate tests
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KARATE_VERSION="1.4.1"
KARATE_CACHE="$SCRIPT_DIR/.cache"
KARATE_JAR="$KARATE_CACHE/karate-${KARATE_VERSION}.jar"

# Check if karate.jar is present, download if not (v1.4.1)
mkdir -p "$KARATE_CACHE"
if [ ! -f "$KARATE_JAR" ]; then
    echo "Karate jar not found, downloading v${KARATE_VERSION}..."
    curl -L "https://github.com/karatelabs/karate/releases/download/v${KARATE_VERSION}/karate-${KARATE_VERSION}.jar" -o "$KARATE_JAR"
fi

if [ "$#" -gt 0 ]; then
    targets=()
    for target in "$@"; do
        if [[ "$target" = /* ]]; then
            targets+=("$target")
        else
            targets+=("$SCRIPT_DIR/$target")
        fi
    done
    java -jar "$KARATE_JAR" "${targets[@]}"
else
    java -jar "$KARATE_JAR" "$SCRIPT_DIR"
fi
