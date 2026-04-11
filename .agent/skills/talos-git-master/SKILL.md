---
name: talos-git-master
description: Use when managing Git history, preparing PRs, or resolving merge conflicts. This skill enforces Talos commit standards and cleanliness.
---

# Talos Git Master

Use this skill to maintain a clean and professional project history.

Load these first:
- `../../../CONTRIBUTING.md`
- `../../../AGENTS.md`
- `../planning/project-history.md`

Workflow:
1. **Status:** Run `git status` and `git diff` to understand the current
   state of the workspace.
2. **Commit:** Draft a clear, concise commit message following the
   Conventional Commits style (e.g., `feat(core): ...`, `fix(perf): ...`).
3. **Sign-off:** Ensure all commits are signed off (`git commit -s`) for DCO
   compliance.
4. **Cleanup:** Review the commit history and squash or rebase if needed to
   maintain a clean narrative.
5. **PR Prep:** Prepare the PR description with a summary, impact analysis,
   and testing notes.

Non-negotiables:
- No commits without sign-off.
- No vague or unprofessional commit messages.
- No large, unorganized commits; prefer smaller, logical changes.
- No submodule pointer changes without an explicit explanation.

Done checklist:
- Changes staged and reviewed.
- Commit messages follow the project style.
- All commits are signed off.
- Final summary includes the commit hash and PR draft link.
