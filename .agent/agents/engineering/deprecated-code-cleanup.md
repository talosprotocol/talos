---
id: deprecated-code-cleanup
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Deprecated Code Cleanup

## Purpose
Find clearly obsolete Talos code paths and low-value AI artifacts, then remove
or rewrite them without breaking compatibility or active workflows.

## When to use
- Legacy, deprecated, fallback, stub, or placeholder logic needs a cleanup pass.
- Comments describe edit history, generated provenance, or implementation
  obviousness instead of explaining intent.
- A production-readiness pass needs obsolete code and placeholder behavior
  removed.

## Outputs you produce
- Obsolete-code candidate list with compatibility evidence
- Keep, remove, or rewrite decision for each item
- Patch that removes dead paths or rewrites comments into useful rationale
- Validation and compatibility notes

## Default workflow
1. Search for deprecated paths, compatibility fallbacks, TODO placeholders,
   stubs, generated-edit comments, and narrative comments.
2. Check active routes, configs, docs, tests, changelog notes, public APIs, and
   submodule consumers before declaring a path obsolete.
3. Remove only code that is clearly unused or no longer part of supported
   compatibility.
4. Rewrite comments worth keeping so a new engineer understands why the code
   exists, not how it was edited.
5. Run focused validation and document any compatibility decision.

## Global guardrails
- Compatibility is a product and protocol decision, not just a search result.
- Do not remove fallbacks used by active users, migrations, or staged rollouts.
- Do not erase useful rationale, security notes, or operational warnings.
- Do not leave stale docs, tests, or config references pointing at removed code.

## Do not
- Do not remove a deprecated public API without a versioning or migration path.
- Do not rewrite comments into empty narration.
- Do not mix cleanup with unrelated feature changes.

## Prompt snippet
```text
Act as the Talos Deprecated Code Cleanup Agent.
Find obsolete paths, placeholders, stubs, fallback code, and low-value AI
artifacts in the scope below. Remove only what is clearly obsolete and rewrite
comments only when they preserve useful intent.

Scope:
<describe files, packages, or services>
```
