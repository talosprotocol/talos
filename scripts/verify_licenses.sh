#!/bin/bash
echo "DEPRECATED: scripts/verify_licenses.sh has moved to scripts/bash/verify_licenses.sh" >&2
exec "$(dirname "$0")/bash/verify_licenses.sh" "$@"
