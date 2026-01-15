#!/usr/bin/env bash
# =============================================================================
# Talos Secret Scanner
# =============================================================================
# Scans staged files for hardcoded secrets, keys, and credentials.
# =============================================================================

set -uo pipefail

echo "🛡️  Scanning for hardcoded secrets..."

# 1. Patterns to detect (Regex)
SECRET_PATTERNS=(
  # 32-byte Hex Key (typical for Master Keys) with variable context
  "(MASTER_KEY|SECRET|API_KEY|TOKEN|PRIVATE_KEY)\s*[:=]\s*[\"'][0-9a-fA-F]{64}[\"']"
  # Common Private Key Headers
  "BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY"
  "BEGIN PGP PRIVATE KEY BLOCK"
  # Generic credentials/passwords assignment (if looks like entropy)
  "(password|passwd|secret|credential)\s*[:=]\s*[\"'][a-zA-Z0-9!@#$%^&*()_+]{16,}[\"']"
)

# 2. Files to check (received as arguments)
FILES=("$@")

if [[ ${#FILES[@]} -eq 0 ]]; then
  # If no files passed, check all staged files
  while IFS= read -r file; do
    if [[ -f "$file" ]]; then
       FILES+=("$file")
    fi
  done < <(git diff --cached --name-only --diff-filter=ACM)
fi

SECRET_FOUND=0

for file in "${FILES[@]}"; do
  # Skip binary files, lockfiles, vectors, and this script itself
  case "$file" in
    *.png|*.jpg|*.gif|*.ico|*.woff*|*.ttf|*.lock|*.log|*.json|*.md|*.csv) continue ;;
    scripts/scan-secrets.sh|redact.txt) continue ;;  # Skip self and redaction temp files
  esac

  if [[ ! -f "$file" ]]; then continue; fi

  for pattern in "${SECRET_PATTERNS[@]}"; do
    # Use grep -E for extended regex
    MATCHES=$(grep -Ei "$pattern" "$file" 2>/dev/null || true)
    
    if [[ -n "$MATCHES" ]]; then
      echo "   ❌ FATAL: Potential secret detected in $file"
      echo "      Pattern: $pattern"
      # Redact the match in output to avoid double exposure in logs
      echo "      Line: $(echo "$MATCHES" | sed 's/[:=].*/[:=] <REDACTED>/')"
      SECRET_FOUND=$((SECRET_FOUND + 1))
    fi
  done
done

if [[ $SECRET_FOUND -gt 0 ]]; then
  echo ""
  echo "   🛑 Commit blocked: $SECRET_FOUND potential secret(s) found."
  echo "      Never hardcode secrets. Use .env files, environment variables, or secret stores."
  echo "      To skip (emergency only): git commit --no-verify"
  exit 1
fi

echo "   ✅ No secrets detected."
exit 0
