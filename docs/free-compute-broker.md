# FreeComputeBroker: OpenRouter free-compute maximization (design)

Status: design for the IMP-0015 ASAP slice (2026-10-01). Roadmap:
`projects/personal-agent-os/roadmap/model-infrastructure-manager.md`, section
"OpenRouter free-compute maximization / FreeComputeBroker"; master roadmap
"Operator-priority: Model Infrastructure Manager / Compute Broker", 2026-10-01
ASAP expansion.

The broker treats OpenRouter's free models as a volatile, opportunistic pool.
It runs inside the existing Compute Broker, router, CAP/EVR, validator, budget
and Research Radar primitives. It is not a second orchestration stack. All of
it is deterministic code over cached, versioned data. Tests run against a fake
provider and fixtures and never touch the network.

## Prior art

`agent-os orchestrate prior-art lookup "OpenRouter free model routing"`
(2026-10-01) returned only generic routers (PA-routellm, PA-llmrouter), a
catalog client (PA-hf-hub) and agent frameworks. None was specific to
OpenRouter. The registry now records **PA-openrouter-api** (INVESTIGATE, low
confidence): the documented `GET /api/v1/models`, `GET /api/v1/key` and
`GET /api/v1/credits` shapes are the interface we borrow. We use a stdlib
adapter, as `compute.py` and `radar.py` do, and add no SDK or gateway
dependency (PA-litellm: BORROW only, supply-chain risk). From RouteLLM we borrow
calibrating the escalation threshold against a target share of escalated calls,
but only once specialization data exists. The field names were not re-fetched
by the design worker. Before code depends on them, the first implementation
step captures one live fixture through the secret-safe adapter.

## Hard invariants

These hold in every module and every test asserts them:

1. **Never purchase credits.** No module has a code path that POSTs to a
   billing, credit, checkout or payment endpoint. `openrouter_account.py` sends
   only `GET` requests to an allowlist (`/api/v1/models`, `/api/v1/key`,
   `/api/v1/credits`). Any other method or path raises before the request is
   built.
2. **Never enable auto-recharge.** No setting, CLI flag or API call changes
   account configuration. The account adapter is read-only by construction.
3. **Never call a paid model.** The broker only *decides*. A `route=free`
   decision names a catalog model whose current snapshot pricing is zero on
   every priced dimension. `free_swarm.py` and backfill re-check that predicate
   against the latest snapshot immediately before dispatch and refuse otherwise.
   `route=escalate` returns a *ladder* to the existing router, and that router
   applies its existing budget gate (`budget.effective`, `quote.budget_gate`)
   and approvals. The broker never dispatches a non-free request itself.
4. **Never read or print secret values.** The key is the reference
   `secrets://openrouter/default`, resolved only inside the adapter's request
   builder via `secret_refs.resolve`. It is never returned, logged, cached,
   stored in a snapshot, ledger, decision or error message, or put in an
   exception string. Errors pass through `secret_refs.redact`. Status output
   uses `secret_refs.status` (presence/source only).

Also: free traffic never bypasses existing concurrency, privacy, secret,
protected-path (`control_plane.protected_globs`) or repository-write controls.

## Module layout (`src/agent_os/orchestrator/`)

| Module | Responsibility | Reuses |
|---|---|---|
| `free_catalog.py` | Fetch `/api/v1/models` through an injectable opener, normalize it to the snapshot schema, decide "free" by zero pricing (no hard-coded model lists), persist versioned snapshots, diff consecutive snapshots | `compute.py` cache pattern, `storage.write_json`, `timestamps.utc_now_iso` |
| `free_policy.py` | Load the versioned provider-policy record, merge operator overrides, report staleness (`verified_at` age) | `store.orchestrator_home` |
| `openrouter_account.py` | Read-only key/credit state behind `secrets://openrouter/default`; GET allowlist; derive `high_allowance` (`true`/`false`/`null`) | `secret_refs`, `retry.RetryPolicy` |
| `free_quota.py` | Append-only quota ledger; daily budget, per-minute governor, reserve, retry budget, reset boundary; backfill eligibility | `provider_health` cooldowns / circuit breaker |
| `free_specialization.py` | Specialization records per task_family x model from ledger + CAP observations; Wilson bounds; proven/canary/unproven | `capability.wilson`, `capability.record_observation` |
| `free_metrics.py` | Metrics report (useful progress per request, acceptance, retries, escalations, paid fallbacks avoided, estimated paid cost avoided) | `usage`, `model_prices` |
| `free_routing.py` | Low-risk/verifiable eligibility rule, data-policy check, model choice, escalation ladder, top-up alert evaluation | `router.select`, `model.ROLES`, `workload.SENSITIVITY`, `control_plane` |
| `free_swarm.py` | Bounded disposable fan-out where validation is cheap; checkpointable backfill queue for otherwise-expiring quota | `delegate.check_contract`, `validators.run_all`, `continuation`/checkpoint conventions |

