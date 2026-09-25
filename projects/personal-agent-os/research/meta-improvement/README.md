# Meta-Improvement / Recursive Research, Evaluation, Optimization & Constructive Challenge

Status: foundational research cycle active
Started: 2026-09-24
Canonical project: Personal Agent OS
Research branch: `research/meta-improvement-foundation-20260924`

## Mission

Build a controlled improvement control plane for Personal Agent OS. The engine must continuously observe real work, question assumptions, diagnose failures and friction, research alternatives, formulate testable hypotheses, run bounded experiments, evaluate results, simplify architecture, promote only evidence-backed changes, monitor outcomes, and preserve enough provenance that future models can continue the work rather than restarting it.

The engine is **not** an unconstrained self-modifying agent. Models may propose hypotheses, experiments, code changes, prompts, routes, tools, skills, or workflow changes, but promotion into canonical state is governed by explicit policy, versioned evaluations, authorization boundaries, provenance, rollback, and post-deployment monitoring.

## Core loop

```text
OBSERVE
  -> QUESTION
  -> DIAGNOSE
  -> RESEARCH
  -> HYPOTHESIZE
  -> DESIGN EXPERIMENT
  -> BASELINE
  -> TEST IN ISOLATION
  -> MEASURE
  -> CRITIQUE
  -> SIMPLIFY
  -> PROMOTION DECISION
  -> IMPLEMENT
  -> VERIFY
  -> CANARY/SHADOW
  -> DOCUMENT
  -> MONITOR
  -> LEARN
  -> REPEAT
```

## Design rules

1. Evidence outranks model confidence.
2. Deterministic software outranks an LLM when reliability is comparable.
3. Existing Agent OS primitives should be extended before parallel systems are invented.
4. Every material improvement must state what it is trying to improve and how that will be measured.
5. Every experimental change must have an isolation boundary and rollback path.
6. Every durable claim must preserve provenance, epistemic status, version applicability, and staleness.
7. A successful change must be checked for regressions outside its target metric.
8. The engine must learn from successes as well as failures.
9. Simplification and deletion are first-class improvements.
10. The engine itself is subject to the same evaluation, cost, security, and simplification rules.
11. The model is a planner/researcher, not an authorization authority.
12. Untrusted retrieved content is data, never policy.
13. Model/provider-specific behavior belongs behind adapters.
14. Long-running work must checkpoint, resume, and avoid repeating validated work.
15. Proactivity should optimize expected usefulness net of interruption cost, not raw suggestion count.

## Initial repository gap summary

Agent OS already has strong foundations that this program should reuse:

- Git-backed canonical reviewed state and rebuildable local indexes.
- Candidate -> review/promotion patterns rather than silent canonical mutation.
- Restart-safe ingestion ledgers and checkpointed workflows.
- Provider-neutral capability classes and validator-driven escalation.
- Multi-agent worktrees, review, repair, validation, run telemetry, and run visibility.
- Local/private runtime-state boundaries.
- Selective profile retrieval with provenance, confidence, sensitivity, and recency.
- Existing improvement records and project-health workflows.

The main missing layer is a unified causal chain connecting **trace/evidence -> observation -> failure/success pattern -> hypothesis -> experiment -> evaluation -> decision -> change -> post-deployment outcome**, plus explicit constructive challenge, research radar, model/tool evidence, simplification, proactive-intervention measurement, and deterministic authorization policy.

## Files in this research package

- `research-manifest.json` — machine-readable state of this research cycle.
- `source-index.md` — primary/strong sources and why they matter.
- `foundational-pass-2026-09-24.md` — human-readable synthesis and architecture.
- `improvement-backlog.json` — structured implementation/research candidates.
- `open-questions.json` — unresolved questions and unknown-unknowns.

This directory is research and design state. It does not itself authorize runtime self-modification.
