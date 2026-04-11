#!/usr/bin/env bash
# scripts/bash/generate-local-secrets.sh
# Generates secure random secrets for local development and testing.
# Populates or updates .env.local with these secrets.
# Compatible with Bash 3.2 (macOS default).

set -eo pipefail

# Get the actual script path even if called via symlink
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.local"

echo "---------------------------------------------------"
echo "🔐 Talos Local Secret Generator"
echo "---------------------------------------------------"

# Function to generate a random base64 secret
gen_secret() {
    openssl rand -base64 32 | tr -d '\n'
}

# Function to generate a random hex secret
gen_hex() {
    openssl rand -hex 16 | tr -d '\n'
}

# Ensure .env.local exists
if [[ ! -f "$ENV_FILE" ]]; then
    echo "📄 Creating new .env.local from .env.example..."
    cp "$ROOT_DIR/.env.example" "$ENV_FILE"
fi

# List of secrets to update
KEYS="AUTH_SECRET AUTH_ADMIN_SECRET AUTH_COOKIE_HMAC_SECRET TALOS_BOOTSTRAP_TOKEN TALOS_SERVICE_TOKEN TALOS_SECRET_KEY MASTER_KEY"

echo "Updating secrets in .env.local..."

for key in $KEYS; do
    if [[ "$key" == *"TOKEN"* ]]; then
        val=$(gen_hex)
    else
        val=$(gen_secret)
    fi

    if grep -q "^${key}=" "$ENV_FILE"; then
        # Use @ as delimiter to avoid issues with / in base64
        sed "s@^${key}=.*@${key}=${val}@" "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
        echo "  ✅ Updated $key"
    else
        echo "${key}=${val}" >> "$ENV_FILE"
        echo "  ➕ Added $key"
    fi
done

# Sync to submodules
echo "---------------------------------------------------"
echo "Syncing secrets to submodules..."

SUBMODULES="site/dashboard services/gateway services/audit"

for sm in $SUBMODULES; do
    if [[ -d "$ROOT_DIR/$sm" ]]; then
        SM_ENV="$ROOT_DIR/$sm/.env.local"
        if [[ ! -f "$SM_ENV" ]] && [[ -f "$ROOT_DIR/$sm/.env.example" ]]; then
            cp "$ROOT_DIR/$sm/.env.example" "$SM_ENV"
        fi
        
        if [[ -f "$SM_ENV" ]]; then
            # Read current values from .env.local and sync them
            for key in $KEYS; do
                if grep -q "^${key}=" "$ENV_FILE" && grep -q "^${key}=" "$SM_ENV"; then
                    val=$(grep "^${key}=" "$ENV_FILE" | cut -d'=' -f2-)
                    sed "s@^${key}=.*@${key}=${val}@" "$SM_ENV" > "${SM_ENV}.tmp" && mv "${SM_ENV}.tmp" "$SM_ENV"
                fi
            done
            echo "  ✅ Synced to $sm"
        fi
    fi
done

echo "---------------------------------------------------"
echo "✨ All local secrets generated and synced!"
echo "⚠️  REMEMBER: Never commit .env.local files to version control."
echo "---------------------------------------------------"