Runtime state lives under `<orchestrator home>/free-compute/` (derived and
rebuildable, outside Git):

```
free-compute/
  catalog/snapshots/<snapshot_id>.json   # one per distinct fetch result
  catalog/latest.json                    # copy of the newest snapshot
  catalog/diffs.jsonl                    # one diff per new snapshot
  account.json                           # last read-only account state (no key)
  policy-overrides.json                  # operator overrides (optional)
  ledger.jsonl                     # append-only events
  specialization.json                    # derived records
  backfill/queue.jsonl, backfill/checkpoints/<item_id>.json
```

The reviewed, canonical provider-policy history lives in Git at
`projects/personal-agent-os/orchestrator-os/records/provider-policy/openrouter-free.json`.
It is append-only: a new version is added, earlier versions are never edited.

## JSON shapes

Every persisted object carries `schema_version`. Timestamps are UTC ISO-8601
(`...Z`). USD amounts are numbers. Token prices are USD per token, parsed from
OpenRouter's decimal strings.

### Catalog snapshot (`free_catalog.py`)

```json
{
  "schema_version": "agent-os/free-catalog-snapshot/v1",
  "provider": "openrouter",
  "snapshot_id": "FCS-20261001T120000Z-3f9a1c2b",
  "fetched_at": "2026-10-01T12:00:00Z",
  "source_url": "https://openrouter.ai/api/v1/models",
  "authenticated": false,
  "content_sha256": "<sha256 of the normalized models array>",
  "free_predicate": "pricing.prompt == 0 and pricing.completion == 0 and pricing.request == 0",
  "models": [
    {
      "slug": "example-org/example-model:free",
      "canonical_slug": "example-org/example-model-2026-09-15",
      "revision": "example-org/example-model-2026-09-15",
      "context_length": 131072,
      "modalities": {"input": ["text"], "output": ["text"]},
      "supports_tools": true,
      "supports_structured_output": false,
      "pricing": {"prompt": 0.0, "completion": 0.0, "request": 0.0, "image": 0.0},
      "data_policy": {"trains_on_prompts": null, "retains_prompts": null, "moderated": false, "source": "unknown"},
      "first_seen": "2026-09-20T08:00:00Z",
      "last_seen": "2026-10-01T12:00:00Z",
      "last_verified": "2026-10-01T12:00:00Z"
    }
  ]
}
```

- Only models that satisfy `free_predicate` are kept. The pool is whatever the
  provider currently prices at zero, so a model can join or leave without a
  code edit. `openrouter/free` is admitted as a pseudo-model with
  `"revision": null` and is only eligible for the backfill route (low-stakes
  opportunistic work).
- `revision` is `canonical_slug` when the provider supplies one, else `null`.
  Specialization records key on `revision` when present, so a silently swapped
  model behind the same slug starts with no evidence of its own.
- `supports_tools` / `supports_structured_output` come from
  `supported_parameters` (`tools`; `structured_outputs` or `response_format`).
- `data_policy` fields are tri-state (`true`/`false`/`null` = unknown). Unknown
  is treated as the restrictive value (see routing).
- `first_seen` is carried forward from the previous snapshot. `last_seen` is
  this fetch. `last_verified` is the last time a real request to the model
  succeeded (from the ledger) or, failing that, `last_seen`.
