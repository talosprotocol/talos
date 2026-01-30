#!/bin/bash
set -e

echo "🔍 Validating paths across CI workflows and scripts..."

ERRORS=0
WARNINGS=0

# Function to check if a path exists
check_path() {
    local path=$1
    local context=$2
    
    if [ ! -e "$path" ]; then
        echo "❌ Invalid path in $context: $path"
        ((ERRORS++))
        return 1
    fi
    return 0
}

# Function to extract paths from YAML files
check_workflow_paths() {
    echo ""
    echo "📋 Checking GitHub Actions workflows..."
    
    for workflow in .github/workflows/*.yml; do
        if [ ! -f "$workflow" ]; then continue; fi
        
        # Extract 'cd' commands and check directories
        grep -oP 'cd\s+\K[^\s;&|]+' "$workflow" 2>/dev/null | while read -r dir; do
            # Skip variables and special cases
            if [[ "$dir" =~ ^\$|^~ ]]; then continue; fi
            
            if [ ! -d "$dir" ]; then
                echo "⚠️  Directory not found in $workflow: $dir"
                ((WARNINGS++))
            fi
        done
        
        # Check for common script paths
        grep -oP '\./scripts/[^\s"]+' "$workflow" 2>/dev/null | while read -r script; do
            if [ ! -f "$script" ] && [ ! -d "$script" ]; then
                echo "⚠️  Script path not found in $workflow: $script"
                ((WARNINGS++))
            fi
        done
    done
}

# Function to check script references in shell scripts
check_script_references() {
    echo ""
    echo "📜 Checking shell script references..."
    
    for script in scripts/**/*.sh scripts/**/*.py; do
        if [ ! -f "$script" ]; then continue; fi
        
        # Check sourced files
        grep -oP 'source\s+\K[^\s]+' "$script" 2>/dev/null | while read -r sourced; do
            if [[ ! "$sourced" =~ ^\$ ]] && [ ! -f "$sourced" ]; then
                echo "⚠️  Sourced file not found in $script: $sourced"
                ((WARNINGS++))
            fi
        done
    done
}

# Function to check submodule paths
check_submodule_paths() {
    echo ""
    echo "📦 Checking submodule paths..."
    
    if [ -f ".gitmodules" ]; then
        # Extract submodule paths and verify they exist
        grep "path = " .gitmodules | sed 's/.*path = //' | while read -r submodule; do
            if [ ! -d "$submodule" ]; then
                echo "❌ Submodule directory not found: $submodule"
                ((ERRORS++))
            fi
        done
    fi
}

# Function to validate package.json file paths
check_package_json_paths() {
    echo ""
    echo "📦 Checking package.json file: dependencies..."
    
    for pkg in site/*/package.json sdks/*/package.json; do
        if [ ! -f "$pkg" ]; then continue; fi
        
        # Extract file: dependencies
        grep -oP '"[^"]+"\s*:\s*"file:\K[^"]+' "$pkg" 2>/dev/null | while read -r dep_path; do
            local full_path="$(dirname "$pkg")/$dep_path"
            if [ ! -d "$full_path" ]; then
                echo "⚠️  Package dependency path not found in $pkg: $dep_path"
                ((WARNINGS++))
            fi
        done
    done
}

# Run all checks
check_workflow_paths
check_script_references
check_submodule_paths
check_package_json_paths

# Summary
echo ""
echo "================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All paths valid!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Found $WARNINGS warnings (non-blocking)"
    exit 0
else
    echo "❌ Found $ERRORS errors and $WARNINGS warnings"
    echo "Please fix invalid paths before proceeding."
    exit 1
fi
