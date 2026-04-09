# Parallelization Checklist

Use this checklist during the parallelization pass.

## 1. Safe to parallelize

- Repo discovery and file reads
- Disjoint code edits in different modules with no shared generated output
- SDK parity work split by language when the contract is already fixed
- Docs updates after the behavior or contract is fixed
- Independent test suites that do not share one runtime fixture

## 2. Keep serial

- Two lanes touching the same file
- Schema or contract edits before the boundary is frozen
- Code generation followed by consumer updates
- One shared local server, port, database, or mutable fixture
- Migrations, release-manifest updates, or dependency lockfile edits
- Final integration, formatting, and user summary

## 3. Required lane fields

- `goal`: what this lane changes
- `owner`: primary Talos skill or specialist agent
- `inputs`: assumptions or prerequisite outputs
- `writes`: files or directories it may edit
- `verify`: smallest command that proves the lane is correct
- `done`: condition for merging back

## 4. Monitoring rules

- Poll for overlap in files, contracts, and test fixtures
- Stop a lane if its prerequisite changed underneath it
- Collapse to serial execution when overlap appears
- Re-run shared verification after merging all lane outputs
