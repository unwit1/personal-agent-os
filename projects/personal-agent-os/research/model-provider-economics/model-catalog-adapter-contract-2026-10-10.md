# Source contract for scalable public model metadata ingestion

2026-10-10. Research-backed implementation contract for the existing IMP-0015 Research Radar. **No network fetcher installed or run in Agent OS in this research pass.**

## High-priority public machine catalogs

### Models.dev — recommended foundation

Official source: [anomalyco/models.dev](https://github.com/anomalyco/models.dev), MIT; [documented schema and URLs](https://github.com/anomalyco/models.dev#api).

| URL | Purpose |
|---|---|
| `https://models.dev/models.json` | **Provider-neutral weight/model identity**: originating lab/model ID, release, license, open weights, weight links, built-in benchmark evidence |
| `https://models.dev/api.json` | **Provider+endpoint** catalog, exact routed ID and provider-specific API limits/prices/capability flags |
| `https://models.dev/catalog.json` | Combined model identity and provider serving information, includes canonical model IDs where known |
| `https://models.dev/api.json?type=all` | Full supported specialized model types, including `decision` instead of default filter |

Source implementation stores model facts under `models/{org}/{model}.toml`, provider endpoints under `providers/{provider}/models/{model}.toml`. Provider-specific records can explicitly refer to `base_model`; `canonical_model_id` in generated output connects relay endpoint to original creator. Provider override wins where context/price/features differ. Models.dev expresses price in **USD per million tokens** using `cost.input`, `cost.output`, `cost.cache_read`, `cost.cache_write`; usage flags `reasoning`, `tool_call`, `structured_output`, `open_weights`; limits `limit.context/input/output`; modalities `modalities.input/output`; licensing & `weights` data in model identity. This is a key reason not to flatten into a simple model-name+cost row.

### LiteLLM metadata (secondary crosscheck)

Registry: [LiteLLM model price/context JSON](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json), schema [here](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.schema.json). Contains provider-prefixed variants and price fields whose **units may differ from Models.dev**: LiteLLM commonly represents `input_cost_per_token`, `output_cost_per_token` (USD/token). Multiply by one million only for a normalized USD/1M quote after verifying the field definition. Its regex fallback generalizations are *not actual served models*; ignore for definitive routing. The registry is community maintained, not authoritative over direct provider quotes. Do not load whole repo/dataset into prompts.

### Provider and benchmark cross-checks

- [OpenRouter List Models](https://openrouter.ai/docs/api/api-reference/models/get-models) and per-model endpoints: live price, `supported_parameters`, context and available providers. Output can vary per provider. An endpoint must accept `tools`, not merely say the weights know function calling.
- [Simon Willison llm-prices](https://github.com/simonw/llm-prices): `https://www.llm-prices.com/current-v1.json` and historical-v1 effective-date records, USD per million. Lower frequency historical sanity check.
- [Artificial Analysis Data API](https://artificialanalysis.ai/data-api): independent model benchmark and inference performance API; inspect access/licensing before use. No free unrestricted API is assumed.
- [Hugging Face Hub official publisher collections](https://huggingface.co/Qwen/models): weights/revisions/license and checkpoint metadata, not hosted inference prices.

## Zero-dependency ingestion requirements (Python standard library feasible)

1. Discover source config from existing Research Radar. Allowlist HTTPS domains/paths; honor conditional GET (`ETag`/`Last-Modified`), gzip and content-length/max-size. Do not store or log auth values.
2. Verify response status/content type, schema and numeric bounds; reject NaN, negative, ambiguous billing units, missing canonical model IDs and malformed context limits. HTML error or stale cached text isn't a model catalog.
3. Normalize separate model, weight variant, endpoint, quote, plan, quota, benchmark entities. Link publisher canonical ID where verified; do not guess associations from names or suffixes.
4. Compare endpoint metadata from primary provider before trusting secondary feed when both exist. Record `source`, `timestamp_utc`, `source_revision_or_etag`, `content_sha256`, `model_id`, `publisher`, `endpoint`, `confidence`, and precise field lineage.
5. On disagreement: append contradiction event; keep current proven routing until manually or deterministically resolved. Never silently replace $0.06/$7 with $0.49/$1.56 or vice versa.
6. On upstream disappearance: mark endpoint as missing/unavailable candidate, not instantly deleted; timestamp status and block routing on stale unresolved availability.
7. Quota/terms metadata from billing plans must be tracked separately. An interactive coding plan is not automatically legal or technically usable for unattended API tasks.
8. Run fixtures and reproducible unit tests with no outgoing network; compare normalized objects and price arithmetic. Canary read-only live fetch can happen later on the operator's trusted machine.
9. Store compact structured snapshots with source links and distinct historical versions, preferably outside hot context; provide filtered queries such as `models.find({coding:true,tools:true,max_cost:...})`.
10. Before promoting a new endpoint: applicable license/terms/privacy, budget approval, runtime tool probes, measured EVS/CAP success and no regression. No paid request solely because the catalog discovered a cheap model.

## Why this beats exhaustive one-off scraping

An exhaustive static list becomes obsolete quickly; Qwen's official publisher catalog alone lists hundreds of models/variants. Combining machine-readable catalogs with publisher/source-of-truth checks covers much more than manually copying every model page, while preserving correct unit conventions and licensing. Success should be measured by **source coverage, update freshness and validated active endpoints**, not by number of names in a prompt.

**Validation status:** URL and data contracts researched via primary documentation. No authenticated OpenRouter catalog API, Models.dev API JSON payload, or official LiteLLM JSON payload was executed or parsed in this pass. Until fetchers are implemented, data in the preceding snapshot files remains curated partial research.