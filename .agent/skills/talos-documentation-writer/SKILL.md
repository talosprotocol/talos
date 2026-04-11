---
name: talos-documentation-writer
description: Use when writing or updating Talos documentation, API references, or guides. This skill ensures clarity, consistency, and accuracy across the project's documentation.
---

# Talos Documentation Writer

Use this skill to maintain high-quality documentation that is useful for both
users and developers of the Talos Protocol.

Load these first:
- `../../../docs/README.md`
- `../planning/program-anchor-index.md`
- The closest module `AGENTS.md`

Workflow:
1. **Research:** Understand the feature or topic thoroughly. Use
   `talos-research-first` if needed.
2. **Structure:** Use the existing templates and structure in `docs/`.
3. **Clarity:** Use clear, professional language. Explain the "why" before
   the "how".
4. **Accuracy:** Verify all code snippets, CLI commands, and API references
   against the current implementation.
5. **Consistency:** Follow the project's style and terminology guidelines.
6. **Parity:** Ensure internal implementation matches the public docs. Use
   `talos-docs-parity` for verification.

Non-negotiables:
- No stale or inaccurate docs.
- No undocumented public APIs or CLI flags.
- No broken links in documentation files.
- No formatting inconsistencies in Markdown files.

Done checklist:
- Documentation updated or created with clear, accurate content.
- Code snippets and commands verified.
- Broken links checked and fixed.
- Style and consistency guidelines followed.
- Final summary includes the scope and impact of the documentation changes.
