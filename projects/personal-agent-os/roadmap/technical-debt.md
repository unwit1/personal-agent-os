# Technical debt

Status: active record
Updated: 2026-09-21

Debt is recorded here rather than left implicit in a roadmap that describes
intent. Each item names what is missing, why it was acceptable to stop there,
and what would close it.

## From P0.0 — Universal routing / MCP hardening

### ChatGPT chat and Work surfaces are bridged, not routed

`integration-health` reports both as "partially bridged", which is honest: no
mechanism exists to preflight Agent OS automatically inside those hosts. They
rely on a manual bridge document.

Closing it needs a genuine automatic invocation path in the host. Until one
exists, the correct behaviour is to keep reporting them as bridged and never
claim an unsupported host can be invisibly intercepted.

### `mcp-compatible-client` is a readiness entry, not a client

It describes server-side readiness for clients that are not registered
individually, so it stays bridged by construction. It becomes routed only when
a specific client registers and carries a preflight instruction.

### The installed Codex adapter must be refreshed after canonical edits

Canonical adapter text now carries an `{{AGENT_OS_REPOSITORY}}` placeholder
rendered at install time. `routing-status` detects drift, but nothing installs
the refreshed copy automatically; `install-routing` reports a conflict rather
than overwriting a modified destination. That conservatism is deliberate — it
will not clobber local edits — but it means a canonical change needs a manual
refresh step.

### Context packet has an irreducible floor

Below roughly 260 tokens the residual core (project identity, git, freshness,
policy flags, measurement) cannot shrink further. `within_budget` reports this
honestly rather than pretending. A smaller floor would require making the
measurement block itself optional.

## From P0.1 — Staged Workflow Orchestrator

### Model stages are prepared, not executed

The orchestrator compiles context, recommends a capability class, and emits an
exact prompt, then stops. It does not call a model. Automatic delegation was
deliberately out of scope for P0.1 and belongs with P1.3 optional API
delegation, which is separately billed and must not shift cost invisibly.

### `cache` and `skill` execution paths are recorded but not dispatched

A stage may declare `preferred_execution_path` of `cache` or `skill`. Both are
surfaced to the agent and carried in the completion packet, but neither is
dispatched differently from `model` yet. Closing this depends on P0.3's
content-addressed cache and on a skill-invocation path that can run a skill
without a model turn.

### Stage ordering is linear

Ordering follows explicit `next_stage` links or declaration order. There is no
branching, no conditional stage, and no parallel execution. Real workflows will
eventually want "if the validator failed, run a repair stage".

### Staging costs more raw context than a single pass

Measured at 3125 staged tokens against 2536 for one unstaged pass on
`repository-health-sweep`. Each stage re-establishes its own footing rather
than sharing one packet. This is the honest trade for model-free stages and
transcript-free resumption, but it is a real cost: a workflow split into many
tiny stages would pay it repeatedly. The regression test bounds the staged
total at twice the single-pass figure rather than asserting a reduction.

### No telemetry yet

Nothing records how long a stage took, how many tokens it actually consumed, or
how often escalation fired. P1.1 covers this; until then, capability selection
is policy-driven rather than evidence-driven at the workflow level.

### Run records are Git-tracked

Run state lives under `projects/<project>/workflows/`. That makes runs portable
and reviewable, but a long-lived or high-frequency workflow would add churn to
canonical Git. A local-only run store with promoted summaries may be needed if
run volume grows.

## From P0.2 — Selective profile retrieval

### Relevance is lexical and vocabulary-driven

A task phrased entirely in synonyms that `DOMAIN_TERMS` does not know retrieves
nothing. It fails closed, which is the safe direction, but the vocabulary needs
curation as the profile grows. A task whose personal dimension is real but
unnamed will be missed silently.

### `drive-derived-context.json` remains unusable

The 60 KB derived Drive index is excluded from retrieval because it is bulk
rather than curated context. Nothing currently distils it into durable facts,
so whatever value it holds is inert. Either promote selected findings into
`user-context.json` with provenance, or index it under the same fact model with
a `derived` confidence and a stricter threshold.

### Confidence and recency are file-level, not fact-level

Every fact inherits its source file's `updated_at` and provenance statuses, so
"last confirmed" cannot distinguish a preference stated yesterday from one
seeded months ago in the same file. Per-fact capture dates would make the
supersede rule meaningfully sharper.

### No profile-specific promotion rule

Candidate profile updates flow through the generic candidate pipeline. There is
no rule yet for when a conversational observation may become a durable profile
fact, which EXEC-0.5 asks for.


## From P0.4 ? Restart-safe recovery

### Checkpoints remain intentionally workstation-local

Recovery records can contain private relative paths and source/item fingerprints,
so they are gitignored instead of synced. A future secure transfer or sanitized
handoff exporter could make intentional cross-machine continuation smoother.

## From P0.5 ? Execution routing

### Cache validity remains subsystem-owned

The generic dispatcher confirms only that a declared cache artifact exists and
is safely located. Content hashes, schema/version compatibility, and semantic
validation remain the responsibility of the cache-owning subsystem.
