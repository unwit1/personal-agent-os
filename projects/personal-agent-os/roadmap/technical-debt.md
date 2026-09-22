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

### `skill` execution path is recorded but not dispatched

A stage may declare `preferred_execution_path` of `skill`. It is surfaced to
the agent and carried in the completion packet, but it is not dispatched as
code. The canonical skill tree currently contains instruction-only `SKILL.md`
files; discovery and matching expose metadata/context, not a deterministic
callable entry point. A safe adapter therefore needs a reviewed skill-runner
contract before it can be implemented.

P0.5 now dispatches the existing local document cache through a constrained
`document_page` lookup adapter. Cache misses persist the next declared route,
so this debt is specifically the approved-skill invocation boundary.

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

### Telemetry is metadata-only and not yet connected to workflows

P1.1 now has a strict local `TelemetryEvent` schema and append-only JSONL store
under the gitignored `.agent-local` tree. It records only compact labels,
counts, booleans, and timestamps; raw prompts, documents, secrets, and free-form
labels are rejected. A count-only synthetic aggregate report now summarizes
execution paths and validator outcomes without exposing event records. No
workflow/provider usage adapter is connected yet, so unavailable metrics remain
absent and capability selection is still policy-driven rather than
evidence-driven at the workflow level.

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

## From P0.3 — Shared document intelligence

### HR-GUI is not yet wired to this layer

The shared layer exists and is tested, but the scanner that would benefit from
it still has its own path. Nothing is faster in production until HR-GUI calls
`extract_page` with its own extractor and OCR callables. That work belongs in
the HR-GUI repository and was deliberately not attempted from here.

### Field-zone OCR and concurrency are not started

Steps 4 and 5 of the optimization path need the real scanner, real documents,
and measurement on the work machine. Guessing at zone coordinates or thread
counts without that evidence would be the kind of unmeasured optimization the
roadmap explicitly gates against.

### The form vocabulary is a fixed allowlist

`FORM_VOCABULARY` is a curated set of generic form words. It is safe by
construction -- a personal value cannot become an anchor -- but a form whose
structure uses unusual vocabulary yields few anchors and therefore a weak
template signature. The honest fix is to learn anchors from terms recurring
*across many documents*, which needs corpus state this layer does not have yet.

### Benchmark numbers are simulated

The measured speedups use a stand-in OCR cost, not a real engine. The ratios
are structurally sound -- a cache hit genuinely skips the call -- but absolute
seconds saved in production are unknown until HR-GUI is wired up and measured.

### No cross-machine cache story

The cache is deliberately workstation-local and must never sync. That is
correct for privacy, and it means a second machine starts cold with no way to
share the work. Accepted, not solved.

