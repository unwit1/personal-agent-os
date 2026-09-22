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

`cache_lookup` is currently limited to a content-addressed `document_page` key
(`file_hash`, `page_index`, and optional extraction settings). It is a lookup
contract, not a second document-processing implementation; callers populate
the cache through `agent_os.documents.extract_page`.

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
parity, and bounded context overhead.

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
  persisted but remain caller-owned.
- No approved skill currently exposes a deterministic invocation interface:
  canonical skills are instruction-only `SKILL.md` files, and discovery/match
  returns metadata rather than an executable adapter. A skill path must not be
  treated as code until a reviewed runner contract exists.
- Stage ordering is linear: explicit `next_stage` links or declaration order.
  There is no parallel or conditional branching yet.
