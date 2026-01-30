# Talos .agent Directory

This directory contains the **program anchor** and anti-drift mechanism for the Talos Protocol ecosystem, along with agent definitions and development workflows.

## 📁 Directory Structure

- **[specs/](specs/)** - Phase specifications (locked requirements)
- **[workflows/](workflows/)** - Active development workflows  
- **[agents/](agents/)** - Agent role definitions for the Talos ecosystem
- **[planning/](planning/)** - Historical planning documents and architecture decisions
- **[status/](status/)** - Current project status and completed features
- **[archive/](archive/)** - Deprecated schemas and historical artifacts
- **[perf_contract.yml](perf_contract.yml)** - Performance contract

## 🚀 Quick Links

### Current Status
- [Current Phase](status/current-phase.md) - Where we are now
- [Completed Features](status/completed-features.md) - All completed phases

### Phase Specifications
- [Completed Phases](specs/completed/) - Phases 7, 9.2, 9.3, 10-13, 15
- [Planned Phases](specs/planned/) - Phase 14+ (future work)

### Development Workflows
- [Development Workflows](workflows/development/) - TGA, Dashboard, README workflows
- [Style Guides](workflows/style-guides/) - Documentation standards

### Planning & Architecture
- [Planning Documents](planning/) - Historical planning and decisions
- [Program Anchor Index](planning/program-anchor-index.md) - Anti-drift rules

### Agents
- [Agent Catalog](agents/) - 34 specialized agents across 7 categories

## 🎯 Anti-Drift Rules

1. **Contract-first** - `talos-contracts` is the source of truth
2. **No cross-repo deep links** - Boundaries crossed via published artifacts only
3. **Determinism and vectors** - Test vectors for all critical behavior
4. **Audit everywhere** - All gateway operations emit audit events
5. **Identity strictness** - Strict schemas, UUIDv7, no nulls
6. **CI as a gate** - Schema validation and drift checks required to merge

See [program-anchor-index.md](planning/program-anchor-index.md) for complete rules.

## 📚 Documentation

For public-facing documentation, see the [`docs/`](../docs/) directory in the root repository.

## 🔄 Last Updated

2026-01-29 - .agent folder reorganized with updated phase status (Phases 7-15 complete)