- `snapshot_id` = `FCS-<fetched_at compact>-<content_sha256[:8]>`. A fetch whose
  `content_sha256` equals the latest snapshot's only bumps `last_seen` /
  `fetched_at` in `latest.json` and writes no new snapshot or diff.
- The cache TTL (default 6 h, like `compute.CACHE_SECONDS`) is configuration.
  Network failure returns `{"models": [], "error": ...}` with the last good
  snapshot still usable and marked `stale: true`. Discovery never raises.

### Catalog diff

```json
{
  "schema_version": "agent-os/free-catalog-diff/v1",
  "provider": "openrouter",
  "from_snapshot": "FCS-20260930T120000Z-aa11bb22",
  "to_snapshot": "FCS-20261001T120000Z-3f9a1c2b",
  "at": "2026-10-01T12:00:00Z",
  "added": ["example-org/new-model:free"],
  "removed": ["example-org/retired-model:free"],
  "changed": [
    {"slug": "example-org/example-model:free",
     "fields": {"context_length": [65536, 131072], "supports_tools": [false, true]}}
  ]
}
```

`changed` compares every snapshot field except `first_seen`, `last_seen` and
`last_verified`. A `revision` change also resets that model's specialization
status to `canary` (see below). A removed model is immediately ineligible for
routing. Its specialization history is kept.

### Versioned provider-policy record (`free_policy.py`)

```json
{
  "schema_version": "agent-os/provider-policy/v1",
  "provider": "openrouter",
  "policy": "free-model-allowance",
  "version": 1,
  "free_rpm": 20,
  "daily_free_requests_low": 50,
  "daily_free_requests_high": 1000,
  "credit_threshold_usd": 10.0,
  "failed_requests_count": true,
  "reset": "00:00Z",
  "source_url": "https://openrouter.ai/docs/api-reference/limits",
  "verified_at": "2026-10-01T00:00:00Z",
  "verified_by": "operator directive / roadmap 2026-10-01",
  "max_age_days": 30,
  "overrides": {}
}
```

- The Git file holds `{"schema_version": "agent-os/provider-policy-history/v1",
  "versions": [<record>, ...]}`. The highest `version` is current. These
  figures are data, not constants: no module hard-codes 20/50/1000/10.
- `failed_requests_count: true` means failed free requests consume daily
  allowance, so the governor charges them.
- `reset` is the daily reset boundary in UTC. It is an assumption until
  verified, and overridable.
- `overrides` (merged from `policy-overrides.json`, operator-only) may set any
  numeric field plus `reserve_requests`, `retry_budget`, `backfill_window_hours`,
  `swarm_max_width`, `allowed_sensitivity`, `allow_training_endpoints`.
  `free_policy.effective()` returns the merged record plus
  `{"stale": bool, "overridden": [field, ...]}`.
- A record whose `verified_at` is older than `max_age_days` is `stale`. A stale
  policy still governs quota conservatively (it uses the low allowance), but it
  can never trigger a top-up alert.

### Account state (`openrouter_account.py`, read-only)

```json
{
  "schema_version": "agent-os/openrouter-account/v1",
  "read_at": "2026-10-01T12:00:00Z",
  "secret_ref": "secrets://openrouter/default",
  "configured": true,
  "key": {"is_free_tier": false, "usage_usd": 0.42, "limit_usd": null, "limit_remaining_usd": null, "rate_limit": {"requests": 20, "interval": "1m"}},
  "credits": {"total_purchased_usd": 10.0, "total_used_usd": 0.42, "balance_usd": 9.58},
  "high_allowance": true,
  "high_allowance_basis": "key.is_free_tier == false",
  "observed_daily_peak": 212,
  "errors": []
}
```

- `secret_ref` is the reference string, never the value.
- `high_allowance` is `true` when `key.is_free_tier` is `false`, or when the
  ledger shows a UTC day with more accepted free requests than
  `daily_free_requests_low` (observed cap evidence). It is `false` when
  `is_free_tier` is `true` and no such evidence exists. It is `null` when
  neither signal is available. When the provider field and ledger evidence
  disagree, the disagreement goes into `errors` as `"discrepancy: ..."`. It is
  surfaced, not guessed away.
- A remaining balance (`balance_usd`) below the threshold says nothing about
  the allowance by itself and is never used to set `high_allowance`.

