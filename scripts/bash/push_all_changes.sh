#!/bin/bash
# scripts/push_all_changes.sh

# List of submodules/directories to check
DIRS=(
	"contracts"
	"core"
	"docs"
	"examples"
	"sdks/go"
	"sdks/java"
	"sdks/python"
	"sdks/rust"
	"sdks/typescript"
	"services/ai-chat-agent"
	"services/ai-gateway"
	"services/aiops"
	"services/audit"
	"services/gateway"
	"services/governance-agent"
	"services/mcp-connector"
	"services/ucp-connector"
	"site/dashboard"
	"site/marketing"
)

ROOT_DIR="$(pwd)"
for dir in "${DIRS[@]}"; do
	echo "---------------------------------------------------"
	echo "Processing ${dir}..."
	if [[ -d ${dir} ]]; then
		cd "${dir}" || exit

		# Get current branch
		BRANCH=$(git rev-parse --abbrev-ref HEAD)
		echo "Current branch: ${BRANCH}"

		# Check for changes
		status_output=$(git status -s)
		if [[ -n ${status_output} ]]; then
			echo "Changes found in ${dir}. Committing and pushing..."
			git add .
			git commit -m "Update ${dir} content"
			git push origin "${BRANCH}"
		else
			# Capture status to avoid pipe masking in conditional
			STATUS_FULL=$(git status)
			if [[ ${STATUS_FULL} == *"ahead of"* ]]; then
				echo "Local commits found in ${dir}. Pushing..."
				git push origin "${BRANCH}"
			else
				echo "No changes in ${dir}."
			fi
		fi
		cd "${ROOT_DIR}" || exit
	else
		echo "Directory ${dir} does not exist."
	fi
done

echo "---------------------------------------------------"
echo "Processing root directory..."
git add .
root_status=$(git status -s)
if [[ -n ${root_status} ]]; then
	git commit -m "Update submodules and root files"
	BRANCH=$(git rev-parse --abbrev-ref HEAD)
	git push origin "${BRANCH}"
else
	echo "No changes in root directory to commit."
	BRANCH=$(git rev-parse --abbrev-ref HEAD)
	git push origin "${BRANCH}"
fi
# Final Quality Check Sync
