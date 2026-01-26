#!/bin/bash
set -euo pipefail

# check_submodule_drift.sh
# Purpose: Fail CI if any submodule's pinned SHA differs from origin/main.
# strict mode: ANY mismatch fails.

echo "🔍 Checking for submodule drift..."

# Abort if submodules are not initialized
if ! git submodule status | grep -q "^ "; then
    # If any line starts with '-', it's uninitialized. '^ ' means initialized and clean.
    # Actually 'git submodule status' prints '-' for uninit, '+' for modified, ' ' for clean.
    # We want to fail if uninitialized to prevent false positives/errors.
    if git submodule status | grep -q "^-"; then
        echo "❌ Error: Submodules are not initialized."
        echo "   Run: git submodule update --init --recursive"
        exit 1
    fi
fi

FAILED=0
DRIFT_FOUND=0

# Iterate to get paths. Using 'git config --file .gitmodules --get-regexp path' is robust.
# Or just 'git submodule foreach' but that requires execution.
# Let's use a while loop over 'git submodule status' to catch all
# Format: [status_char][SHA] [path] [(describe)]

echo -e "Path\t\t\t\tPinned SHA\t\tLatest Main SHA"
echo "--------------------------------------------------------------------------------"

while read -r line; do
    status_char=$(echo "$line" | cut -c1)
    pinned_sha=$(echo "$line" | awk '{print $1}' | sed 's/^[+-]//') # Remove status char if present
    path=$(echo "$line" | awk '{print $2}')
    
    # Skip if path is empty
    [[ -z "$path" ]] && continue
    
    # 1. Fetch remote main (without touching working tree)
    # We rely on 'branch = main' config or default to main
    # Actually, we should just fetch 'origin main'.
    
    if ! git -C "$path" fetch -q origin main; then
        echo "❌ $path: Failed to fetch origin main. Check credentials/network."
        FAILED=1
        continue
    fi
    
    # 2. Get remote SHA
    latest_sha=$(git -C "$path" rev-parse refs/remotes/origin/main)
    
    # 3. Compare
    if [[ "$pinned_sha" != "$latest_sha" ]]; then
        echo -e "$path\t$pinned_sha\t$latest_sha ⚠️ DRIFT"
        DRIFT_FOUND=1
    else
        # Optional: Print OK or stay silent for clean output
        :
    fi
    
done < <(git submodule status --recursive)

if [[ $FAILED -eq 1 ]]; then
    echo ""
    echo "❌ Failed to check some submodules."
    exit 1
fi

if [[ $DRIFT_FOUND -eq 1 ]]; then
    echo ""
    echo "❌ Drift detected! The pinned submodules are behind remote main."
    echo "   Resolution: Run the sync workflow or manually update pins."
    exit 1
fi

echo "✅ All submodules matches origin/main."
exit 0
