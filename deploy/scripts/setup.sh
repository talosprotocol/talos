#!/usr/bin/env bash
set -euo pipefail

python3 -c 'import sys; print(sys.version)' >/dev/null

echo "[setup] syncing submodules..."
git submodule sync --recursive

echo "[setup] init/update submodules (manifest order)..."
while IFS= read -r path; do
  echo "  -> ${path}"
  git submodule update --init --recursive "${path}"
done < <(python3 deploy/submodules.py --field new_path)

echo "[setup] done"
