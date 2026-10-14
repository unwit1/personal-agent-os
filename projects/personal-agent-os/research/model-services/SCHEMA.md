# Model service catalog: schema `personal-agent/model-service-catalog/v1`

Canonical file: `projects/personal-agent-os/research/model-services/catalog.json` (in Git; it holds no secrets).
Raw research behind it: `projects/personal-agent-os/research/model-services/raw/batch-*.json`. These are worker outputs, kept verbatim as provenance.
Loader and validator: `src/agent_os/orchestrator/model_services.py`.

Ground rules (the validator enforces those it can):
- Every service, model and media record has `sources` (>= 1 entry, each {url, title, accessed: YYYY-MM-DD, official: bool}). A service needs at least one `official: true` source.
- Unknown stays unknown. A field that is not verified is `null`, and its field name appears in that record's `unknown` list. Do not invent values.
- `reviewed_at` (YYYY-MM-DD) appears at the top level and on each service. A service is *stale* when it is older than `review_interval_days`; the validator reports a warning, not an error.
- Refusal behaviour is kept separate from the other properties: `open_weights` (are the weights downloadable), `license`, and `refusal_profile`: `standard`; `low` (fine-tuned or prompted for fewer refusals); `abliterated` (refusal-direction removal, documented by the author); or `unknown`. Never infer `abliterated` from a name alone; it needs `refusal_evidence`.
- Public benchmarks live only in `benchmarks_prior` and are labelled priors. Suitability per task family is `suggested_prior_task_families`; it is not evidence. Measured Agent OS evals (CAP/EVR) decide routing.

```jsonc
{
  "schema": "personal-agent/model-service-catalog/v1",
  "reviewed_at": "2026-10-12",
  "review_interval_days": 60,
  "services": [{
    "id": "nanogpt",                       // kebab-case, unique
    "name": "NanoGPT",
    "category": "subscription_allowance",  // subscription_allowance | hosted_api | custom_hosting | gateway
    "homepage": "https://nano-gpt.com",
    "reviewed_at": "2026-10-12",
    "integration_status": "preset_ready",
      // preset_ready        : openai_chat endpoint + at least one plan whose terms allow automation -> `services add` works
      // preset_restricted   : preset exists but needs --ack-terms (automation_allowed is null/unclear)
      // bridge_claude_code  : only usable through an approved client (Claude Code) -> claude_code bridge preset
      // catalog_only        : documented, but no safe/allowed automated preset (e.g. terms forbid automation, or non-chat API)
      // deferred            : needs something not done here (paid provisioning, custom container, KYC)
    "integration_notes": "string",
    "deployment": "subscription",          // subscription | api | serverless | gpu_pod | local  (model_profile.DEPLOYMENTS)
    "modalities": ["text", "code"],        // model_profile.MODALITIES plus: rerank, tts, asr, video
    "endpoints": [{
      "id": "subscription",                // unique within the service; "default" for the main one
      "protocol": "openai_chat",           // openai_chat | anthropic_messages | vendor
      "base_url": "https://nano-gpt.com/api/subscription/v1",   // EXACTLY as documented
      "path_style": "auto",                // endpoints.PATH_STYLES: auto | root | append_v1
      "models_path": "/models",            // relative to the api root; null when no documented list
      "models_list_requires_auth": false,  // true | false | null
      "secret_ref": "secrets://nanogpt/default",
      "notes": "string"
    }],
    "plans": [{
      "id": "subscription",
      "name": "NanoGPT subscription",
      "usd_per_month": 8,                  // number | null
      "endpoint": "subscription",          // endpoint id this plan bills through
      "billing": {                         // the model_profile billing block, verbatim
        "mode": "allowance",               // seat | allowance | metered | credits | free | local | per_gpu_time
        "plan": "subscription",
        "allowance": {"unit": "requests", "amount": null, "reset_window": "monthly"},
        "overage": "blocked",              // blocked | metered | unknown
        "metered_triggers": ["explicit provider selection"]
      },
      "automation_allowed": true,          // true | false | null (null = terms unclear -> preset needs --ack-terms)
      "allowed_clients": null,             // null = any client; else a list, e.g. ["Claude Code", "Kimi CLI"]
      "notes": "string"
    }],
    "privacy": {"training_on_prompts": "unknown", "retention": null, "zdr": null, "weights_location": "third_party"},
    "restrictions": {"disallowed_uses": ["string"], "notes": "string"},
    "quotas": {"rate_limits": "string|null", "concurrency": "string|null", "context_caps": "string|null"},
    "models": [{"id": "exact API model id", "catalog_model": "models[].id or null", "open_weights": true, "license": "string|null",
                "refusal_profile": "standard|low|abliterated|unknown", "context_window": 131072, "modalities": ["text"]}],
    "findings": [{"claim": "string", "status": "confirmed|contradicted|unverified", "evidence": "string", "source": "url"}],
    "unknown": ["field names"],
    "sources": [{"url": "...", "title": "...", "accessed": "2026-10-12", "official": true}]
  }],
  "models": [{
    "id": "qwen3-coder-next", "name": "...", "hf_repos": ["Qwen/..."], "family": "qwen", "base_model": "string|null",
    "params_total_b": 80, "params_active_b": 3, "license": "apache-2.0", "open_weights": true, "context_window": 262144,
    "released": "YYYY-MM-DD|null", "refusal_profile": "standard", "refusal_evidence": "string|null", "abliteration_method": "string|null",
    "vs_base": "string|null", "served_by": [{"service": "service id", "model_id": "exact id"}],
    "benchmarks_prior": [{"name": "...", "score": "...", "source": "url"}],
    "suggested_prior_task_families": ["coding", "automation", "research", "extraction", "lore", "creative"],
    "unknown": [], "sources": [], "notes": "string"
  }],
  "media": [{
    "id": "...", "name": "...", "task": "image_generation|image_editing|asr|diarization|tts|voice_clone|embedding|rerank",
    "hf_repo": "string|null", "open_weights": true, "license": "string|null",
    "served_by": [{"service": "service id", "model_id": "...", "endpoint": "path", "pricing": "string|null"}],
    "local_feasible": "string|null", "unknown": [], "sources": [], "notes": "string"
  }]
}
```

