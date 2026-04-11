---
name: talos-notepad
description: Use when you need to store persistent notes, track progress across sessions, or maintain a local "project memory" for the current workspace.
---

# Talos Notepad

Use this skill to keep the session focused and ensure long-term task
persistence.

Load these first:
- `../planning/project-history.md`
- `../../../AGENTS.md`

Workflow:
1. **Note:** Capture important decisions, findings, or open questions from
   the current session.
2. **Store:** Use the `save_memory` tool with the `project` scope to persist
   these facts.
3. **Recall:** At the beginning of a new session, read the stored memory to
   rehydrate the current task context.
4. **Prune:** Regularly review and remove obsolete or redundant notes to keep
   the notepad high-signal.

Non-negotiables:
- Do not store secrets or PII in the notepad.
- Do not use the notepad for transient session data (use session history instead).
- Do not lose critical task-related context or decisions.

Done checklist:
- Persistent project memory updated with current session notes.
- Key decisions and findings recorded for future use.
- Final summary includes what was added to the notepad.
