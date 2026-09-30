# Context Efficiency & Token Amplification

Status: **operator-requested, high priority**  
Owner: Orchestrator OS  
Tracked improvement: **IMP-0018**  
Requested: 2026-09-29

## Why this matters

Long-running agent sessions can become disproportionately expensive because
previous conversation, tool output, repository excerpts, worker reports, and
review history may be reprocessed on many later calls. A conversation that grows
linearly can therefore create roughly quadratic cumulative input-token work, and
multi-agent fan-out, retries, and review loops can multiply that further.

This is a cost, latency, context-window, and model-quality problem. Orchestrator
should measure it directly and optimize it only where evidence shows a real win.

Existing Agent OS evidence already supports the direction: focused delegate
attachments reduced tokens and latency by roughly 68% at equal measured
accuracy (EVR-0013 / DEC-0018). Treat that as a starting observation, not as a
universal expected result.

## High-priority objective

Build a measurable context-economy layer that minimizes repeated model input
while preserving or improving validated task outcomes.

The system should prefer:

1. no model call when deterministic work suffices;
2. the smallest truthful task-specific context packet;
3. references/retrieval instead of accumulated raw history;
4. compact structured stage outputs instead of full upstream transcripts;
5. checkpoint/resume from canonical state instead of conversation replay;
6. deduplicated tool/file content;
7. provider prompt caching when stable context genuinely must repeat;
8. larger context windows only when retrieval/compaction cannot safely preserve
   required information.

Do not optimize token count in isolation. Correctness, validation, latency,
retries, and cost per successful result remain separate dimensions.

## Core measurements

Record these per call, stage, worker, and complete run where available:

- input tokens;
- cached input tokens / cache-hit ratio;
- output tokens;
- unique source tokens represented;
- repeated source tokens represented;
- context packet size;
- cumulative input tokens;
- tool-result tokens;
- file-content tokens;
- prior-turn/history tokens;
- worker-report tokens;
- number of model calls;
- fan-out factor;
- retry/repair count;
- latency;
- monetary cost or relative cost;
- validator outcome;
- review findings / repair burden.

Derived metrics:

### Context amplification

```text
total model input tokens processed
----------------------------------
unique source tokens needed by run
```

This reveals how many times useful source information is effectively re-read.

### Cumulative-context growth

Track cumulative input against:
- number of agent turns;
- elapsed run duration;
- number of workers;
- number of tool calls;
- number of retries/reviews.

Fit/report linear vs superlinear growth rather than assuming a shape.

### Context efficiency

```text
validated useful context
------------------------
total context processed
```

Where "useful" cannot be measured directly, approximate it through controlled
ablation/removal experiments and unchanged validator outcomes; label estimates
as estimates.

### Token churn

Measure how much context enters a call only because it was present in previous
turns but is neither referenced nor necessary for the current stage.

### Fan-out duplication

Measure repeated parent context copied to multiple parallel workers.

### Tool-output re-read cost

Track how many later calls continue to carry large logs, test output, search
results, or file bodies after their durable result could have been summarized.

## Test suite

Create a dedicated CONTEXT-ECONOMY evaluation family using deterministic or
sanitized fixtures first.

### A. Long-session growth benchmark

Run equivalent synthetic workflows at increasing lengths (for example 5, 10,
25, 50, 100 stages where practical) and record:

- final context size;
- cumulative input;
- context amplification;
- latency;
- cost;
- validation result.

The test should make superlinear cumulative usage visible.

### B. Raw history vs compiled context

Compare:

1. broad accumulated history;
2. current Agent OS context compiler;
3. task-specific retrieval + compact Task Context Contract.

Use identical objectives and validators.

### C. Tool-output retention

Inject large deterministic logs/file outputs, then compare:
- raw retention;
- extracted findings + reference;
- bounded excerpts;
- discard-after-durable-state.

Verify that later stages can still diagnose failures.

### D. Multi-agent fan-out

Compare giving every worker the parent packet vs compiling a separate minimal
packet per worker. Measure total tokens, latency, task success, and review
findings.

### E. Review/repair loops

Measure whether reviewers need full worker histories or only:
- task contract;
- changed artifacts/diff;
- validator evidence;
- compact implementation summary.

### F. Checkpoint vs conversation replay

Resume the same staged job using:
- full prior conversation;
- canonical checkpoint + targeted retrieval.

Measure outcome equivalence and token difference.

### G. Prompt-cache economics

For providers that expose cache accounting, compare:
- repeated stable prefix without cache;
- cache-eligible stable prefix;
- retrieval that omits the prefix entirely.

Prefer omission when it is safe and materially cheaper; use caching when
repetition is genuinely required.

### H. Context-window scaling

Benchmark representative tasks at progressively larger supplied contexts.
Record whether more context:
- improves results;
- has no measurable effect;
- increases latency/cost;
- increases error or distraction.

Do not treat maximum supported context as the desired operating point.

## Candidate implementation mechanisms

