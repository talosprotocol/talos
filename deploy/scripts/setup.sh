#!/usr/bin/env bash
set -euo pipefail

MODE="strict"
FORCE_UPDATE=0

usage() {
  cat <<'EOF'
Usage: ./deploy/scripts/setup.sh [--strict|--lenient] [--force]

  --strict   Fail on the first submodule error (default)
  --lenient  Continue past individual submodule errors and report them at the end
  --force    Force checkout of pinned submodule commits to repair broken worktrees
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      MODE="strict"
      ;;
    --lenient)
      MODE="lenient"
      ;;
    --force)
      FORCE_UPDATE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[setup] unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

python3 -c 'import sys; print(sys.version)' >/dev/null

echo "[setup] syncing submodules..."
git submodule sync --recursive

echo "[setup] init/update submodules (manifest order)..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
update_args=(submodule update --init --recursive)
if [[ "$FORCE_UPDATE" -eq 1 ]]; then
  update_args+=(--force --checkout)
fi

failures=()
while IFS= read -r path; do
  echo "  -> ${path}"
  if ! git "${update_args[@]}" "${path}"; then
    if [[ "$MODE" == "strict" ]]; then
      exit 1
    fi
    failures+=("${path}")
  fi
done < <(python3 "$ROOT_DIR/deploy/submodules.py" --field new_path)

if [[ "${#failures[@]}" -gt 0 ]]; then
  echo "[setup] completed with submodule failures:" >&2
  for path in "${failures[@]}"; do
    echo "  - ${path}" >&2
  done
  if [[ "$MODE" == "strict" ]]; then
    exit 1
  fi
fi

echo "[setup] done"
