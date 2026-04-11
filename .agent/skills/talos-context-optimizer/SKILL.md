---
name: talos-context-optimizer
description: Use when the conversation history is long or complex. This skill helps identify the most important context to keep and what can be compressed or removed to maintain performance and reduce token costs.
---

# Talos Context Optimizer

Use this skill to keep the session fast, efficient, and focused on the current
task.

Load these first:
- `../planning/program-anchor-index.md`
- `../planning/project-history.md`

Workflow:
1. **Analyze:** Identify the key accomplishments, open questions, and
   decisions made in the current session.
2. **Summarize:** Create a concise summary of the session's progress. Use the
   `save_memory` tool for long-term project facts.
3. **Compress:** Identify redundant or low-signal tool outputs that can be
   omitted from future turns.
4. **Refocus:** Clear any transient state or data that is no longer needed
   for the current goal.

Non-negotiables:
- Do not lose critical project context or decisions.
- Do not clear facts that are still needed for the active task.
- Do not compromise accuracy for the sake of brevity.

Done checklist:
- Session progress summarized and key decisions recorded.
- Redundant context identified and compressed.
- Project-level facts saved to memory (`project` scope).
- Final summary calls out what was preserved and what was optimized.
