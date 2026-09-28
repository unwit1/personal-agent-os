# Meta-Improvement Research Changelog

## 2026-09-24 — MIR-2026-09-24-FOUNDATION-01

Foundational problem-space mapping completed on branch `research/meta-improvement-foundation-20260924`.

### Added

- Research mission and operating principles.
- Machine-readable research manifest.
- 46-entry source index covering agent architecture, orchestration, protocols, durable execution, observability, provenance, evaluation, routing, memory/retrieval, self-improvement, security/authorization, and proactive HCI.
- Eighteen-section foundational architecture pass matching the requested research deliverables.
- 20-item structured improvement backlog.
- 20 explicit open questions plus an unknown-unknown research frontier.
- Initial controlled-improvement object taxonomy and future-model handoff design.

### Key decisions / provisional findings

- Treat the Meta-Improvement Engine as a control plane over existing Agent OS primitives, not a parallel agent framework.
- Treat model reflection/self-critique as a hypothesis generator, not evidence that a change is correct.
- Keep deterministic authorization outside model control.
- Prefer task-specific measured model/tool evidence over a single global intelligence score.
- Preserve the current Git-canonical / local-private-derived-data split.
- Do not adopt a heavyweight workflow engine, graph database, fine-tuning loop, or always-on critic until measurements justify the added complexity.
- Make deletion and simplification explicit improvement outcomes.
- Evaluate the Meta-Improvement Engine by verified user value gained per unit of complexity, cost, risk, and attention.

### Next pass

1. Evaluation registry, task corpus, graders, holdouts, contamination controls, and user-effort metrics.
2. Authorization threat model, capability boundaries, prompt-injection/data-flow controls.
3. Task-specific model/tool capability registry and routing uncertainty.
4. Proactivity and constructive-challenge intervention policy.
5. Simplification/deletion audit system.
6. Durable execution build-vs-adopt threshold analysis.
