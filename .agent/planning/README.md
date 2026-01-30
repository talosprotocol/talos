# Planning Documents

Historical planning documents and architecture decisions for Talos Protocol.

## Documents

- **[program-anchor-index.md](program-anchor-index.md)** - Program anchor and anti-drift rules
- **[project-history.md](project-history.md)** - What we decided, and why
- **[gap-analysis.md](gap-analysis.md)** - Plan vs reality, and what is missing
- **[mvp-completion.md](mvp-completion.md)** - MVP backend completion plan
- **[a2a-multi-architecture.md](a2a-multi-architecture.md)** - A2A and multi-party communication design
- **[a2a-architecture.md](a2a-architecture.md)** - Mermaid diagrams for A2A session flow and data flow
- **[tga-plan.md](tga-plan.md)** - Talos Governance Agent (repo layout, runtime, supervisor)

---

## Anti-Drift Rules

From [program-anchor-index.md](program-anchor-index.md):

1. **Contract-first** - talos-contracts is the source of truth
2. **No cross-repo deep links** - Boundaries cross only via published artifacts
3. **Determinism and vectors** - Test vectors for all critical behavior
4. **Audit everywhere** - Gateway operations must emit audit events
5. **Identity strictness** - Strict schemas, UUIDv7, no nulls
6. **CI as a gate** - Schema validation and drift checks required to merge

---

See [../README.md](../README.md) for full .agent directory navigation.
