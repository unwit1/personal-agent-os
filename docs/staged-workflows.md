# Staged workflow orchestrator

Status: implemented (P0.1)

## Why stages exist

A single expensive session should not carry an entire multi-step job. Some
stages of real work are deterministic — running a validator, a test suite, an
index rebuild — and cost nothing but wall-clock time. Others genuinely need
reasoning. Without stages, the cheap parts are paid for at the price of the
expensive parts, and an interruption loses everything because the only record
of progress is the conversation itself.

The orchestrator splits work into stages so that:

- each stage runs at the cheapest capability class that could satisfy it;
- each stage compiles **its own** context inside **its own** token budget;
- progress is persisted, so an interrupted job resumes from disk rather than
  from conversation memory;
- every boundary emits a compact completion packet and an exact next prompt.

## Capability classes are provider-neutral

A stage names a capability *class*, never a model:

    deterministic -> fast -> balanced -> reasoning -> frontier

Concrete models resolve at execution time from `~/.agent-os/providers.json`
(override with `AGENT_OS_PROVIDERS`), shaped as:

```json
{
  "providers": [
    {"id": "example-runner", "enabled": true, "models": {"fast": "...", "balanced": "..."}}
  ]
}
```

When no provider is configured, resolution reports that honestly and the
orchestrator still recommends a class — the operator chooses the model. Nothing
in `src/agent_os/workflows.py`, `src/agent_os/capabilities.py`, or the manifest
schema may name a vendor; a regression test enforces this.

(The client-surface registry from P0.0 *does* name vendors, on purpose: it
exists to describe real clients. The neutrality rule covers the orchestrator
core, not the whole repository.)

## Execution paths are selected economically

`preferred_execution_path` remains the backward-compatible default. A stage may
also declare `available_execution_paths` when more than one approved route is
actually available. The orchestrator selects the first candidate in the
deterministic economy order:

    deterministic -> cache -> skill -> model

The selected path is persisted in run state and returned in stage packets, so a
resumed agent sees the same routing decision. This bounded policy stage makes
route selection deterministic. A stage that declares a `cache_lookup` may use
the existing private document cache: a hit completes locally, while a miss
persists the next declared path before handing the stage to its caller. The
cache adapter returns only hit metadata; cached document content never enters
workflow state. Skill execution remains caller-owned.

Stage packets also expose a compact `execution_path_explanation` containing the
preferred path, declared candidates, selected path, and whether the cheapest
declared route or a persisted fallback was selected. This is an observable
policy explanation; it does not name or invoke a provider.

`cache_lookup` is currently limited to a content-addressed `document_page` key
(`file_hash`, `page_index`, and optional extraction settings). It is a lookup
contract, not a second document-processing implementation; callers populate
the cache through `ingester_engine.cache.extract_page` (the shared per-user cache
owned by the Ingester Engine; legacy `<checkout>/.agent-local/document-cache`
entries are still honored on lookup).

## Manifests

Manifests are canonical Git data in `workflows/<workflow_id>.json`, validated by
`schemas/workflow-manifest-v1.schema.json` and by `agent.py validate`.

Each stage declares `stage_id`, `goal`, inputs/artifacts, `required_context`
(task plus token budget), `preferred_execution_path`, optional
`available_execution_paths`, `capability_class`,
`effort`, `allowed_tools`, `limits`, a `validator`, a `stop_condition`,
`expected_outputs`, an optional `checkpoint`, `next_stage`, and an optional
`next_prompt` template.

Context compilation uses a default minimum skill relevance score of two lexical
points. A single generic overlap is omitted; callers can request a different
threshold explicitly, and the selected threshold is recorded in
`context_policy`. Synthetic context-bloat coverage keeps unrelated skill growth
out of the selected metadata and confirms skill bodies remain unloaded by
default. Accuracy coverage also checks relevant, weak, and unrelated synthetic
tasks through both direct matching and compiled context packets. Workflow
regression coverage verifies completed cheap stages remain no-ops, partial
failure escalates only the unresolved stage, and persisted checkpoints produce
the same resumable next prompt. A synthetic benchmark also compares a baseline
packet with staged fixture packets and records model-free stages, validation
parity, and bounded context overhead. Its synthetic A/B arm also records
hypothetical model-call/handoff avoidance and the highest executed path without
invoking a provider.