### Quota ledger event (`free_quota.py`)

One JSON line per free request attempt, appended to `ledger.jsonl`:

```json
{
  "schema_version": "agent-os/free-quota-event/v1",
  "ts": "2026-10-01T12:03:17Z",
  "model": "example-org/example-model:free",
  "revision": "example-org/example-model-2026-09-15",
  "task_family": "unit_test_generation",
  "run_id": "run-20261001T195202Z-16098f",
  "node_id": "fcb-impl",
  "outcome": "success",
  "http_status": 200,
  "retry": 0,
  "escalated": false,
  "validator_passed": true,
  "accepted": true,
  "useful_units": 1,
  "latency_ms": 4210,
  "tokens": {"input": 1834, "output": 612, "accuracy": "exact"},
  "structured_output_ok": true,
  "tool_calls_ok": null,
  "lane": "priority"
}
```

- `outcome` is one of `success | invalid_output | validator_failed |
  rate_limited | quota_exhausted | provider_error | timeout | context_overflow`.
  `retry` is the 0-based attempt index for the same work item.
  `validator_passed` / `accepted` are `null` until known. A later
  `{"type": "verdict", "ts", "event_ts", "validator_passed", "accepted",
  "escalated"}` line can complete them, so the ledger stays append-only.
- `lane` is `priority | swarm | backfill`.
- `tokens` uses the `usage.normalized` accuracy labels. No prompt or output text
  is ever stored.
- The governor counts the day's events with `ts >= last reset` as spent
  allowance. When `failed_requests_count` is true, every outcome counts. A
  `rate_limited` or `quota_exhausted` outcome also records a provider cooldown
  through `provider_health.record_quota` and opens the per-model circuit.

Governor rules: `budget_today = allowance - spent - reserve_requests`, where
`allowance` is `daily_free_requests_high` if `high_allowance is true`, else
`daily_free_requests_low`. An unknown tier counts as low. The per-minute window
admits at most `free_rpm` requests per rolling 60 s. Retries draw on
`retry_budget` (default 1 per item) with `retry.full_jitter` backoff. A model
whose breaker is open gets no requests until it cools down. `admit(lane)`
returns `{"admitted": bool, "wait_seconds": float, "reason": str,
"budget_remaining": int, "resets_at": ts}`. The broker never issues a request
only to use up quota.

### Specialization record (`free_specialization.py`)

```json
{
  "schema_version": "agent-os/free-specialization/v1",
  "task_family": "unit_test_generation",
  "model": "example-org/example-model:free",
  "revision": "example-org/example-model-2026-09-15",
  "n": 24,
  "passed": 21,
  "pass_rate": 0.875,
  "wilson95": [0.690, 0.957],
  "retries": 3,
  "latency_ms": {"p50": 3900, "p90": 9100},
  "structured_output_reliability": 0.958,
  "tool_reliability": null,
  "useful_progress_per_request": 0.778,
  "review_acceptance_rate": 0.9,
  "context_failures": 1,
  "status": "proven",
  "first_observed": "2026-09-21T10:00:00Z",
  "last_observed": "2026-10-01T12:03:17Z",
  "evidence": ["local:free-compute/ledger.jsonl#2026-10-01T12:03:17Z"]
}
```

- Records are derived from the ledger (plus matching `capability.py`
  observations recorded with `provider: "openrouter-free"`). They are never
  hand-written. `wilson95` uses `capability.wilson`.
- `useful_progress_per_request = sum(useful_units of accepted events) /
  requests charged against quota` (retries and failures included).
- Status:
  - `unproven`: `n < canary_min` (default 5). The model may only receive
    exploration traffic: at most `explore_share` (default 10%) of eligible
    items in the family, and only in the backfill/swarm lanes.
  - `canary`: `n >= canary_min` and Wilson lower bound below
    `proven_floor`, or the revision changed. Traffic is capped by
    `canary_share` (default 25%) and never displaces a proven specialist.
  - `proven`: `n >= proven_min` (default 20) and the Wilson lower bound is at
    least `proven_floor` (default 0.65). It gets priority traffic for the family.
  - Demotion is automatic: if the Wilson upper bound over the last
    `demote_window` (default 20) events falls below `proven_floor`, the model
    returns to `canary`.

