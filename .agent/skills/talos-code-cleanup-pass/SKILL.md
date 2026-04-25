---
name: talos-code-cleanup-pass
description: Coordinate a comprehensive, low-risk codebase cleanup across 7 focused tracks (Deduplication, Type Consolidation, Dead Code, Circular Deps, Type Strengthening, Error Handling, Deprecated/AI Slop). Use when the user wants a systematic quality pass that prioritizes high-confidence fixes and rigorous validation.
---

# Talos Code Cleanup Pass

This skill coordinates a 7-track cleanup pass to improve code quality while maintaining system integrity.

## Workflow

For each track below, follow this iterative process:
1. **Inspect**: Use specialized tools and scripts to scan the codebase.
2. **Assess**: Write a critical assessment of findings.
3. **Rank**: Categorize findings by confidence level (High/Medium/Low).
4. **Implement**: Apply ONLY High-confidence, low-risk fixes.
5. **Verify**: Run build, lint, and type checks after every batch.

## The 7 Cleanup Tracks

### 1. Deduplication
Activate `talos-deduplication-agent`.
Scan for repeated logic and redundant abstractions. Consolidate only where it genuinely simplifies without obscuring intent or crossing boundaries.

### 2. Type Consolidation
Activate `talos-type-consolidation-agent`.
Merge scattered or drifted type definitions into single sources of truth, preferring `contracts/` for protocol shapes.

### 3. Dead Code Removal
Activate `talos-dead-code-removal-agent`.
Use `knip` or `ruff` to find unused exports/variables. Manually verify against dynamic imports and config references before removal.

### 4. Circular Dependencies
Activate `talos-circular-dependencies-agent`.
Map the dependency graph (e.g., using `madge`). Untangle harmful cycles by extracting shared logic into neutral modules.

### 5. Type Strengthening
Activate `talos-type-strengthening-agent`.
Replace placeholder `any` or `unknown` types with strong, researched types from contracts or runtime usage.

### 6. Error Handling Cleanup
Activate `talos-error-handling-cleanup-agent`.
Audit try/catch blocks. Remove silent swallowing and "just-in-case" defaults that mask real failures. Preserve real recovery/audit boundaries.

### 7. Deprecated Code and AI Slop
Activate `talos-deprecated-code-cleanup-agent`.
Remove clearly obsolete legacy paths and AI-generated narrative comments. Rewrite useful comments for technical clarity.

## Guardrails
- **Safety First**: Implement ONLY high-confidence changes.
- **Surgical Edits**: Keep cleanup patches narrow and focused.
- **Validation**: Never skip post-cleanup checks.
