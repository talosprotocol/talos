# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Context

This is a submodule of the [Talos Protocol](https://github.com/talosprotocol/talos) multi-repository project.

Main repository: https://github.com/talosprotocol/talos
Documentation: https://github.com/talosprotocol/talos-docs

## About This Component

This submodule contains [specific functionality of this component].

## Development Workflow

Standard Talos development practices apply:

1. Make changes in this submodule
2. Run tests with `scripts/test.sh` if available
3. Validate with the parent repository's test suite
4. Submit changes as PR to this submodule repository
5. Parent repository will update the submodule pin after merge

## Common Commands

```bash
# Run tests (if test script exists)
./scripts/test.sh --unit

# Install dependencies (language specific)
# For Python: pip install -e .
# For Node.js: npm install
# For Rust: cargo fetch
# For Go: go mod download
```

## Integration Points

This component integrates with:
- [List key integration points with other submodules]

## Testing

Each submodule follows the standardized test interface:
- `scripts/test.sh --unit` for unit tests
- `scripts/test.sh --ci` for CI suite
- Reports results to `artifacts/test/results.json`

See main repository CLAUDE.md for orchestrating multi-submodule testing.