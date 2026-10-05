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

## Synthetic prompt/context bench (P2.3)

Run `agent-os orchestrate context-bench` to measure prompt and context economy
over the synthetic fixtures. `--corpus` selects the compiler and skill
selection cases (default `tests/fixtures/economy-corpus.json`); `--handoffs`
selects handoff fixtures (default `tests/fixtures/economy-handoffs.json`);
`--project` selects the project context (default `personal-agent-os`);
`--budget` sets the context token budget (default `1200`); repeat `--run-dir`
to include telemetry coverage for run directories; and `--out` writes the
report JSON to a file. With no `--run-dir`, telemetry coverage is omitted
(`null`).

The report has four parts: compiler and skill-selection measurements for each
corpus case; worker, reviewer, and planner prompt sizes, including cacheable
shared-prefix tokens measured by `agent_os.orchestrator.prompt_measure`; handoff
compaction measured by `agent_os.economy.handoff_compaction_report`; and
optional telemetry coverage from `context_economy`. The bench makes no model
or provider call. Its report contains only integers, labels, and case IDs. Use
it as the baseline when comparing future prompt and context changes.

### Baseline comparison

Save a baseline with `agent-os orchestrate context-bench --out baseline.json`.
After a prompt-template or retrieval-query change, run
`agent-os orchestrate context-bench --baseline baseline.json` and optionally
add `--fail-on-regression`. The report gains a `comparison` object with schema
`personal-agent/orchestrator-context-bench-compare/v1`; its `metrics` list
records baseline, current, delta, and status for compiler selective tokens and
tokens avoided, total prompt tokens overall and per role, cacheable prefix
tokens, handoff compacted tokens and tokens avoided, and the compiler
all-within-budget flag. Its `regressions` list names worsened metrics.
`--fail-on-regression` exits with status 1 when that list is nonempty. A
baseline with a different schema is rejected. The comparison makes no model
call.

### Handoff value compaction

`_compact_handoff` keeps only `created_at`, `completed`, `decisions`,
`remaining`, and `validation`. It normalizes whitespace in string values and
string list items, drops empty items and exact duplicates (keeping the first
occurrence and preserving order), and omits keys left empty. This applies to
the compiled context packet's latest handoff and the `handoffs` section of
`agent-os orchestrate context-bench`; save a baseline before the change and
rerun `context-bench --baseline <file>` to see `handoffs.compacted_tokens`
reported as improved.

Compaction never truncates text, caps list length, or moves items between
keys. Lossy limits such as truncation, per-key caps, and dropping `remaining`
items already completed are not implemented.
