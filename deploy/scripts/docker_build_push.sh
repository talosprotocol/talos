#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Build and Push Docker Images
# Usage: ./deploy/scripts/docker_build_push.sh [version]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
ORG="${DOCKER_ORG:-talosprotocol}"
VERSION="${1:-latest}"

# Services to build
SERVICES=(
    "talos-gateway:deploy/repos/talos-gateway"
    "talos-dashboard:deploy/repos/talos-dashboard"
    "talos-mcp-connector:deploy/repos/talos-mcp-connector"
    "talos-audit-service:deploy/repos/talos-audit-service"
)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Build and push each service
# =============================================================================
build_and_push() {
    local name="$1"
    local context="$2"
    local full_tag="${REGISTRY}/${ORG}/${name}:${VERSION}"
    local latest_tag="${REGISTRY}/${ORG}/${name}:latest"
    
    log_info "Building ${name}..."
    
    # Dashboard needs NPM secret for private packages
    if [ "$name" = "talos-dashboard" ]; then
        # Create temporary npmrc with token
        echo "//npm.pkg.github.com/:_authToken=${NPM_TOKEN:-}" > /tmp/.npmrc.docker
        echo "@talosprotocol:registry=https://npm.pkg.github.com" >> /tmp/.npmrc.docker
        
        DOCKER_BUILDKIT=1 docker build \
            --secret id=npmrc,src=/tmp/.npmrc.docker \
            -t "${full_tag}" -t "${latest_tag}" \
            "${ROOT_DIR}/${context}"
        
        rm -f /tmp/.npmrc.docker
    else
        docker build -t "${full_tag}" -t "${latest_tag}" "${ROOT_DIR}/${context}"
    fi
    
    if [ "${PUSH:-false}" = "true" ]; then
        log_info "Pushing ${name}..."
        docker push "${full_tag}"
        docker push "${latest_tag}"
    else
        log_warn "Skipping push (set PUSH=true to push)"
    fi
    
    log_info "✓ ${name} complete"
}

# =============================================================================
# Main
# =============================================================================
echo "=========================================="
echo "Talos Protocol - Docker Build & Push"
echo "=========================================="
echo "Registry: ${REGISTRY}"
echo "Org: ${ORG}"
echo "Version: ${VERSION}"
echo ""

for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name context <<< "$entry"
    build_and_push "$name" "$context"
done

echo ""
log_info "All images built!"

if [ "${PUSH:-false}" = "true" ]; then
    log_info "All images pushed to ${REGISTRY}/${ORG}"
else
    echo ""
    echo "To push images, run:"
    echo "  PUSH=true $0 ${VERSION}"
fi
