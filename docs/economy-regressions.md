# Skill and economy regression safeguards

P0.6 guards the economy layer with deterministic tests instead of provider
calls. `skills.match()` accepts a `minimum_score`; compiled context uses `2`,
so a single incidental word cannot inject an irrelevant skill. Direct callers
may choose a different threshold when their use case requires it.

`agent_os.economy.context_economy_report()` turns existing compiler diagnostics
into a compact baseline: selective and naive token estimates, avoided tokens,
budget status, matched-skill count, whether skill bodies were loaded, and model
calls (always zero for this deterministic measurement).

Regression coverage includes weak-match omission, 200 unrelated synthetic
skills, exact-match preservation, metadata-only skill loading, match-count
limits, and packet-budget compliance. It is intentionally a local test harness;
provider usage and latency telemetry remain later, privacy-safe roadmap work.
