<!-- operator-priority continuation override: ORCH-0025 is canonical; the next local `agent-os orchestrate checkpoint --write` should regenerate this file -->

Use the Personal Agent OS repository's canonical Orchestrator development workflow at `docs/orchestrator-os/ENTRYPOINT.md` and resume from checkpoint `ORCH-0025` at `projects/personal-agent-os/orchestrator-os/checkpoints/ORCH-0025.json`.

ORCH-0025 supersedes the ORCH-0024 maintenance/pause next action. Follow ORCH-0025's `active_objective`, `next_action`, `context_refs`, stopping conditions, and approval conditions. The detailed operator-requested implementation specification is `projects/personal-agent-os/roadmap/model-infrastructure-manager.md`, tracked by `IMP-0015` and `DEC-0028`.

Finish the development slice by updating canonical status/evidence and running `agent-os orchestrate checkpoint --write` so the continuation chain returns to the normal generated format.