A deterministic stage must declare a real validator. A deterministic stage
nobody can check is just an unverified stage wearing a cheaper label.

## Lifecycle

    resolve workflow
    -> run the cheapest appropriate stage
    -> validate
    -> persist outputs/checkpoint
    -> stop at the configured boundary
    -> emit a compact completion packet
    -> emit the next stage, its capability class, and a ready-to-paste prompt

Two execution modes share that lifecycle:

- **deterministic** stages execute locally, right now, with no model involved;
- every other stage is *prepared* — context compiled, prompt generated,
  capability recommended — and handed to whatever agent is running, which
  reports back through `workflow-complete`.

The orchestrator never pretends to run a model itself.

## Escalation is evidence-driven

A stage moves up the ladder one rung only after its declared validator actually
fails, and the reason is recorded. Escalation stops at `max_escalations` and
marks the stage `blocked` rather than climbing to the most expensive class by
default.

A stage that already passed is never re-run, and never re-run at a higher class
without an explicitly recorded reason. Partial outputs from a failed stage are
merged and kept, so only the unresolved portion is redone.

`complete_stage` accepts what an agent reports, but the declared validator —
not the caller's confidence — decides whether the stage passed.

## Resumability

Run state lives in `projects/<project>/workflows/<run_id>.json` and holds stage
outcomes, capability classes, attempts, escalations, outputs, checkpoints, and
validation evidence. It deliberately holds **no transcript**: saving one is
refused, and `agent.py validate` fails a run record that carries one.

`agent.py workflow-next <workflow> --run-id <id>` answers "what do I run next?"
entirely from that file.

## Commands

```powershell
agent-os workflows
agent-os workflow-start repository-health-sweep --run-id sweep-1
agent-os workflow-run   repository-health-sweep --run-id sweep-1
agent-os workflow-next  repository-health-sweep --run-id sweep-1
agent-os workflow-stage repository-health-sweep --run-id sweep-1
agent-os workflow-complete repository-health-sweep --run-id sweep-1 --stage triage --output "..."
agent-os workflow-runs personal-agent-os
```

The same operations are exposed over MCP as `workflow.list`, `workflow.start`,
`workflow.next`, `workflow.stage`, `workflow.run_stage`,
`workflow.complete_stage`, and `workflow.runs`, so every routed surface from
P0.0 can drive a staged run.

## Local usage telemetry (opt-in)

Stage telemetry is recorded only when a caller explicitly enables it. The
orchestrator records metadata-only events in a local JSONL file under 
`.agent-local/telemetry`. The telemetry captures one event per executed 
stage (deterministic, cache hit, or agent-reported model stage) with:
- execution path (deterministic, cache, skill, or model);
- capability class;
- retry and escalation counts;
- validator outcome;
- input, cached, reasoning, and output token counts (when reported).

Prompts, outputs, and other raw content are never recorded; unavailable metrics 
are never fabricated. Raw telemetry stays local and is never committed.

### Enabling telemetry via CLI

Pass `--telemetry-path <file>` to `workflow-run` or `workflow-complete` to 
record one local event per executed stage. The path must be under `.agent-local` 
or outside the repository:

```powershell
agent-os workflow-run repository-health-sweep --run-id sweep-1 --telemetry-path .agent-local/telemetry/sweep-1.jsonl
agent-os workflow-complete repository-health-sweep --run-id sweep-1 --stage triage --output "..." --telemetry-path .agent-local/telemetry/sweep-1.jsonl
```

`workflow-complete` accepts optional caller-reported token usage and model 
information. These are recorded only when telemetry is enabled, validated 
before the run record changes, and omitted values stay unknown and are never 
estimated:

```powershell
agent-os workflow-complete repository-health-sweep --run-id sweep-1 --stage triage \
  --output "..." \
  --telemetry-path .agent-local/telemetry/sweep-1.jsonl \
  --provider openai \
  --model gpt-4-turbo \
  --input-tokens 500 \
  --cached-tokens 100 \
  --reasoning-tokens 50 \
  --output-tokens 200
```

