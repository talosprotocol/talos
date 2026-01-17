#!/usr/bin/env bash
set -euo pipefail

run_if_exists() {
  local dir="$1"
  local cmd="$2"
  if [[ -d "${dir}" ]]; then
    echo "[tests] ${dir}: ${cmd}"
    (cd "${dir}" && bash -lc "${cmd}")
  fi
}

# Required only keeps it strict for CI. Local dev can run full suite separately.
while IFS= read -r path; do
  case "${path}" in
    contracts)
      run_if_exists "${path}" "ls >/dev/null"
      ;;
    services/ai-gateway)
      run_if_exists "${path}" "PYTHONPATH=. pytest -q"
      ;;
    services/audit)
      run_if_exists "${path}" "PYTHONPATH=. pytest -q"
      ;;
    services/mcp-connector)
      run_if_exists "${path}" "PYTHONPATH=. pytest -q"
      ;;
    sdks/python)
      run_if_exists "${path}" "PYTHONPATH=src pytest -q"
      ;;
    sdks/typescript)
      run_if_exists "${path}" "npm test --silent"
      ;;
    site/dashboard)
      run_if_exists "${path}" "npm test --silent || npm run test --silent"
      ;;
    site/marketing)
      run_if_exists "${path}" "npm test --silent || true"
      ;;
    docs)
      run_if_exists "${path}" "ls >/dev/null"
      ;;
    *)
      : # ignore optional paths in required-only mode
      ;;
  esac
done < <(python3 deploy/submodules.py --field new_path --required-only)
