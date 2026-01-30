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
    "talos-gateway:services/gateway"
    "talos-ai-gateway:services/ai-gateway"
    "talos-dashboard:site/dashboard"
    "talos-mcp-connector:services/mcp-connector"
    "talos-audit-service:services/audit"
)

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

# =============================================================================
# Build and push each service
# =============================================================================
build_and_push() {
    local name="$1"
    local context="$2"
    local full_tag="${REGISTRY}/${ORG}/${name}:${VERSION}"
    local latest_tag="${REGISTRY}/${ORG}/${name}:latest"
    
    info "Building ${name}..."
    
    # Gateway context is always ROOT because it copies SDKs/contracts
    if [[ "$name" == "talos-gateway" || "$name" == "talos-ai-gateway" || "$name" == "talos-mcp-connector" || "$name" == "talos-audit-service" ]]; then
        info "Building ${name} from ROOT context..."
        docker build -f "${ROOT_DIR}/${context}/Dockerfile" -t "${full_tag}" -t "${latest_tag}" "${ROOT_DIR}"
    elif [ "$name" = "talos-dashboard" ]; then
        # Create temporary npmrc with token
        echo "//npm.pkg.github.com/:_authToken=${NPM_TOKEN:-}" > /tmp/.npmrc.docker
        echo "@talosprotocol:registry=https://npm.pkg.github.com" >> /tmp/.npmrc.docker
        
        # Build from ROOT context
        info "Building Dashboard from ROOT context..."
        DOCKER_BUILDKIT=1 docker build \
            --secret id=npmrc,src=/tmp/.npmrc.docker \
            -f "${ROOT_DIR}/${context}/Dockerfile" \
            -t "${full_tag}" -t "${latest_tag}" \
            "${ROOT_DIR}"
        
        rm -f /tmp/.npmrc.docker
    else
        docker build -t "${full_tag}" -t "${latest_tag}" "${ROOT_DIR}/${context}"
    fi
    
    if [ "${PUSH:-false}" = "true" ]; then
        info "Pushing ${name}..."
        docker push "${full_tag}"
        docker push "${latest_tag}"
    else
        warn "Skipping push (set PUSH=true to push)"
    fi
    
    info "✓ ${name} complete"
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
info "All images built!"

if [ "${PUSH:-false}" = "true" ]; then
    info "All images pushed to ${REGISTRY}/${ORG}"
else
    echo ""
    echo "To push images, run:"
    echo "  PUSH=true $0 ${VERSION}"
fi
