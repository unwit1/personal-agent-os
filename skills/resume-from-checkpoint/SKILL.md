---
name: resume-from-checkpoint
description: Resume a staged project from persisted checkpoint state without rediscovering completed work or reloading the full previous conversation.
---

# Resume From Checkpoint

Use when continuing a staged workflow in a new chat, model, computer, or agent.

1. Resolve the project and locate the latest valid workflow/stage checkpoint.
2. Verify checkpoint identity, stage status, artifacts, and validation outcome.
3. Use `artifact-reuse-check` for referenced outputs before regenerating them.
4. Treat validated completed stages as complete unless required inputs changed, a dependency/version invalidated the result, the stored validator failed, or the user explicitly requests rework.
5. Do not rescan repositories, files, archives, documents, or prior conversations simply to reconstruct history already present in the checkpoint.
6. If the checkpoint is bloated, use `checkpoint-compactor` before compiling model context.
7. Compile only the context required for the next incomplete stage with `context-budgeter`.
8. Surface unresolved blockers before starting expensive work.
9. Apply `cheap-route-first` to the next stage and preserve the existing workflow id/provenance.
10. After material work, create a new stage-completion handoff.

If no valid checkpoint exists, fall back to project context compilation and create one rather than pretending prior state is known.
