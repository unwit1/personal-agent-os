# Skill and economy regression safeguards

P0.6 guards the economy layer with deterministic tests instead of provider
calls. `skills.match()` accepts a `minimum_score`; compiled context uses `2`,
so a single incidental word cannot inject an irrelevant skill. Direct callers
may choose a different threshold when their use case requires it.

`agent_os.economy.context_economy_report()` turns existing compiler diagnostics
into a compact baseline: selective and naive token estimates, avoided tokens,
budget status, matched-skill count, whether skill bodies were loaded, and model
calls (always zero for this deterministic measurement).

Regression coverage includes a fixed synthetic corpus for scanner debugging,
Drive crawling, iCloud import, artifact/ZIP generation, focused code fixes,
and research-heavy tasks. It asserts active and dormant skills across SIMPLE,
PLANNED, and STAGED work; also covers weak-match omission, 200 unrelated
synthetic skills, exact-match preservation, metadata-only loading, match-count
limits, and packet-budget compliance.

`classify_complexity()` takes observable structured facts and chooses the
smallest of SIMPLE, PLANNED, or STAGED. Workflow tests cover the paired policy:
valid cache and approved-skill routes precede model handoff, completed cheap
stages are not rerun, and validation failures preserve partial outputs while
escalating only the unresolved stage.

`compare_economy_paths()` evaluates privacy-safe synthetic A/B measurements:
context, model calls, repeated work, retries, escalations, wall-clock time,
capability class, and validation result. Savings count only with validation
parity; a validating path without a saving is explicitly reported as a
justified stronger route. It is intentionally a local test harness; provider
usage and latency telemetry remain later, privacy-safe roadmap work.
