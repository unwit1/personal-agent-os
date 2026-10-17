# Canonical agent policy

Use Personal Agent OS as a routing and context layer, not as an excuse to load
all available history.

1. Identify the target project and inspect its Git state before meaningful work.
2. Compile a focused task packet and load only matched project context and skills.
3. Treat project-local policies as authoritative for that project.
4. Preserve unrelated work and respect privacy, secret, and data boundaries.
5. Prefer deterministic checks and scripts before model review.
6. Record only durable, evidenced knowledge; proposed memories begin as candidates.
7. Create a handoff after meaningful work, including validation and remaining risk.
8. Do not commit or push unless the current user request authorizes it.
9. During technical work, capture durable changes and improvements only as compact,
   deduplicated candidates with evidence references; they remain hypotheses until tested.
10. Form intake may retain sanitized template fingerprints only. Never store source
    documents, completed values, raw OCR, or personal data; Google is not its fallback.
11. Orchestrator development and Agent OS self-improvement follow Orchestrator OS:
    start at `docs/orchestrator-os/ENTRYPOINT.md`; rules are in
    `policy/orchestrator-os.policy.json`; the protected control/evaluation plane is
    enforced by `src/agent_os/orchestrator/control_plane.py`. Agent OS owns durable
    state; models provide temporary cognition.
12. Open-source prior art is a required input to significant Orchestrator design
    decisions: consult `projects/personal-agent-os/research/prior-art/` (proportional
    to the change) before new subsystems or dependencies, prefer subsuming over
    depending, and record what was checked in the decision.
13. Every model failure is a defect to remove, not noise. Apply the deterministic
    remedy, record the failure, and fix what has no remedy or keeps recurring
    (`policy/orchestrator-os.policy.json` `failure_learning`; the orchestrator does
    this automatically via `agent-os orchestrate learn`). When you hit a worker
    failure by hand, add its remedy and a regression test the same way.

Raw transcripts and broad history are archival sources, not default prompt input.
Derived indexes must remain disposable and rebuildable from canonical Git state.