## Preset rules (`model_services.preset_entry`)

- The endpoint must be `openai_chat` (adapter `openai_api`). The entry uses `model_profile.endpoint_entry`, passing base_url, path_style, secret_ref, deployment, the plan's billing block, privacy, model license/open_weights/refusal_profile/context_window (from catalog `models` when linked, otherwise `unknown`), and roles (default `["inline"]`).
- The plan's `automation_allowed` decides what happens: `false` refuses; `null` needs `ack_terms=True`, recorded in the entry as `options.terms_ack = {"service", "plan", "at"}`; `true` is OK.
- `allowed_clients` decides it too. When it is non-null and does not list `"any OpenAI-compatible client"`, the preset refuses with a message. If Claude Code is listed and the service has an `anthropic_messages` endpoint, the message points to `bridge_entry`.
- `bridge_entry(service, plan, model_map)` builds a `claude_code` adapter entry. It sets `options.env = {"ANTHROPIC_BASE_URL": <anthropic endpoint base_url>, ...model env}` and `options.secret_env = {"ANTHROPIC_AUTH_TOKEN": <secret_ref>}`, with the profile and billing taken from the plan. Default roles are `["inline", "planner"]`; coding roles only when passed explicitly. Default costs are 1.0 per class, so a new entry does not take over routing until the operator lowers the cost.
- Default costs are 1.0 per class, overridable. Default max_concurrency is 2.
- Never add provider-selection or routing parameters to requests. Example: NanoGPT bills explicit provider selection as pay-as-you-go.

## Discovery (`model_services.discover`)

A read-only `GET <api_root><models_path>` with Bearer auth from the endpoint's `secret_ref`, sent only when the endpoint requires auth or when a key is configured. It never POSTs. It returns `[{"id", "owned_by", "context_length"}]`. It caches `{fetched_at, service, endpoint, models}` to `<orchestrator home>/service-models/<service>--<endpoint>.json`. It errors clearly when `models_path` is null or the needed key is missing. The key never appears in output, errors or cache.