### Route decision (`free_routing.py`)

```json
{
  "schema_version": "agent-os/free-route-decision/v1",
  "decided_at": "2026-10-01T12:03:10Z",
  "task_family": "unit_test_generation",
  "route": "free",
  "model": "example-org/example-model:free",
  "revision": "example-org/example-model-2026-09-15",
  "reason": "proven specialist: wilson95 low 0.690 >= floor 0.65; 412 free requests left before reserve",
  "eligibility": {"low_risk_verifiable": true, "failed_checks": []},
  "policy_allowed_by": ["policy:openrouter/free-model-allowance@v1", "sensitivity:internal<=allowed", "data_policy:no-training-known", "validators:2 declared"],
  "catalog_snapshot": "FCS-20261001T120000Z-3f9a1c2b",
  "quota": {"budget_remaining": 412, "rpm_headroom": 17, "resets_at": "2026-10-02T00:00:00Z"},
  "ladder": [
    {"rung": "alternate_free", "candidates": ["example-org/other-model:free"]},
    {"rung": "local_or_already_paid", "candidates": ["local-abliterated", "claude-code(subscription)"]},
    {"rung": "cheap_paid", "candidates": ["<router.select fast class>"]},
    {"rung": "frontier", "candidates": ["<router.select frontier class>"]}
  ]
}
```

`route` is `free | escalate`. With `escalate`, `model` is `null`, `reason`
names the failed check (for example `"not low-risk: effort high"`,
`"quota: reserve reached"`, `"no free model with tools"`), and the ladder starts
at the first applicable rung. Candidates on rungs 2-4 come from
`router.select` over the existing provider registry. The broker lists them and
the engine executes them under existing budget and approval gates.

### Metrics report (`free_metrics.py`)

```json
{
  "schema_version": "agent-os/free-metrics/v1",
  "window": {"from": "2026-10-01T00:00:00Z", "to": "2026-10-01T23:59:59Z"},
  "policy_version": 1,
  "free_policy_last_verified_at": "2026-10-01T00:00:00Z",
  "openrouter_free_quota_tier": "high",
  "openrouter_credit_balance": 9.58,
  "catalog": {"snapshot": "FCS-20261001T120000Z-3f9a1c2b", "free_models": 31, "added_today": 1, "removed_today": 0},
  "free_requests_attempted": 140,
  "free_requests_successful": 118,
  "free_requests_wasted_or_failed": 22,
  "free_request_budget_remaining": 812,
  "free_useful_progress_per_request": 0.71,
  "free_validator_pass_rate": 0.84,
  "free_review_acceptance_rate": 0.9,
  "free_retry_rate": 0.11,
  "free_escalation_rate": 0.08,
  "free_paid_fallbacks_avoided": 97,
  "estimated_paid_cost_avoided_usd": 3.12,
  "estimated_paid_cost_basis": "per accepted free result: tokens x price of the cheapest paid route router.select would have used (model_prices snapshot 2026-10-01)",
  "per_family": [
    {"task_family": "unit_test_generation", "preferred": "example-org/example-model:free", "free_model_task_family_success_rate": 0.875,
     "free_model_latency_p50_ms": 3900, "free_model_tool_reliability": null, "free_model_structured_output_reliability": 0.958}
  ],
  "by_lane": {"priority": 80, "swarm": 40, "backfill": 20},
  "top_up": {"status": "not_needed", "shortfall_usd": null, "rationale": "account has high allowance (key.is_free_tier == false)", "evidence": ["policy:openrouter/free-model-allowance@v1 verified 2026-10-01"], "errors": []}
}
```

- `free_paid_fallbacks_avoided`: accepted free results that never escalated to
  a paid rung.
- `estimated_paid_cost_avoided_usd`: for each of those, the token counts times
  the per-token price of the paid route the router would otherwise have chosen.
  It is labeled "estimated" and carries its basis. Subscription routes count
  as 0 USD avoided (already paid).
- Rates divide by attempted requests in the window. A rate is `null` when its
  denominator is zero.
- The report is optimized for and ranked by *cost per verified successful task*
  and *useful progress per free request*, never by raw call count.

