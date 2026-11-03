# Continuous Model + Subscription Intelligence (IMP-0015 extension)

Updated 2026-10-10. **Proposal / design, not deployed.** Source-backed manual model research in this directory is a seed; it cannot ever be globally exhaustive or permanently current. Automatically ingest canonical machine-readable catalogs and run task-specific canary evals to keep agent information up to date.

## New data / references added this research pass

- 77 distinct publisher-named open-weight model/quantization artifacts across 13 families, source provenance to publisher model cards/collections. Open weights **not necessarily OSI open source**. See `open-weight-artifacts-2026-10-10.json`.
- 41 separate Gemma4, GLM5+, and gpt-oss benchmark results, carefully marked publisher/Hub source rather than Orchestrator outcomes. See `open-weight-benchmark-evidence-2026-10-10.json`.
- 31 quoted Together/Fireworks/Cerebras model price pairs from dated official price pages (do not infer API ids). See `provider-official-api-quotes-2026-10-10.json`.
- 25 explanations of commercial access model, subscription or developer API terms/quotas (with explicit unattended-use eligibility). See `service-commercial-mechanics-2026-10-10.json`.
- 12 benchmark methodology/version entries (including evolution of Artificial Analysis v1.5 Coding Agent Index and v4.3.2 Intelligence Index). See `benchmark-methodologies-2026-10-10.json`.
- Paperclip/Gas Town related study: `../prior-art/paperclip-integration-analysis-2026-10-10.md`; structured prior art `../prior-art/discovery-paperclip-and-model-data-2026-10-10.json`.

These supplement—not replace—the previous 26 model quotes, 16 plans, 24 GPU rates, 24 previously recorded published benchmarks, and nine low-refusal API candidates.

## Source hierarchy and licensing

