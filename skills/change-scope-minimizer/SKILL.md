---
name: change-scope-minimizer
description: Minimize coding and configuration changes to the smallest coherent file and behavior scope required to satisfy the task and validation.
---

# Change Scope Minimizer

Use before editing a repository or configuration.

1. Identify the exact behavior that must change.
2. Locate the smallest set of files, functions, schemas, tests, or configuration entries that control that behavior.
3. Preserve unrelated code and uncommitted work.
4. Avoid broad refactors, repository-wide rewrites, dependency upgrades, or formatting changes unless they are required for correctness.
5. Add or update the narrowest useful tests.
6. Expand scope only when validation proves the smaller change is insufficient.
7. Record any intentionally deferred cleanup separately rather than bundling it into the current task.

The objective is lower review/context cost and lower regression risk, not minimal line count at any price.
