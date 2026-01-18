#!/bin/bash
# Build all Docker images with version metadata

set -e

# Get version info
GIT_SHA=$(git rev-parse HEAD)
VERSION=$(git rev-parse --short HEAD)
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "Building Talos Docker images..."
echo "  Version: $VERSION"
echo "  SHA: $GIT_SHA"
echo "  Build Time: $BUILD_TIME"
echo ""

SERVICES=("gateway" "audit" "mcp-connector" "dashboard")

for service in "${SERVICES[@]}"; do
  echo "Building $service..."
  
  if [ "$service" = "dashboard" ]; then
    DOCKERFILE="site/dashboard/Dockerfile"
    IMAGE_NAME="talos-dashboard"
  else
    DOCKERFILE="services/$service/Dockerfile"
    IMAGE_NAME="talos-$service"
    if [ "$service" = "mcp-connector" ]; then
      IMAGE_NAME="talos-mcp-connector"
    elif [ "$service" = "audit" ]; then
      IMAGE_NAME="talos-audit-service"
    fi
  fi
  
  docker build \
    --build-arg GIT_SHA="$GIT_SHA" \
    --build-arg VERSION="$VERSION" \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    -t "$IMAGE_NAME:latest" \
    -t "$IMAGE_NAME:$VERSION" \
    -f "$DOCKERFILE" \
    .
  
  echo "✅ Built $IMAGE_NAME:$VERSION"
  echo ""
done

echo "🎉 All images built successfully!"
echo ""
echo "Images created:"
docker images | grep "talos-" | head -8
