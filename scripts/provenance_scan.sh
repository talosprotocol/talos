#!/bin/bash
echo "DEPRECATED: scripts/provenance_scan.sh has moved to scripts/bash/provenance_scan.sh" >&2
exec "$(dirname "$0")/bash/provenance_scan.sh" "$@"