## Low-risk and verifiable: the eligibility rule

`free_routing.eligible(task, *, sensitivity, protected_globs) -> (bool,
failed_checks)` returns `(True, [])` only if **all** hold; otherwise it returns
`(False, [...])` naming every failed check:

1. **Declared validators.** The task has at least one declared validator
   (`validators.run_all` input). Each validator is a deterministic command,
   schema/output contract (`delegate.check_contract`) or repository check.
   "Review only" does not qualify for priority-lane work.
2. **Role** is `implementer` or `test_author` (`model.INTEGRATED_ROLES`). For
   swarm/backfill microtasks the `inline` delegate role also qualifies when its
   output contract is the validator. Planner, reviewer-of-record and repairer
   roles never go free-first.
3. **Effort** is `low` or `medium`.
4. **No protected or secret paths.** No path in the task scope or attachments
   matches the `protected_globs` argument (callers pass
   `control_plane.protected_globs(policy)`) or the secret patterns
   (`**/secrets/**`, `**/.env*`, `**/*.pem`, `**/*.key`, `**/credentials*`, and
   anything `secret_refs` manages). Run-level `protected_paths_allowed` grants
   do not extend to free routes.
5. **Sensitivity allowed.** The `sensitivity` argument (a
   `workload.SENSITIVITY` value) is in the policy's `allowed_sensitivity`
   (default `["public", "internal"]`). `private` and `secret` are never
   eligible.

If any check fails, the result is `route=escalate` with the failing checks in
`eligibility.failed_checks`. `eligible()` is model-independent. The decision
also requires a free model that meets the task's needs (context length >=
estimated prompt + output; tools / structured output when required), passes
the data-policy check, and gets governor admission for the lane. Data-policy
check: for `internal` sensitivity (repository code), the model's
`data_policy.trains_on_prompts` must be `false`, unless the project policy sets
`allow_training_endpoints: true`. Unknown (`null`) counts as `true`.

Model choice inside the free pool: proven specialist with the highest Wilson
lower bound for the family, then `useful_progress_per_request`, then lower p50
latency. Ties break by slug, so the order is deterministic. Exploration and
canary shares are applied with a seeded hash of `(run_id, node_id)`, never
`random`. No global favorite model exists.

## Escalation ladder

On validator failure, invalid output, quota refusal or an open circuit, the
next rung is tried in this fixed order:

