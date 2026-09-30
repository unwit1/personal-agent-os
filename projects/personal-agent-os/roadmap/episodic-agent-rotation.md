# Episodic Agent Rotation & Context Boundary Scheduler

Status: **operator-requested, high priority experiment**  
Owner: Orchestrator OS  
Tracked improvement: **IMP-0019**  
Depends on: **IMP-0018 Context Efficiency & Token Amplification**  
Requested: 2026-09-29

## Hypothesis

Long-running agent work may be cheaper and cleaner when Orchestrator ends a
worker at natural semantic boundaries, persists only validated artifacts +
structured state, and starts a fresh worker with the minimum task-specific
context needed for the next episode.

The goal is not "spawn more agents." The goal is to determine **when replacing
a context-heavy worker with a fresh worker lowers total cost per validated unit
of work**.

A fresh worker has non-zero bootstrap, retrieval, handoff, and rediscovery
costs. Rotation should happen only when the expected savings from avoiding
stale/repeated context exceed those costs.

## Preferred execution model

```text
canonical project state
        |
        v
context compiler
        |
        v
task episode / worker
        |
        +-- artifact(s)
        +-- decisions
        +-- validator evidence
        +-- remaining work
        +-- provenance / source refs
        |
        v
durable structured handoff
        |
        v
fresh worker for next semantic episode
```

Conversation history is disposable cognition. Durable state is the contract
between episodes.

## What survives a worker

Preserve compact structured state rather than raw reasoning/history:

1. **Artifacts** — code, schemas, documents, tests, generated assets.
2. **Decisions** — what was chosen and why; important rejected alternatives.
3. **State** — completed, remaining, blockers, dependencies.
4. **Evidence** — tests, benchmarks, failures, measurements, review findings.
5. **Pointers** — source/file/record references for lazy retrieval of deeper
   context.

Raw logs and transcripts may remain available locally for diagnosis but should
not automatically enter the next worker's prompt.

## Candidate rotation signals

Measure and test these signals rather than hard-code them initially:

- semantic stage completion (research -> design -> implementation -> review);
- retained-context size;
- estimated relevant-context fraction;
- repeated/stale context fraction;
- number of expected remaining model calls;
- tool/log payload dominating the current window;
- context-window utilization/headroom;
- change in required capability/model for the next stage;
- dependency boundary where downstream work can be expressed as a stable
  contract;
- reviewer/repair transition;
- checkpoint availability and confidence;
- current worker retry/failure rate;
- expected rediscovery cost.

A semantic boundary should generally outrank an arbitrary token threshold.

## Break-even model

Estimate two alternatives for each potential boundary.

### Continue current worker

```text
C_continue =
    expected retained-context tokens across remaining calls
  + new required context
  + expected output
  + expected retries/review/repair
  + latency/cost effects
```

### Rotate to fresh worker

```text
C_rotate =
    worker bootstrap
  + structured handoff
  + targeted retrieval
  + required source context
  + expected rediscovery
  + expected output
  + expected retries/review/repair
  + orchestration overhead
```

Rotate only when expected total validated cost is lower by a meaningful margin.
Do not rotate based on input-token savings alone.

Record prediction vs actual result so the policy can improve.

## Context pressure score

Add an explainable context-pressure calculation using measurable inputs such as:

```yaml
context_pressure:
  current_context_tokens:
  estimated_relevant_tokens:
  relevance_ratio:
  repeated_or_stale_tokens:
  context_window_utilization:
  expected_remaining_calls:
  projected_continue_input:
  estimated_fresh_worker_input:
  bootstrap_overhead:
  handoff_overhead:
  estimated_rediscovery_penalty:
  projected_savings:
  confidence:
  recommendation:
    - continue
    - compact
    - rotate
    - split_parallel
```

The first implementation should be deterministic/heuristic and observable.
Do not build a learned controller until enough real outcomes exist.

## Experiments

Use the same objective, source revision, model capability class, validators, and
budget when comparing strategies.

### EXP-A — continuation vs fresh rotation

Run representative tasks in two modes:

- one persistent worker;
- worker rotation at semantic boundaries.

Measure total input/output, elapsed time, calls, retries, validator result,
review findings, and cost per validated completion.

### EXP-B — rotation frequency curve

Test multiple rotation policies, for example:

- never rotate;
- rotate after every task;
- rotate at every semantic stage;
- rotate at moderate context pressure;
- rotate only at high context pressure.

Plot total cost / tokens / latency / quality. Find the region where additional
rotation stops helping.

### EXP-C — relevant-context fraction

Construct tasks where the next stage needs approximately different fractions of
the current worker's accumulated state (for example 10%, 25%, 50%, 75%, 90%).
Measure where fresh-worker bootstrap stops being worthwhile.

Do not turn those percentages into policy until measured.

### EXP-D — remaining-call horizon

