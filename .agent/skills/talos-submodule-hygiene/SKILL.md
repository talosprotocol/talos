---
name: talos-submodule-hygiene
description: Use when classifying dirty Talos worktrees or submodules, separating intentional edits from generated artifacts, or tightening ignore rules without hiding real source changes. Start from git status evidence, produce a cleanup plan, and keep deletions or ignore updates scoped and justified.
---

# Talos Submodule Hygiene

Load these first:
- `../planning/program-anchor-index.md`
- `../../../AGENTS.md`

Use `scripts/classify_dirty_worktree.py` for the first pass when the dirty
surface is larger than a few files or spans submodules.

Workflow:
1. Capture the real dirty surface. Use `git status --short` for the current
   repo and include recursive submodules when the task crosses repo boundaries.
2. Classify each path as `keep`, `clean`, `ignore-candidate`, or
   `inspect-first`. Treat tracked source edits as intentional until proven
   generated.
3. For generated artifacts, name the owning command, build step, or tool
   before proposing cleanup.
4. Prefer the narrowest ignore scope that solves the recurring noise:
   submodule-local ignore before shared root rules, and local excludes for
   machine-specific clutter.
5. Produce a cleanup plan before deleting files or editing ignore rules.
   Include the post-clean verification command.

Helper:
- `python3 .agent/skills/talos-submodule-hygiene/scripts/classify_dirty_worktree.py --repo-path . --submodules --format markdown`
- The helper emits per-repo buckets for tracked changes, generated artifacts,
  ignore candidates, and ambiguous paths that still need review.

Guardrails:
- Do not ignore tracked files to make `git status` look clean.
- Do not delete build output or caches without checking whether an active
  service or test still depends on them.
- Do not widen shared `.gitignore` for a single developer-local artifact when
  `.git/info/exclude` or a submodule-local ignore is enough.
- Do not assume every untracked file is disposable; generated fixtures and
  captured evidence may be intentional.

Done checklist:
- Dirty files grouped by action.
- Generated artifacts mapped to an owning command or tool.
- Ignore recommendations scoped to the correct repo level.
- Verification command listed for the final re-check.