1. **Alternate free model**: the next-ranked free model for the family, only
   when its expected value is positive (Wilson low bound times the value of a
   pass exceeds the request's quota cost plus validation cost) and quota
   remains. At most `alternate_free_max` (default 1) alternates per item.
2. **Local / already-paid**: local endpoints and subscription CLI workers
   (Claude Code, Codex) at the task's capability class through `router.select`.
3. **Cheap paid**: the lowest-cost paid API route at the `fast`/`balanced`
   class, subject to `budget.effective` and the job hard cap.
4. **Frontier**: the `reasoning`/`frontier` class, as policy allows.

Verified partial outputs (files whose validators passed, accepted map items)
are checkpointed and passed forward. Escalation never redoes successful work.
Every rung transition appends a ledger event (`escalated: true`) or a router
observation, so escalation rates are measurable.

## Disposable fan-out and backfill (`free_swarm.py`)

- **Fan-out** happens only when validation is cheap: the family's declared
  validator has a measured median below `swarm_validator_max_seconds` (default
  60 s), or the output is a schema-checked contract. Width is
  `min(swarm_max_width (default 4), rpm_headroom, budget_today - reserve,
  engine concurrency limit)`. Workers get minimal, task-scoped context
  (`delegate.build_attachments`, datamarked) and no repository write access.
  Results are aggregated by deterministic validation and map-reduce (keep the
  passing outputs, de-duplicated by content hash), not by majority vote.
- **Backfill** consumes otherwise-expiring free quota. An item is admitted only
  when `hours_to_reset <= backfill_window_hours` (default 4) and
  `budget_today - projected_priority_demand > reserve_requests`. Projected
  priority demand is the mean of the last 7 days' priority-lane requests in
  the same window. Queue items (tests, docs, static review, eval samples,
  metadata extraction) carry `{item_id, task_family, validators, checkpoint}`.
  They resume from `backfill/checkpoints/<item_id>.json`, so a reset or crash
  loses at most one request. Backfill never delays a priority-lane admission
  and never runs an item without a validator. If no useful item exists, the
  quota is left unused.

## Top-up alert rule

`free_routing.top_up_status(account, policy)` returns one of `not_needed |
recommended | unknown | blocked_by_policy`:

- `not_needed`: `account.high_allowance is true`. This holds whatever the
  remaining balance is: a low balance by itself never triggers an alert.
- `recommended` (the only status that alerts the operator): **all** of
  `account.high_allowance is false`, the current policy is verified (not stale)
  with a non-null `credit_threshold_usd`, and `credits.total_purchased_usd` is
  known. The alert states the exact shortfall `shortfall_usd =
  round(credit_threshold_usd - total_purchased_usd, 2)` (> 0), the allowance
  it would unlock (`daily_free_requests_low` -> `daily_free_requests_high`),
  the policy `source_url` and `verified_at`, and the account read time. It
  says that Agent OS will not buy credits: the operator tops up in the
  OpenRouter console.
- `unknown`: high allowance is `null`, the policy is stale, or purchased
  credits are unreadable. Also `unknown`: `high_allowance is false` but the
  computed `shortfall_usd <= 0` (purchases already meet the threshold). Then
  `shortfall_usd` is `null`, the top-up result's `errors` (and the account
  record's `errors`) record
  `"discrepancy: is_free_tier true despite purchases >= threshold"`, and no
  alert is sent. This is shown in the CLI/GUI with the reason and is never sent
  as an alert.
- `blocked_by_policy`: the operator disabled free routing or no task family is
  eligible under the data policy. A top-up would not help, so there is no alert.

The alert is raised at most once per (policy version, account state) pair and
recorded as a finding. The broker never acts on it.

## CLI / GUI surface

`agent-os orchestrate free-compute <catalog [--refresh] | diff | policy |
account | quota | route <task.json> | specialization | metrics [--day] |
backfill | status>` prints JSON. `orchestrate free-compute status` combines the roadmap view: allowance and remaining
requests, RPM headroom, free-model count and preferred specialists, useful free
requests today, estimated paid calls/cost avoided, free validation/acceptance
rate, and top-up status. The GUI reads the same JSON.

## Test plan (no network)

- A fake opener serves fixture `/models`, `/key` and `/credits` payloads.
  Tests check that free models are discovered by zero pricing, that
  adding/removing/changing a model yields the right diff with no code edit, and
  that an identical fetch writes no new snapshot.
- Policy: overrides merge; stale policy uses the low allowance and suppresses
  alerts.
- Governor: RPM window, daily budget at both tiers, failed requests charged,
  reset boundary, reserve, retry budget, open circuit.
- Eligibility: each of the five checks fails alone.
- Ladder order is fixed. Partial outputs are preserved.
- Specialization: status transitions and demotion. A swapped revision restarts
  as canary.
- Metrics arithmetic on a fixture ledger.
- Top-up: the four statuses, including the case "balance USD 2 but
  is_free_tier false -> not_needed", an exact shortfall, and the discrepancy
  case "is_free_tier true, total_purchased_usd >= credit_threshold_usd ->
  unknown, discrepancy recorded in errors, no alert".
- Invariants: the account adapter rejects non-GET and non-allowlisted URLs. No
  secret value appears in any persisted file, decision, report or exception
  (the test seeds a sentinel key value and scans outputs). A route never names
  a model with non-zero pricing.

## Implementation order

1. `free_catalog.py` + `free_policy.py` (discovery, snapshot/diff, versioned
   policy).
2. `openrouter_account.py` (read-only), `free_quota.py` (ledger + governor).
3. `free_routing.py` for two families first (`unit_test_generation`,
   `documentation`) with the eligibility rule and ladder.
4. `free_specialization.py`, `free_metrics.py`, and the top-up status.
5. `free_swarm.py` fan-out and backfill. Then CLI wiring and a held-out A/B
   evaluation against the incumbent route, promoting only with noninferior
   validation and lower expected paid cost.
