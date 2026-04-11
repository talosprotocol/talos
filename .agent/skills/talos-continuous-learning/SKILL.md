---
name: talos-continuous-learning
description: Use at the end of a session or after completing a significant task. This skill helps extract architectural insights, project-specific patterns, and "lessons learned" to be persisted in the project memory.
---

# Talos Continuous Learning

Use this skill to ensure that the AI's "experience" in the Talos codebase is
accumulated and shared across future sessions.

Load these first:
- `../planning/program-anchor-index.md`
- `../planning/project-history.md`

Workflow:
1. **Reflect:** Review the current session's accomplishments, challenges, and
   surprising discoveries (e.g., "The pre-commit hook has a false positive for
   absolute paths in its own source code").
2. **Extract:** Identify reusable coding patterns, specific project
   constraints, or "gotchas" that were encountered.
3. **Persist:** Use the `save_memory` tool with the `project` scope to save
   these lessons. Format them as concise, actionable facts.
4. **Update:** If the discovery significantly impacts the project's
   architecture or history, propose an update to `../planning/project-history.md`.

Non-negotiables:
- Do not persist secrets or PII.
- Do not persist transient data; focus on long-term value.
- Do not repeat facts that are already in the project memory.

Done checklist:
- Session accomplishments reviewed.
- Key lessons learned identified and extracted.
- Actionable facts saved to project memory (`save_memory`).
- Final summary calls out the specific "instincts" or "lessons" learned.
