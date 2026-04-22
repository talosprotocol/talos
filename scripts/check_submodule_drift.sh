#!/bin/bash
echo "DEPRECATED: scripts/check_submodule_drift.sh has moved to scripts/bash/check_submodule_drift.sh" >&2
exec "$(dirname "$0")/bash/check_submodule_drift.sh" "$@"
