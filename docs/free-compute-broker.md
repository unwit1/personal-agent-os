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
   decision names a catalog model for which `free_catalog.is_free(pricing)` is
   true on the current snapshot: every value in the raw provider `pricing`
   object parses to exactly 0 (see the catalog snapshot). `free_swarm.py` and
   backfill call the same `is_free` function on the latest snapshot's raw
   pricing immediately before dispatch and refuse otherwise. There is no second
   predicate.
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
| `free_catalog.py` | Fetch `/api/v1/models` through an injectable opener, normalize it to the snapshot schema, decide "free" with the single `is_free(pricing)` predicate (every raw pricing value parses to 0; no hard-coded model lists), persist versioned snapshots, diff consecutive snapshots | `compute.py` cache pattern, `storage.write_json`, `timestamps.utc_now_iso` |
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
(`...Z`). USD amounts are numbers. Model `pricing` is persisted exactly as
OpenRouter returns it (decimal strings, USD per unit, every key kept) and is
parsed with `decimal.Decimal` only when evaluated.

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
  "free_predicate": "free_catalog.is_free/v1: pricing non-empty and every raw value parses to Decimal 0",
  "models": [
    {
      "slug": "example-org/example-model:free",
      "canonical_slug": "example-org/example-model-2026-09-15",
      "revision": "example-org/example-model-2026-09-15",
      "context_length": 131072,
      "modalities": {"input": ["text"], "output": ["text"]},
      "supports_tools": true,
      "supports_structured_output": false,
      "pricing": {"prompt": "0", "completion": "0", "request": "0", "image": "0", "web_search": "0", "internal_reasoning": "0"},
      "data_policy": {"trains_on_prompts": false, "retains_prompts": null, "moderated": false, "source": "policy:openrouter/free-model-allowance@v2#data_policies[0]", "verified_at": "2026-10-01T00:00:00Z"},
      "first_seen": "2026-09-20T08:00:00Z",
      "last_seen": "2026-10-01T12:00:00Z",
      "last_verified": "2026-10-01T12:00:00Z"
    }
  ]
}
```

- The free predicate is one function, `free_catalog.is_free(pricing) -> bool`.
  It is true only when `pricing` is a non-empty object and **every** value in
  it, whatever the key (including keys this design does not name, such as a
  newly introduced priced dimension), parses as a `Decimal` equal to 0. A
  missing `pricing` object, an empty one, a `null`, non-numeric or negative
  value, or any non-zero value makes the model non-free. The snapshot stores
  the raw pricing object with all keys unchanged, so the predicate can be
  re-evaluated from the snapshot alone. Catalog filtering, routing and the
  swarm/backfill pre-dispatch re-check all call this function.
- Only models for which `is_free` holds are kept. The pool is whatever the
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
  is treated as the restrictive value (see routing). The `/models` listing does
  not supply them. Their only source is the `data_policies` entries of the
  versioned provider-policy record (below). The snapshot stores the value
  resolved at fetch time, with `source` naming the policy version and entry and
  `verified_at` copied from that entry, or `{"...": null, "source": "unknown",
  "verified_at": null}` when no entry matches. Routing does not trust this
  stored copy: it re-resolves through `free_policy.data_policy_for(slug,
  revision)` against the current effective policy, so a new policy version
  takes effect without a refetch.
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
`last_verified`. A `revision` change starts a new specialization record keyed
on the new revision with `n = 0`, so the model is `unproven` again (see below);
the old revision's record is kept but no longer routes. A removed model is immediately ineligible for
routing. Its specialization history is kept.

### Versioned provider-policy record (`free_policy.py`)

```json
{
  "schema_version": "agent-os/provider-policy/v1",
  "provider": "openrouter",
  "policy": "free-model-allowance",
  "version": 2,
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
  "data_policies": [
    {"match": "example-org/example-model:free", "revision": "example-org/example-model-2026-09-15",
     "trains_on_prompts": false, "retains_prompts": null, "moderated": false,
     "source_url": "https://openrouter.ai/docs/<provider data-policy page>", "verified_at": "2026-10-01T00:00:00Z"}
  ],
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
- `data_policies` is the only data-policy source. Each entry is reviewed by the
  operator from the provider's published data policy for that model/endpoint
  and carries its own `source_url` and `verified_at`. `match` is an exact slug
  or a provider prefix ending in `/` (for example `"example-org/"`). An exact
  slug beats a prefix; when `revision` is set the entry applies only to that
  revision, so a swapped model falls back to unknown. An entry whose
  `verified_at` is older than `max_age_days` resolves to unknown. A later
  implementation may add a read-only per-endpoint fetch captured in a fixture,
  but only by adding it to the GET allowlist and recording its result as a new
  policy version; this slice does not.
- The shipped `version: 1` record has `"data_policies": []`; the example above
  is an illustrative later `version: 2` with one reviewed entry. **Until entries are
  populated, every model's data policy is unknown and only `public`-sensitivity
  work is free-eligible**; `internal` (repository) work escalates with
  `"data_policy: unknown"` (see routing).

### Account state (`openrouter_account.py`, read-only)

```json
{
  "schema_version": "agent-os/openrouter-account/v1",
  "read_at": "2026-10-01T12:00:00Z",
  "secret_ref": "secrets://openrouter/default",
  "configured": true,
  "key": {"is_free_tier": false, "usage_usd": 0.42, "limit_usd": null, "limit_remaining_usd": null, "rate_limit": {"requests": 20, "interval": "1m"}},
  "credits": {"total_purchased_usd": 10.0, "total_used_usd": 0.42, "balance_usd": 9.58},
  "policy_version": 1,
  "high_allowance": true,
  "high_allowance_basis": "credits.total_purchased_usd 10.00 >= credit_threshold_usd 10.00 (policy@v1)",
  "observed_daily_peak": 212,
  "errors": []
}
```

- `secret_ref` is the reference string, never the value.
- `openrouter_account.derive_high_allowance(key, credits, policy, ledger)`
  sets `high_allowance` from the policy's own criterion, purchased credits, in
  this order:
  1. **Credits readable** (`credits.total_purchased_usd` is a number) and the
     policy has a non-null `credit_threshold_usd`: `high_allowance =
     total_purchased_usd >= credit_threshold_usd`. Basis:
     `"credits.total_purchased_usd X >= / < credit_threshold_usd T (policy@vN)"`.
  2. **Credits unreadable**: `true` if the ledger shows a UTC day with more
     charged free requests than `daily_free_requests_low` (observed-cap
     evidence; basis `"ledger: N requests on <day> > low cap L"`), else `null`.
     Without credits or that evidence the tier is unknown, never inferred.
  `key.is_free_tier` is never used to set `high_allowance`. It is only a
  cross-check: when it disagrees with the derived value in either direction
  (`is_free_tier false` but `high_allowance false`, or `is_free_tier true` but
  `high_allowance true`), `errors` gets
  `"discrepancy: key.is_free_tier=<v> but high_allowance=<v> (<basis>)"`.
  Ledger evidence that contradicts a credits-based `false` (a day above the
  low cap while purchases are below the threshold) is recorded the same way as
  `"discrepancy: ledger observed cap ..."`. Discrepancies are surfaced, not
  guessed away.
- A remaining balance (`balance_usd`) below the threshold says nothing about
  the allowance by itself and is never used to set `high_allowance`.

### Quota ledger event (`free_quota.py`)

One JSON line per free request attempt, appended to `ledger.jsonl`:

```json
{
  "schema_version": "agent-os/free-quota-event/v1",
  "event_id": "FQE-20261001T120317Z-7c2e9a41",
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
- `event_id` = `FQE-<ts compact>-<8 hex random>`, assigned when the attempt is
  appended. It is unique across concurrent priority/swarm/backfill attempts
  (unlike `ts`, which has one-second precision).
- `validator_passed` / `accepted` are `null` until known. A later
  `{"type": "verdict", "ts", "event_id", "validator_passed", "accepted",
  "escalated"}` line can complete them, so the ledger stays append-only. The
  verdict's `event_id` names the attempt it completes; the last verdict for an
  `event_id` wins, and a verdict naming an unknown `event_id` is ignored and
  reported in the metrics `errors`.
- Attempt events are the lines with no `type` field. Only attempt events are
  charged against allowance and counted as requests in metrics and in
  specialization `n`. Verdict lines are never charged or counted; they only
  fill in the fields of their attempt.
- `lane` is `priority | swarm | backfill`.
- `tokens` uses the `usage.normalized` accuracy labels. No prompt or output text
  is ever stored.
- The governor counts the day's attempt events (no `type` field) with
  `ts >= last reset` as spent allowance. When `failed_requests_count` is true, every outcome counts. A
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
  "evidence": ["local:free-compute/ledger.jsonl#FQE-20261001T120317Z-7c2e9a41"]
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
  - `proven`: `n >= proven_min` (default 20) and the Wilson lower bound is at
    least `proven_floor` (default 0.65), and not currently demoted (below). It
    gets priority traffic for the family.
  - `canary`: `n >= canary_min` and not `proven`. This covers a low Wilson
    lower bound, `n` still below `proven_min` whatever the bound, and a
    demoted model. Traffic is capped by `canary_share` (default 25%) and never
    displaces a proven specialist.
  - The three statuses partition every record: `n < canary_min` is
    `unproven`, otherwise `proven` if its rule holds, otherwise `canary`.
  - `n` counts attempt events only (see the quota ledger). Records key on
    `(task_family, model, revision)`, so a new revision starts at `n = 0` and
    is `unproven`.
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
  "policy_allowed_by": ["policy:openrouter/free-model-allowance@v2", "sensitivity:internal<=allowed", "data_policy:trains_on_prompts=false (policy@v2#data_policies[0], verified 2026-10-01)", "validators:2 declared"],
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
  "top_up": {"status": "not_needed", "shortfall_usd": null, "rationale": "account has high allowance (credits.total_purchased_usd 10.00 >= credit_threshold_usd 10.00)", "evidence": ["policy:openrouter/free-model-allowance@v1 verified 2026-10-01"], "errors": []},
  "errors": []
}
```

- `free_paid_fallbacks_avoided`: accepted free results that never escalated to
  a paid rung.
- `estimated_paid_cost_avoided_usd`: for each of those, the token counts times
  the per-token price of the paid route the router would otherwise have chosen.
  It is labeled "estimated" and carries its basis. Subscription routes count
  as 0 USD avoided (already paid).
- Denominators. `free_validator_pass_rate` divides by attempt events in the
  window whose `validator_passed` is non-null; `free_review_acceptance_rate`
  divides by attempt events whose `accepted` is non-null. Rate limits, quota
  exhaustion, timeouts and other attempts that never reached a validator or
  review are therefore not counted as quality failures. `free_retry_rate`,
  `free_escalation_rate` and `free_useful_progress_per_request` divide by
  attempted requests (attempt events) in the window, so wasted requests do
  lower them. A rate is `null` when its denominator is zero.
- In the example, 140 attempts produced 118 successes and 22 wasted or failed
  requests; the 0.84 validator pass rate and 0.9 review acceptance rate are
  over the attempts that actually reached a validator / review.
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
check: the model's data policy is `free_policy.data_policy_for(slug, revision)`
on the current effective policy (never the snapshot copy). For `internal`
sensitivity (repository code), `trains_on_prompts` must be `false`, unless the
project policy sets `allow_training_endpoints: true`. Unknown (`null`, no
matching entry, or an expired entry) counts as `true`. `public` work needs no
data-policy entry. With the shipped empty `data_policies`, internal work
therefore always escalates (`reason: "data_policy: unknown"`); this is the
intended conservative default, not an error. The route-decision example above
assumes a later policy version (`@v2`) that has a verified entry.

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
  `account.high_allowance is false` with the credits basis (rule 1 above, so
  `total_purchased_usd < credit_threshold_usd`), the current policy is
  verified (not stale) with a non-null `credit_threshold_usd`, and no ledger
  observed-cap discrepancy is recorded. The alert states the exact shortfall
  `shortfall_usd = round(credit_threshold_usd - total_purchased_usd, 2)`
  (always > 0 here), the allowance it would unlock (`daily_free_requests_low`
  -> `daily_free_requests_high`), the policy `source_url` and `verified_at`,
  and the account read time. An `is_free_tier` discrepancy does not suppress
  the alert (the verified policy criterion is purchases); it is copied into
  the result's `errors` so the operator sees it. The alert says that Agent OS
  will not buy credits: the operator tops up in the OpenRouter console.
- `unknown`: `high_allowance` is `null`, the policy is stale, purchased
  credits are unreadable, or a ledger observed-cap discrepancy contradicts a
  credits-based `false` (the published policy may be out of date).
  `shortfall_usd` is `null`, the reason and any discrepancies are in `errors`,
  and no alert is sent. This is shown in the CLI/GUI with the reason and is
  never sent as an alert.
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

## Engine integration (free_routing_enabled)

Status: decision record for IMP-0015 / ORCH-0038 (2026-10-02). The implementer
tasks follow this section. It wires `free_routing.decide` / `escalate` into
`engine.py` behind one opt-in run-policy flag and fixes the metrics findings
accepted at the `fcb-metrics` gates (R5-1 to R5-5).

Prior art: `agent-os orchestrate prior-art lookup "free-first model routing
with validator-gated escalation"` (2026-10-02) returned PA-openrouter-api
(INVESTIGATE), PA-llmrouter / PA-aflow / PA-optuna (DEFER), PA-crewai (REJECT),
PA-hf-hub, PA-pydantic-ai and PA-ragas (BORROW, none for routing). Nothing
covers validator-gated free-first dispatch inside an existing scheduler. We
reuse our own primitives (`router.select`, `_next_rung`, the run ledger,
`free_quota.Governor`) and add no dependency.

### Run-policy flag

- `model.DEFAULT_POLICY["free_routing_enabled"] = False`, added to the boolean
  list in `model._check_policy`. It is operator-only like `allow_paid_spend`:
  planners cannot set run policy.
- The engine reads it as `bool(record["policy"].get("free_routing_enabled"))`,
  so records created before the flag existed behave as off.
- **Off (the default) is byte-for-byte the current behavior.** With the flag
  off, `_launch` and `_validation_failed` do not import or call
  `free_dispatch`, read no `free-compute/` file, write no free ledger line and
  emit no new ledger event. Node records gain no new keys.

### Module `src/agent_os/orchestrator/free_dispatch.py`

Pure functions with no model calls and no network. Only `load_default` reads
disk. Exact signatures:

```python
def task_view(record: dict, node: dict) -> dict
@dataclass
class FreeInputs:
    catalog: dict            # catalog snapshot ({"models": [...]} at minimum)
    specializations: list    # free_specialization records
    governor: Any            # free_quota.Governor (or a fake with can_spend/remaining/record)
    project_policy: dict     # free_policy effective record + protected_globs + source
    @classmethod
    def load_default(cls, home: Path | None = None) -> "FreeInputs"
def decide_for_node(record: dict, node: dict, inputs: FreeInputs) -> dict
def selection_for(decision: dict, registry: router.ProviderRegistry) -> dict | None
def after_failure(node: dict, failure: dict, registry: router.ProviderRegistry, governor: Any) -> dict
```

- `task_view(record, node)` maps node fields to the `free_routing` task shape:
  `role`, `effort`, `capability_class`, `scope` (the node's file scope),
  `validators` (`node["validators"]`, else `record["policy"]["default_validators"]`,
  the same fallback the engine uses to validate), `task_family =
  node.get("task_family") or node["role"]`, `sensitivity` =
  `(node.get("requirements") or {}).get("sensitivity")` when it is a
  `workload.SENSITIVITY` value, else `"internal"`; `run_id`, `node_id`, and
  `lane: "priority"`. A node whose `requirements.deployment` excludes `"api"`
  (the deployment free OpenRouter providers run under) is given sensitivity
  `"private"`, so it fails eligibility with a named reason instead of failing
  later in `selection_for`. No other field is invented.
- `FreeInputs.load_default(home)` reads, from `<orchestrator home>/free-compute/`
  unless `home` is given: the catalog cache through `free_catalog`'s cache
  reader, **never `free_catalog.discover`** (the engine must not touch the
  network); `specialization.json` (a list of records); `free_policy.load()` for
  the effective policy; `account.json` for `high_allowance`; and a
  `free_quota.Governor(policy, high_tier=<high_allowance>, home=home)`.
  `project_policy` is the effective policy plus `protected_globs =
  control_plane.protected_globs()` (the canonical list; run-level
  `protected_paths_allowed` grants never extend to free routes) and `source =
  "policy:openrouter/free-model-allowance@v<version>"`. On **any** exception
  it returns `FreeInputs({"models": []}, [], <governor that refuses>,
  {"protected_globs": [...]})`, so `decide` escalates with `"no usable free
  model: catalog empty"`. It never raises.
- `decide_for_node(record, node, inputs)` returns `free_routing.decide(
  task_view(record, node), catalog=inputs.catalog,
  specializations=inputs.specializations, governor=inputs.governor,
  project_policy=inputs.project_policy)` unchanged. It adds nothing and never
  raises: an exception becomes an `escalate` decision with reason
  `"free routing error: <ExceptionType>"`.
- `selection_for(decision, registry)` returns `None` unless `decision["route"]
  == "free"`. Otherwise it finds the first provider, in registry order, for which
  `decision["model"]` is one of `provider["models"].values()`, and returns a
  selection shaped like `router._selection`: `resolved: True`, `provider`,
  `adapter`, `model` (the exact `:free` slug), `capability_class` (the class
  key that maps to that slug), `effort` and `provider_effort` from the
  decision's effort, `overridden: False`, `reason: "free route: " +
  decision["reason"]`, `notes: []`, `profile`, plus `free_route: True`. With no
  such provider it returns `None`.
- `after_failure(node, failure, registry, governor)` calls
  `free_routing.escalate(node["free_route"], failure, registry=registry,
  governor=governor, role=node["role"], effort=node["effort"],
  requirements=node.get("requirements"))` and returns one of:
  - `{"action": "free", "decision": step}` when the step is
    `route == "free"` (an alternate free model);
  - `{"action": "router", "capability_class": C, "effort": E, "decision":
    step, "reason": step["reason"]}` when the step is `route == "router"` or
    `"wait"`. `C` is the rung's class (`step["selection"]["capability_class"]`
    for `router`, the node's class for `wait`); `E` is the node's effort. The
    engine uses only `C`/`E`, never the provider `escalate` named, so the
    normal `select()` path and its paid-spend, exclusion and approval gates
    still choose the provider;
  - `{"action": "exhausted", "decision": step}` when the ladder is exhausted.

### Engine hook points (`src/agent_os/orchestrator/engine.py`)

The `Orchestrator` constructor takes an optional `free_inputs` (a `FreeInputs`
or a zero-argument callable returning one). Tests inject fixtures through it.
Otherwise the engine calls `FreeInputs.load_default()` lazily, at most once per
`step()`, and only when a run with the flag on reaches a hook.

1. **`Orchestrator._launch`**, after `if node["execution_path"] ==
   "deterministic": return self._run_deterministic(...)` and before `selection
   = select(...)`. Runs only when the flag is on and `node["role"] in
   {"implementer", "test_author"}`:
   - If `node.get("free_route")` exists with `free_state == "escalated"`, skip
     the hook (the node is back on the normal path).
   - Else, when `node.get("free_route")` exists with `free_state == "free"`,
     use that decision (a retry on a chosen alternate). Otherwise call
     `decide_for_node`, store the decision in `node["free_route"]` and emit
     the `free_route_decision` ledger event.
   - On `route == "free"`, call `selection_for`. A `None` result, or a provider
     in `node["excluded_providers"]` or not available under
     `self.availability()`, sets `decision["route"] = "escalate"` with reason
     `"no registry provider serves <slug>"` (or `"free provider <id> excluded"`
     / `"... unavailable"`), sets `free_state = "escalated"` and falls through to
     `select()`. Otherwise the selection replaces the `select()` result.
     `_paid_blocked` does not apply to it: by invariant 3 the model is free on
     the current snapshot. Everything after that (cheaper-reset wait, context
     misfit, prompt, `routing_decision` / `model_selected` events, launch) is
     unchanged. A context misfit excludes the provider as today, and the next
     launch then escalates through the rule above.
   - On `route == "escalate"`, set `free_state = "escalated"` and continue to
     `select()` unchanged.
   - Counterfactual paid route (needed by R5-2): when the route is `free`, the
     engine also runs the same `select(...)` call it would otherwise have
     made. This is deterministic and makes no model call. It stores
     `{"provider", "model", "capability_class", "subscription": not
     is_paid(provider)}` as `node["free_route"]["paid_route"]`, or `None`
     when that selection is unresolved.
2. **`Orchestrator._validation_failed`**, after `_push_failure` and
   `_fallback_to_model`, before the `_next_rung(node)` block. When the flag is
   on and `node.get("free_route", {}).get("free_state") == "free"`, call
   `after_failure(node, {"kind": "validator_failed", "verified_outputs":
   ...}, self.registry(), governor)`:
   - `free`: replace `node["free_route"]` with the step (`free_state` stays
     `"free"`), set `state = "FAILED_RETRYABLE"`, `selection = None`, and
     `wait_reason = "validator failed; alternate free model <slug>"`.
   - `router`: set `free_state = "escalated"`, `node["capability_class"] =
     C`, `node["effort"] = E`, `state = "FAILED_RETRYABLE"`, `selection =
     None`, and `wait_reason = "validator failed; escalated from free to
     C/E"`.
   - `exhausted`: set `free_state = "escalated"` and fall through to the
     existing `_next_rung` block unchanged.
   Free transitions do not increment `node["escalations"]` and do not advance
   `ladder_step`, so the node keeps its full paid ladder (`max_escalations`).
   `alternate_free_max` (default 1) plus the single step off the free pool
   bound the extra attempts. Each transition emits `free_route_escalated` and
   the existing `model_escalated` event (`from: "free:<slug>"`).
3. **`Orchestrator._fail`** (provider failures such as `rate_limited`,
   `unavailable` or `process_error` on a free-routed node) applies the same
   `after_failure` rule before its `_next_rung` call, with `failure["kind"]`
   set to the failure kind.

### Telemetry

- Run ledger (`self.ledger.emit`, so `telemetry.jsonl`), only when the flag is
  on: `free_route_decision` with `role`, `task_family`, `route`, `model`,
  `reason`, `failed_checks` (from `eligibility`), `catalog_snapshot`, `quota`
  and `paid_route`. `free_route_escalated` carries `from_model`, `to`
  (`free:<slug>`, `class:<C>/<E>` or `exhausted`), `failure` and `reason`. No
  prompt or output text is logged.
- Free quota ledger (`inputs.governor.record`), only for workers launched on a
  free route. When the result is collected (the `_record_telemetry` call sites),
  the engine writes an attempt event (schema above) with `outcome` mapped from
  the result (completed -> `success`; timeout -> `timeout`; rate limit / quota
  failure -> `rate_limited` / `quota_exhausted`; unparseable result block ->
  `invalid_output`; anything else -> `provider_error`), `tokens` from
  `result.usage`, `lane: "priority"`, `paid_route` from the decision, and
  `validator_passed` / `accepted` set to `null`. Its `event_id` is stored in
  `node["free_route"]["event_id"]`. Later facts append verdict lines: after
  validation, after review (`accepted`), and when `after_failure` moves off the
  model (`escalated: true`). Each verdict line carries **all three fields known
  so far**, because the last verdict for an `event_id` wins.
- `TelemetryEvent` gets no new field. The free route is visible because its
  `provider` and `model` are the free selection.

### Metrics fixes (`free_metrics.py`, R5-1 to R5-5)

- **R5-1.** A verdict whose `event_id` names no attempt in `ledger_events`
  adds `"verdict for unknown event_id <id>"` to `errors`, one entry per
  distinct id, sorted. A verdict without `event_id` adds `"verdict without
  event_id"` once. Neither changes any count.
- **R5-2.** The signature is `report(ledger_events, *, prices=None)`. The
  `paid_model` parameter is removed: passing it is a `TypeError`. Each
  accepted, non-escalated attempt is priced from its own `paid_route` (written
  by the engine as above): a `subscription: true` route adds 0 USD and counts
  as priced; otherwise the cost is `(tokens.input * prices[model].input +
  tokens.output * prices[model].output) / 1e6`, using
  `model_prices.fetch_prices()["prices"]` per-million figures. The basis
  string is `"per accepted free result: tokens x price of the paid route
  router.select would otherwise have run"`.
- **R5-3.** The estimate is partial, never all-or-nothing:
  `estimated_paid_cost_avoided_usd = round(sum over priceable results, 6)`
  when at least one result is priceable, else `null`. A new field
  `estimated_paid_cost_coverage: {"priced": k, "accepted": n}` is added. Each
  unpriceable cause adds one aggregated `errors` entry:
  `"estimated cost: <m> accepted result(s) without tokens"`,
  `"... without paid_route"`, `"... no price for paid model <model>"`, and
  `"estimated cost unavailable: no prices supplied"` when `prices` is `None`
  and a non-subscription result needs it. Tokens are usable only when
  `tokens` is an object whose `input` and `output` are both non-negative `int`
  (not `bool`). `0` counts as a value, not as missing.
- **R5-4.** `prices` must be `None` or a mapping of `str` model ->
  mapping. Its `input` and `output` must each be a finite, non-negative
  `int`/`float` (not `bool`) or `None` (unpriced; that model counts as no
  price). Other keys such as `cached_input` are ignored. The report never
  raises on bad data: a non-mapping `prices` adds `"invalid prices: expected
  an object of model -> {input, output}"` and prices nothing; a bad entry adds
  `"invalid prices: <model>: <field> must be a non-negative number"` and is
  treated as absent.
- **R5-5.** Tests in `tests/test_free_metrics.py` assert exact values, not just
  presence or truthiness:
  - an unknown-id verdict is reported and changes no count;
  - `report(events, paid_model="x")` raises `TypeError`;
  - mixed paid routes price per event: two models at different prices give the
    exact sum, and a subscription route adds 0 and counts as priced;
  - one accepted event without tokens gives a partial sum and `coverage
    {"priced": 1, "accepted": 2}` plus the error;
  - each invalid `prices` shape is reported (non-mapping, string price, `bool`,
    negative, `NaN`);
  - the caller's events are not mutated;
  - escalated or non-accepted events are never priced.

### Tests for the integration (no network, no model calls)

- `tests/test_free_dispatch.py` (pure). `task_view` field mapping, including
  the `task_family` fallback, the sensitivity default and the deployment
  narrowing. `load_default` on an empty or corrupt home returns an empty
  catalog and never raises, and never calls `discover` (patched to raise).
  `selection_for` finds the serving provider and returns `None` when none
  serves the slug. `after_failure` returns each of `free` / `router` /
  `exhausted`.
- `tests/test_engine_free_routing.py`, with a fake adapter and injected
  `FreeInputs` (fixture catalog with one proven model and a registry provider
  serving its `:free` slug):
  - **Default off.** `free_dispatch.decide_for_node` and `load_default` are
    patched to raise, and the run still completes. Selections and the ledger
    event types match a run made without the patch, and no `free_route` key
    or `free-compute/` file exists.
  - **On, eligible.** The implementer launches on the free provider/model, a
    `free_route_decision` event with `route: "free"` and a `paid_route` is
    emitted, and an attempt event is written to the free ledger.
  - **On, validator fails.** The node relaunches on the alternate free model,
    then fails again and relaunches through `select()` at the escalated
    class. `node["escalations"]` stays unchanged across the free steps, and
    `free_route_escalated` events record each transition.
  - **On, ineligible** (reviewer role, high effort, or a protected path). The
    node routes exactly as with the flag off, and the decision event names the
    failed check.
  - **On, no provider serves the slug.** The decision records route
    `escalate` with reason `no registry provider serves <slug>`, and the node
    uses `select()`.

## Test plan (no network)

- A fake opener serves fixture `/models`, `/key` and `/credits` payloads.
  Tests check that free models are discovered by `is_free`, including that a
  model with `"0"` prompt/completion but a non-zero (or unknown extra) pricing
  key, a missing or empty `pricing`, or an unparseable value is excluded; that
  raw pricing keys round-trip through the snapshot; that
  adding/removing/changing a model yields the right diff with no code edit, and
  that an identical fetch writes no new snapshot.
- Policy: overrides merge; stale policy uses the low allowance and suppresses
  alerts. Data policy: with empty `data_policies`, `public` work is eligible
  and `internal` work escalates with `"data_policy: unknown"`; an exact-slug
  entry beats a prefix; a revision-pinned entry does not apply to a swapped
  revision; an expired entry resolves to unknown.
- High allowance: `is_free_tier false`, `total_purchased_usd 5`, threshold 10
  -> `high_allowance false`, `is_free_tier` discrepancy in `errors`, top-up
  `recommended` with `shortfall_usd 5.00`. `is_free_tier true`, purchases 10,
  threshold 10 -> `high_allowance true`, discrepancy recorded, `not_needed`.
  Credits unreadable with a ledger day above the low cap -> `true`; credits
  unreadable without it -> `null`.
- Governor: RPM window, daily budget at both tiers, failed requests charged,
  reset boundary, reserve, retry budget, open circuit.
- Eligibility: each of the five checks fails alone.
- Ladder order is fixed. Partial outputs are preserved.
- Specialization: status transitions and demotion; `canary_min <= n <
  proven_min` with a Wilson lower bound at or above `proven_floor` is
  `canary`. A swapped revision starts a new record with `n = 0` and is
  `unproven`. Verdict lines do not change `n`.
- Ledger: verdict lines complete their attempt by `event_id` (two attempts in
  the same second stay distinct) and are never charged by the governor.
- Metrics arithmetic on a fixture ledger.
- Top-up: the four statuses, including the case "balance USD 2 but
  total_purchased_usd 10 >= threshold 10 -> not_needed", an exact shortfall,
  and the case "purchases below threshold but a ledger day above the low cap
  -> unknown, discrepancy recorded in errors, no alert".
- Invariants: the account adapter rejects non-GET and non-allowlisted URLs. No
  secret value appears in any persisted file, decision, report or exception
  (the test seeds a sentinel key value and scans outputs). A route never names
  a model for which `is_free` is false, and swarm/backfill refuse dispatch
  when the latest snapshot's pricing for the model fails `is_free`.

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
