#!/bin/bash
echo "DEPRECATED: scripts/docker_build_sdk_tool.sh has moved to scripts/bash/docker_build_sdk_tool.sh" >&2
exec "$(dirname "$0")/bash/docker_build_sdk_tool.sh" "$@"