### Reporting aggregate telemetry

Use `agent-os telemetry-report --path <file>` to view aggregate counts across
events. The report includes:
- `event_count`: total events;
- `execution_path_counts`: distribution of execution paths;
- `capability_class_counts`: distribution of capability classes;
- `token_totals`: sum of input, cached, reasoning, and output tokens;
- `token_unknown_counts`: count of events with unknown (unreported) token values;
- `retry_total`, `escalation_total`, `events_with_retries`, `events_with_escalations`: retry and escalation metrics;
- `deterministic_path_model_class_counts`: model classes executed on deterministic paths;
- `validator_outcome_counts`: distribution of validator pass/fail.

The report exposes only aggregate statistics without exposing per-event records,
provider information, event IDs, or timestamps. Add `--group-by project` or 
`--group-by category` to break down the report by project ID or task category:

```powershell
agent-os telemetry-report --path .agent-local/telemetry/sweep-1.jsonl --group-by project
```

Grouped reports include a top-level `group_by` field and a `groups` object with 
one report per label; provider, model, event ID, and timestamp information is 
never included in any report.

### Enabling telemetry via Python API

A Python caller enables telemetry by providing a `LocalTelemetryStore` to the 
`run_stage()` and `complete_stage()` functions in `src/agent_os/workflows.py`:

```python
from agent_os.telemetry import LocalTelemetryStore
from agent_os.workflows import run_stage, complete_stage

store = LocalTelemetryStore(".agent-local/telemetry/sweep-1.jsonl")
run_stage("repository-health-sweep", "sweep-1", telemetry_store=store)
complete_stage(
    "repository-health-sweep", 
    "sweep-1", 
    "triage", 
    telemetry_store=store,
    provider="openai",
    model="gpt-4-turbo",
    input_tokens=500,
    cached_tokens=100,
    reasoning_tokens=50,
    output_tokens=200,
)
```

Then aggregate the results:

```powershell
agent-os telemetry-report --path .agent-local/telemetry/sweep-1.jsonl
```

## Measured behaviour

Measured on `repository-health-sweep` in this repository:

| stage    | budget | context tokens | capability     | path          |
|----------|--------|----------------|----------------|---------------|
| validate | 600    | 549            | deterministic  | deterministic |
| tests    | 600    | 553            | deterministic  | deterministic |
| triage   | 1200   | 1167           | fast           | model         |
| record   | 900    | 856            | fast           | skill         |
| **total**|        | **3125**       |                |               |

A single unstaged pass covering the whole goal measures 2536 tokens; a naive
load of all registered context measures 29123.

Read that honestly: **staging costs somewhat more total context than one
unstaged pass** (3125 vs 2536), because each stage re-establishes its own
footing instead of sharing one packet. What it buys is that two of the four
stages need no model at all, no stage carries a prior transcript, each model
stage stays near 1000 tokens instead of growing with the conversation, and an
interruption resumes from disk. The saving is in model work and recovery, not
in raw context bytes — and the regression test bounds the staged total rather
than claiming a reduction that does not exist.

## Known limits

- The orchestrator prepares model stages; it does not execute them. Automatic
  delegation is deliberately out of scope for P0.1.
- The local `cache` path can complete approved `document_page` lookups; cache
  misses persist the next declared route. `skill` paths are selected and
  persisted but remain caller-owned. The document-page cache stays
  workflow-stage-specific; the task cache is separate and covers coding tasks
  when `task_cache_enabled` is true. See [docs/orchestrator-os/task-cache-route.md](docs/orchestrator-os/task-cache-route.md).
- skill paths remain caller-owned by operator decision because canonical skills are instruction-only `SKILL.md` files and discovery/match returns metadata, not an executable adapter; a skill becomes executable only by shipping an approved deterministic command used through the deterministic route (see docs/orchestrator-os/task-cache-route.md section 9).
- Stage ordering is linear: explicit `next_stage` links or declaration order.
  There is no parallel or conditional branching yet.
