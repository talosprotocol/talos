#!/bin/bash
echo "DEPRECATED: scripts/generate_repos_manifest.sh has moved to scripts/bash/generate_repos_manifest.sh" >&2
exec "$(dirname "$0")/bash/generate_repos_manifest.sh" "$@"
