#!/bin/bash
set -e

# Talos Protocol - Developer Environment Setup
# Sets up pyenv for Python and nvm for Node.js to ensure isolated environments

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/../.."

# Required versions
PYTHON_VERSION="3.12.2"
NODE_VERSION="20.11.0"

echo "=================================================="
echo "  Talos Protocol - Developer Environment Setup    "
echo "=================================================="
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

command_exists() {
    command -v "$1" &>/dev/null
}

print_step() {
    echo ""
    echo "[$1] $2"
}

print_success() {
    echo "    ✅ $1"
}

print_warning() {
    echo "    ⚠️  $1"
}

print_error() {
    echo "    ❌ $1"
}

# ============================================================================
# 1. Install pyenv (Python Version Manager)
# ============================================================================

print_step "1/5" "Setting up pyenv..."

if command_exists pyenv; then
    print_success "pyenv already installed: $(pyenv --version)"
else
    echo "    Installing pyenv via Homebrew..."
    
    if ! command_exists brew; then
        echo "    Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install pyenv pyenv-virtualenv
    
    # Add to shell config
    SHELL_RC=""
    if [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    
    if [[ -n "$SHELL_RC" ]] && ! grep -q 'pyenv init' "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# pyenv configuration" >> "$SHELL_RC"
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$SHELL_RC"
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> "$SHELL_RC"
        echo 'eval "$(pyenv init -)"' >> "$SHELL_RC"
        echo 'eval "$(pyenv virtualenv-init -)"' >> "$SHELL_RC"
        print_success "Added pyenv to $SHELL_RC"
    fi
    
    # Source for current session
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    print_success "pyenv installed"
fi

# ============================================================================
# 2. Install Python via pyenv
# ============================================================================

print_step "2/5" "Installing Python ${PYTHON_VERSION}..."

if pyenv versions | grep -q "$PYTHON_VERSION"; then
    print_success "Python ${PYTHON_VERSION} already installed"
else
    echo "    This may take a few minutes..."
    pyenv install "$PYTHON_VERSION"
    print_success "Python ${PYTHON_VERSION} installed"
fi

# Set as local version for the project
cd "$ROOT_DIR"
pyenv local "$PYTHON_VERSION"
print_success "Set Python ${PYTHON_VERSION} as local version for project"

# ============================================================================
# 3. Install nvm (Node Version Manager)
# ============================================================================

print_step "3/5" "Setting up nvm..."

export NVM_DIR="$HOME/.nvm"

if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    source "$NVM_DIR/nvm.sh"
    print_success "nvm already installed: $(nvm --version)"
else
    echo "    Installing nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    
    # Load nvm for current session
    source "$NVM_DIR/nvm.sh"
    
    print_success "nvm installed"
fi

# ============================================================================
# 4. Install Node.js via nvm
# ============================================================================

print_step "4/5" "Installing Node.js ${NODE_VERSION}..."

if nvm ls "$NODE_VERSION" &>/dev/null; then
    print_success "Node.js ${NODE_VERSION} already installed"
else
    nvm install "$NODE_VERSION"
    print_success "Node.js ${NODE_VERSION} installed"
fi

nvm use "$NODE_VERSION"
nvm alias default "$NODE_VERSION"

# Create .nvmrc for the project
echo "$NODE_VERSION" > "${ROOT_DIR}/.nvmrc"
print_success "Created .nvmrc with Node ${NODE_VERSION}"

# ============================================================================
# 5. Verify Installation
# ============================================================================

print_step "5/5" "Verifying installation..."

echo ""
echo "    Python: $(python3 --version) [$(which python3)]"
echo "    pip:    $(pip3 --version | cut -d' ' -f1-2)"
echo "    Node:   $(node --version) [$(which node)]"
echo "    npm:    $(npm --version)"
echo ""

# ============================================================================
# Create project virtual environment
# ============================================================================

print_step "EXTRA" "Creating project virtual environment..."

VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    print_success "Created virtualenv at .venv"
else
    print_success "Virtualenv already exists at .venv"
fi

# Install development dependencies
echo "    Installing core dev dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip wheel setuptools
"$VENV_DIR/bin/pip" install pytest pytest-asyncio httpx

print_success "Development dependencies installed"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=================================================="
echo "  ✅ Environment Setup Complete!                  "
echo "=================================================="
echo ""
echo "  Python: ${PYTHON_VERSION} (via pyenv)"
echo "  Node:   ${NODE_VERSION} (via nvm)"
echo "  Venv:   .venv"
echo ""
echo "  To activate the Python environment:"
echo "    source .venv/bin/activate"
echo ""
echo "  To use the correct Node version:"
echo "    nvm use"
echo ""
echo "  Then run the stack:"
echo "    ./scripts/bash/start_stack.sh"
echo ""
echo "=================================================="
