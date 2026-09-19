---
name: resume-from-checkpoint
description: Resume a staged project from persisted checkpoint state without rediscovering completed work or reloading the full previous conversation.
---

# Resume From Checkpoint

Use when continuing a staged workflow in a new chat, model, computer, or agent.

1. Resolve the project and locate the latest valid workflow/stage checkpoint.
2. Verify checkpoint identity, stage status, artifacts, and validation outcome.
3. Treat validated completed stages as complete unless:
   - required inputs changed;
   - a dependency/version invalidated the result;
   - the stored validator failed;
   - the user explicitly requests rework.
4. Do not rescan repositories, files, archives, documents, or prior conversations simply to reconstruct history already present in the checkpoint.
5. Compile only the context required for the next incomplete stage.
6. Load the matched stage skill or instructions only when needed.
7. Surface unresolved blockers before starting expensive work.
8. Continue from the exact next stage and preserve the existing workflow id/provenance.
9. After material work, create a new stage-completion handoff.

If no valid checkpoint exists, fall back to project context compilation and create one rather than pretending prior state is known.
