# Talos TUI Contracts

This directory does **NOT** contain source-of-truth schemas. 

The authoritative schemas are located in the `talos-contracts` repository (or `contracts/` in the monorepo) under `schemas/ui/v1`.

## Local Validation

The TUI's Domain Models (`src/talos_tui/domain/models.py`) must remain compatible with the upstream schemas.

Run the interop check:
```bash
../ci/scripts/check_interop.sh
```