Evaluate, rather than blindly implement:

- per-stage Task Context Contracts;
- file/range-level retrieval;
- content hashes and duplicate suppression;
- semantic/structural deduplication of retrieved chunks;
- stable-source references with lazy fetch;
- durable structured findings instead of copied tool output;
- log/test-output reducers that preserve errors and failing cases;
- rolling conversation state;
- hierarchical summaries with provenance back-links;
- worker-specific context compilation;
- bounded parent-to-child context inheritance;
- compact result contracts for worker-to-foreman communication;
- retrieval budgets by token and source count;
- stale-context expiry;
- context caching keyed by source revision + task family;
- provider prompt-prefix caching;
- checkpoint-first resume;
- automatic context-pressure detection;
- context-window headroom targets;
- automatic recompile/compact before escalating to a larger-context model.

Every compaction must preserve provenance so a later worker can retrieve the
original source when needed.

## Promotion rule

A context optimization should be promoted only when controlled evaluation shows:

- lower cumulative input tokens and/or lower cost/latency;
- validation is noninferior under the repository's eval policy;
- no meaningful increase in retries, repair loops, or reviewer findings;
- provenance/retrievability is preserved;
- resume/recovery remains correct.

If an optimization merely shortens prompts but causes more failed attempts,
repairs, or stronger-model escalations, calculate total cost per successful task
before deciding it is beneficial.

## Router integration

Eventually make context cost part of route selection.

For a candidate route estimate:

```text
expected total cost of success =
  expected input processing
+ expected output
+ expected retries
+ expected review/repair
+ expected tool/model escalation
```

The router should consider:
- context packet size;
- provider cache behavior;
- model context-window requirement;
- expected worker count;
- likely fan-out duplication;
- historical retries for that task family.

A nominally cheaper model can be more expensive if it needs repeated huge
contexts or produces more repair cycles.

## UI / reporting

Add a Context Economy view or section showing:

- total input/output tokens per run;
- cached vs uncached input;
- unique source tokens;
- context amplification ratio;
- largest repeated sources;
- biggest tool-output contributors;
- per-worker context sizes;
- fan-out duplication;
- retry/repair amplification;
- estimated tokens/cost avoided by retrieval/compaction;
- context-window utilization;
- before/after benchmark results.

Flag obvious "token furnaces", such as a large unchanged source being sent to
many workers or retained through many later turns.

## Interfaces

Suggested provider-neutral interfaces:

```text
context.measure
context.compile
context.explain
context.sources
context.dedupe
context.compact
context.pressure
context.cache.plan
context.amplification.report
context.benchmark.run
```

Reuse the existing context compiler, Task Context Contract, telemetry, eval
harness, checkpoints, capability evidence, and usage reporting. Do not create a
second parallel context system.

## Implementation order

### Phase 0 — measurement first
- Add deterministic token/context accounting to existing run telemetry.
- Add context amplification and fan-out-duplication reporting.
- Build synthetic long-session and fan-out benchmarks.
- Establish an incumbent baseline.

### Phase 1 — low-risk reductions
- Deduplicate identical file/tool payloads.
- Stop carrying durable tool output after its structured result is recorded.
- Tighten worker-specific context compilation.
- Prefer checkpoint + targeted retrieval on resume.

### Phase 2 — controlled compaction
- Add provenance-preserving hierarchical/rolling summaries where measured.
- Add context-pressure-triggered recompilation.
- Test bounded worker result contracts.

### Phase 3 — cache-aware routing
- Capture provider cache accounting when available.
- Compare cache vs omission vs retrieval.
- Include effective context cost in route economics.

### Phase 4 — adaptive optimization
- Learn context budgets by task family from measured successful runs.
- Automatically choose context strategy from evidence.
- Continuously regression-test quality as models/context windows change.

## Immediate instruction to the running Orchestrator agent

Treat IMP-0018 as a **high-priority measurement and optimization track** that
can proceed alongside the current model-infrastructure work.

Start with Phase 0 because it requires no paid compute and can expose whether
the expected savings exist in real Orchestrator runs. Reuse EVR-0013/DEC-0018
as prior evidence, then establish broader baselines.

If benchmarks show material token/cost/latency reductions with noninferior
validation, implement the lowest-risk winning mechanisms and record an EXP/EVR/
DEC for each promoted change. If a technique does not improve total cost per
validated success, reject or defer it rather than adding complexity.

Keep the work resumable and leave a checkpoint/status update after a material
slice.


## Related high-priority experiment: episodic agent rotation

See [episodic-agent-rotation.md](episodic-agent-rotation.md) (IMP-0019). That
track tests whether Orchestrator should terminate context-heavy workers at
semantic boundaries and start fresh task-scoped workers with structured
handoffs and targeted retrieval. It must measure bootstrap, handoff,
rediscovery, retry, and coordination costs as well as tokens avoided, and must
identify the diminishing-return/break-even region before automatic rotation is
promoted.
