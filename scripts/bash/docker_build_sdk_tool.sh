#!/usr/bin/env bash
# =============================================================================
# Build SDK Tool Images with Consistent Tagging and Labeling
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
SDK=""
TAG=""
REGISTRY="ghcr.io/talosprotocol"
GIT_SHA="${GIT_SHA:-$(git rev-parse --short HEAD)}"
VERSION="${VERSION:-dev}"

usage() {
    cat << EOF
Usage: $0 --sdk <go|java|rust> --tag <tag> [options]

Build SDK tool images with consistent tagging and OCI labels.

Required:
    --sdk SDK           SDK to build (go, java, rust, or 'all')
    --tag TAG           Image tag (e.g., sha-abc123, v1.0.0)

Optional:
    --registry REG      Container registry (default: ghcr.io/talosprotocol)
    --git-sha SHA       Git commit SHA (default: auto-detected)
    --version VER       Version for OCI label (default: dev)
    --push              Push image after build
    --help              Show this help message

Examples:
    # Build Go SDK with SHA tag
    $0 --sdk go --tag sha-$(git rev-parse --short HEAD)

    # Build all SDKs with version tag and push
    $0 --sdk all --tag v1.0.0 --push

    # Build Java SDK for CI
    $0 --sdk java --tag sha-abc123 --version 1.0.0
EOF
}

build_sdk() {
    local sdk=$1
    local tag=$2
    local full_image="${REGISTRY}/talos-sdk-${sdk}-tool:${tag}"
    
    local sdk_upper=$(echo "$sdk" | tr '[:lower:]' '[:upper:]')

    echo "🔨 Building ${sdk} SDK tool image..."
    echo "   Image: ${full_image}"
    echo "   Context: ${REPO_ROOT}"
    echo "   Dockerfile: sdks/${sdk}/Dockerfile"
    
    docker build \
        -f "${REPO_ROOT}/sdks/${sdk}/Dockerfile" \
        -t "${full_image}" \
        --label "org.opencontainers.image.source=https://github.com/talosprotocol/talos" \
        --label "org.opencontainers.image.description=Talos ${sdk_upper} SDK Tool Image" \
        --label "org.opencontainers.image.licenses=Apache-2.0" \
        --label "org.opencontainers.image.version=${VERSION}" \
        --label "org.opencontainers.image.revision=${GIT_SHA}" \
        --label "org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        "${REPO_ROOT}"
    
    echo "✅ Built: ${full_image}"
    
    if [[ "${PUSH:-false}" == "true" ]]; then
        echo "📤 Pushing ${full_image}..."
        docker push "${full_image}"
        echo "✅ Pushed: ${full_image}"
    fi
}

# Parse arguments
PUSH=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --sdk)
            SDK="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --git-sha)
            GIT_SHA="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SDK" ]]; then
    echo "Error: --sdk is required"
    usage
    exit 1
fi

if [[ -z "$TAG" ]]; then
    echo "Error: --tag is required"
    usage
    exit 1
fi

# Build SDKs
if [[ "$SDK" == "all" ]]; then
    for sdk in go java rust; do
        build_sdk "$sdk" "$TAG"
    done
else
    case $SDK in
        go|java|rust)
            build_sdk "$SDK" "$TAG"
            ;;
        *)
            echo "Error: Invalid SDK '$SDK'. Must be 'go', 'java', 'rust', or 'all'"
            exit 1
            ;;
    esac
fi

echo ""
echo "🎉 All SDK tool images built successfully!"