Compare rotation when only 1–2 calls remain versus 5, 10, or many calls remain.
A large stale context is much more expensive when it will be re-read repeatedly.

### EXP-E — structured handoff richness

Compare:
- minimal summary;
- structured decisions/state/evidence/pointers;
- broad transcript inheritance.

Measure rediscovery, errors, retries, and tokens. Determine the minimum durable
handoff that preserves performance.

### EXP-F — progressive disclosure

Compare:
- preload all predicted context;
- start with a small contract and lazily retrieve additional source material;
- broad parent context.

Measure whether lazy retrieval reduces unused context without increasing
failure/rework.

### EXP-G — worker tree depth / fan-out

Measure orchestration overhead as delegation depth increases.

Default experimental guardrail:
- foreman/orchestrator;
- worker;
- optional specialist helper.

Do not allow unrestricted recursive delegation. Test whether deeper trees ever
improve total validated cost before enabling them.

### EXP-H — capability transition boundaries

Test whether switching workers is especially useful when work changes class,
such as research -> coding -> review, because the next worker can receive a
different context contract and model profile.

## Diminishing-return detection

The central question is not "does rotation save tokens?" but:

> At what rotation frequency does marginal savings fall below worker bootstrap,
> coordination, and rediscovery cost?

Track the marginal gain of each additional optimization/rotation level.

Stop increasing rotation frequency when one or more occur:

- total cost per validated completion stops decreasing;
- latency rises materially with little token benefit;
- rediscovery tokens approach the history tokens avoided;
- retry/rework rate increases;
- reviewer findings increase;
- more stages need to fetch the same supposedly omitted context;
- handoff construction itself becomes a large fraction of cost;
- worker count/fan-out grows faster than useful parallel work;
- quality confidence falls or variance increases.

Record the observed break-even region by task family.

## Agent half-life

If evidence supports it, maintain a task-family-specific estimate of useful
worker lifetime, expressed in measurable terms rather than a fixed wall-clock
time:

- calls since episode start;
- unique new context introduced;
- retained-context growth;
- relevance ratio;
- semantic stages crossed;
- expected remaining work.

Examples of future policy outputs:

```text
repository implementation:
  rotate primarily at stage boundaries
  pressure threshold learned from successful runs

research synthesis:
  longer worker lifetime; preserve thematic continuity

mechanical file transformation:
  very short episodes; small contracts

architecture debugging:
  avoid rotation while working state remains highly coupled
```

The term "agent half-life" is a metric/policy concept, not a requirement to
terminate workers on a timer.

## Scheduler behavior

Possible future provider-neutral interfaces:

```text
episode.start
episode.finish
episode.handoff.compile
episode.handoff.validate
episode.rotation.estimate
episode.rotation.explain
episode.context_pressure
episode.policy.evaluate
episode.benchmark.run
```

The scheduler should support four outcomes:

- **continue** — continuity is worth more than context savings;
- **compact** — keep worker but replace bulky transient context with durable
  structured state where the provider/runtime permits;
- **rotate** — checkpoint and start a fresh worker;
- **split_parallel** — create independent workers only when artifacts and
  dependencies are sufficiently separable.

## Relationship to IMP-0018

IMP-0018 measures context amplification and develops context compaction,
retrieval, caching, and deduplication.

IMP-0019 tests a higher-level strategy:

> Instead of repeatedly optimizing one increasingly long agent context, should
> Orchestrator end the episode and instantiate a fresh task-scoped worker?

Both tracks use the same telemetry and eval harness. Do not build duplicate
measurement systems.

## Promotion criteria

Enable automatic rotation only after controlled evidence shows:

- lower total tokens and/or monetary cost per validated completion;
- noninferior validation;
- no material rise in retries or repair burden;
- correct checkpoint/resume behavior;
- structured handoffs preserve decision/evidence provenance;
- worker startup/rediscovery cost is captured honestly;
- recursion/fan-out remains bounded.

Start in report/shadow mode: calculate "would rotate here" decisions without
changing execution. Compare predicted savings with actual historical/replayed
runs before enabling live rotation.

## Immediate instruction to the running Orchestrator agent

Treat IMP-0019 as a high-priority experiment that can share implementation work
with IMP-0018.

First add the measurements needed to compare continue-vs-rotate. Then create a
deterministic/synthetic benchmark and a shadow rotation advisor. Do **not**
immediately make Orchestrator spawn more workers.

If the measured results show a meaningful reduction in total validated cost,
implement semantic-boundary rotation incrementally, beginning with the clearest
boundaries (for example completed research -> implementation, implementation ->
independent review, and checkpointed stage transitions).

Record EXP/EVR/DEC evidence, including the point where additional rotations show
diminishing returns. The desired end state is an evidence-based policy that
learns when continuity is valuable and when a clean worker is cheaper.