1. **Current official model/provider API metadata:** exact provider+model ID, endpoint parameters, modality, context, cache pricing, rates, provider/location. Highest authority for availability and price, still freshness-bound.
2. **Original creator/weight artifact:** Hugging Face model ID+revision, architecture/quantization, actual license (may be restrictive or custom), downloadable checkpoint. Source of 'open weights', not proof of hosting.
3. **Independent bench data:** Artificial Analysis Data API, LiveCodeBench, Terminal-Bench, controlled evals. Every result pinned to suite/harness/revision, reasoning effort, tool scaffold and date. Access/license conditions required.
4. **Aggregator secondary metadata:** [Models.dev](https://github.com/anomalyco/models.dev) public API `https://models.dev/api.json` and [LiteLLM price/context registry](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json), plus [Simon Willison's pricing history](https://github.com/simonw/llm-prices). Prefer small adaptive fields from third-party sources; retain disagreements rather than override trusted quotes.
5. **Community model cards/leaderboards and low-refusal claims:** mark publisher or community assertions, do not conflate with independent tests. Example Heretic derivatives must be evaluated independently from base model.

Never import raw external code, dependencies, models or benchmark corpora automatically merely by finding a new release. Verify copyright/license terms, permitted use and source pin before download or execution. Catalog research is metadata-only by default.

## Canonical data model

```text
PublisherModel: stable public weight ID, source, revision, family, total/active params, modalities, tokenizer, license, source provenance
WeightVariant: base model FK, modifier (base/instruct/quantized/LoRA/abliterated), revision/hash, format, tested runtime, license inheritance
ServingEndpoint: provider, exact endpoint API ID, region/privacy, capabilities (tools, streaming, JSON, context), rate limits, live health
PriceQuote: serving_endpoint FK, input/output/cache/context-tier prices, billing currency/unit, source, checked_at, effective dates, anomalies
Plan: provider, billing style [PAYG, seat, prepaid, bundle, GPU, PTU], price, payment terms, refill behavior, expiry
PlanEligibility: permitted clients/workload types, interactive-only, unattended, production, multi-agent, key scope and terms URL/observed_at
QuotaWindow: 5h/day/week/month, unit type (requests/credits/tokens/concurrency), multiplier, reset timezone, burst, throttling evidence
PublishedEval: exact model/endpoint/revision, suite and version, harness, effort, publisher/third-party, score units, date, source
ObservedEval: CAP/EVR output with real task, verifier, actual cost, error/refusal, time, sample and provenance
ComputeQuote: GPU SKU/provider/memory, runtime and cold-start rates, disk/network, availability, utilization, memory fit
SourceObservation: retrieval URL, content hash, claimed modification time, time fetched, source type, confidence, contradiction links
```

Use stable IDs and relationships to avoid price inheriting across distinct providers and scores inheriting across weight variants. Version assertions and attach source evidence, never replace a contradictory quote silently.

## Provider-neutral adapters: non-mutating by default

```text
ResearchRadar.schedule(now)
  -> queue allowed sources by change frequency and retry budget
     OpenRouter GET /api/v1/models (+ model endpoints for native tool support, quote)
     Models.dev models JSON (with ETag, gzip, max response size)
     LiteLLM versioned cost map (hash/ETag), source only
     Hugging Face public model metadata / model card / revision
     curated official provider pricing pages or APIs
     benchmark Data API if legally authorized
     -> validate + normalize schema + dedup by source key
     -> compare to prior snapshot + create source change event
     -> quarantine malformed, revoked, conflicted or anomalous prices
     -> queue task-family canary eval of interesting model/provider pairs
     -> CAP/EVR benchmark; only after confidence & budget check propose promotion
```

HTTP read only, with conditional GET, retries/backoff, cap on bytes/requests, user agent and no credentials in logged URLs. Do not fetch unsupported sites by bypassing ToS, anti-bot or metering; skip gated benchmark APIs without approved entitlements.

## Scoring and auto-routing constraints

- **Before selecting price**, reject: disallowed subscription use, incorrect privacy/domain, no required endpoint-native tools, insufficient context/output, unsupported license, wrong region, unhealthy endpoints, exhausted quotas, no spend approval.
- Value of one job: `verified_success_probability` (Wilson lower bound where useful), validator cost and retries, p95 latency and provider uptime, incremental subscription opportunity cost, cumulative monthly spending.
- For a plan already bought: **marginal** cost may be near zero *until* limits/rolling-window tokens become scarce. Calculate quota opportunity cost and alternative API price rather than falsely setting all requests to $0.
- Refresh immediately before allocation: free route availability; provider actual endpoint, price, credit and rate limit, GPU quote/capacity. Detect a sudden order-of-magnitude price change and fail closed.
- Public benchmarks only shortlist candidates. Require paired Orchestrator task evals, no regression on correctness and authorization, and documented improvement in total cost/verified accepted task before promotion.
- Keep benchmark input prompt and tool schema exactly pinned. Refusal rate on allowed tasks is a separate metric from overall quality. Never let a low-refusal model approve its own privileged changes or expenditures.

## Work plan / definition of done

| Priority | Research/implementation step | Acceptance |
|---|---|---|
| P0 | Catalog adapter reading live OpenRouter, Models.dev and LiteLLM | Deterministic fixture tests, schema validation, caching, provenance, dedup, diff; no SDK dependency required |
| P0 | Subscription terms/limits registry | Explicit 5h/week/month windows, allowed-client type and no-unattended restriction, renewal/credit field, and fail-closed eligibility unit tests |
| P0 | Paperclip-style atomic work leases and scoped wake | Demonstrate no duplicate checkouts, no stale lease mutations and safe resume after crash in repeatable tests; integrate into existing Orchestrator IDs |
| P1 | Independent benchmark/API evidence ingestion | Normalize suite versions, source license, author, score/harness. No benchmark scores from model cards without attribution |
| P1 | Model/provider pair probe | Tool call, JSON schema, long context, latency/TTFT, availability, data handling: no silent prompt downgrade |
| P1 | Real-world coding A/B | Standard GLM vs Heretic on equal bounded benign tasks, followed by frontier open-weight candidates; >=10 tasks/family and repeated samples; cost/verified success |
| P1 | Paperclip shadow bridge | Read-only task synchronization with synthetic projects, no data leak, no duplicate state, no new paid subscriptions |
| P2 | Mobile run status, budgets, skills Studio concepts | Reuse Agent OS dashboard and eval registry; user-visible UI only after actual needs and tests |
| P2 | Historical drift/optimization radar | Cost/quality change alerts, weekly summaries, duplicate/failure analysis, no surprise routing promotion |

All changes must reuse `projects/personal-agent-os/roadmap/model-infrastructure-manager.md`, Orchestrator `CAP/EVR`, `docs/model-infrastructure.md`, and canonical security/approval mechanisms. This is **not a separate agent OS**. Protected evaluator assets must not change as part of a candidate test. Any new external paid usage requires operator approval.

## Coverage and gaps at end of this research pass

Covered a broad source-backed sample, not all published models or API services. Not done: full authenticated OpenRouter catalog inventory, 469-entry Qwen publisher catalog expansion, model card checkpoint sizes for every family, live per-endpoint rate limits, all subscription checkout/legal terms across countries, all independent benchmarks/leaderboard exports, runtime GPU throughput at working context/concurrency, local Orchestrator trials. These must remain explicitly **unknown** and be filled by vetted automated ingestion and measured evaluation rather than model guessing.
