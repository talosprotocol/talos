# Test Manifests (`.agent/test_manifest.yml`)

Each repository in the Talos ecosystem must include a test manifest to be discovered by the universal test runner.

## Schema Specification

```yaml
# Unique identifier for the repository (used in summary reports)
repo_id: "talos-core-rs"

# Directory containing the source code (relative to manifest)
repo_root: "." 

commands:
  # The script that implements the standardized test contract
  test_entrypoint: "scripts/test.sh"

coverage:
  enabled: true
  # Supported formats: cobertura
  format: "cobertura"
  # Path to the emitted coverage report (standard is artifacts/coverage/coverage.xml)
  report_path: "artifacts/coverage/coverage.xml"
  
  # Global thresholds (0.0 to 1.0)
  thresholds:
    line: 0.80
    branch: 0.70
    
  # High-risk path-specific thresholds (glob patterns)
  path_thresholds:
    "src/crypto/**": { line: 0.95 }
    "src/logic/auth/**": { line: 1.00 }

ci:
  # Default suites to run in CI/pre-commit
  default: ["--smoke", "--unit", "--coverage"]
```

## Standardized Test Contract

The `test_entrypoint` script MUST support following flags:

| Flag | Requirement |
|------|-------------|
| `--smoke` | Quick validation of core paths |
| `--unit` | Complete unit test suite |
| `--integration` | Services and cross-component tests |
| `--coverage` | Unit tests with coverage emission |
| `--ci` | Composite of smoke + unit + coverage |
| `--full` | Everything including integration |

## Discovery Logic

The orchestrator `run_all_tests.sh` performs a shallow scan (depth 5) for files matching `test_manifest.yml`. It strictly expects manifests to live inside a `.agent/` directory within the component root.
