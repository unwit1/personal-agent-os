You are a research worker for the Agent OS Orchestrator (a personal multi-model coding/automation router). Today is 2026-10-12.
Use live web search and open OFFICIAL sources (vendor docs, pricing pages, terms of service, API references, model cards on Hugging Face). Third-party blogs are acceptable only as clearly-labelled secondary sources.
Do NOT sign up, log in, purchase, or enter any credential. Read-only research only. Do not run shell commands except to read nothing; no files need to be written.

Rules:
- Every factual field must be backed by a source URL in that record's "sources" list (with the date you accessed it, 2026-10-12). If you cannot verify a field from an official page, set it to null and add the field name to "unknown". Never guess. Keep unknown capabilities unknown.
- Distinguish: open-weight availability, license, low-refusal tuning (fine-tuned to refuse less), and actual abliteration (refusal-direction removal). Do not conflate them.
- Record API base URLs EXACTLY as documented, including whether they already include /v1 or use another prefix (e.g. /api/v1, /openai/v1, /compatible-mode/v1, /api/subscription/v1, /inference/v1). Record the model-list endpoint (GET .../models) if documented, and whether it needs auth.
- For subscriptions: record plan names, monthly price, what the allowance is (requests / tokens / points / usage-value), the reset window (5h rolling, daily, weekly, monthly), what happens on exhaustion (blocked vs. metered overage vs. falls to pay-as-you-go), whether subscription keys differ from standard API keys, and ANY restriction on clients or scenarios (e.g. only approved coding tools, no background automation, no API resale, personal use only).
- Note privacy/deployment: data retention, training on prompts, regions, zero-data-retention options, where weights run.
- Note uncertain or conflicting statements explicitly in "notes".

Output: your FINAL message must be ONLY a JSON object (no markdown fences) of the form
{"batch": "<batch id>", "records": [ ... ], "open_questions": ["..."]}

Each record (one per service) must have exactly these keys:
{
 "id": "kebab-case service id",
 "name": "...",
 "category": "subscription_allowance | hosted_api | custom_hosting | gateway",
 "homepage": "url",
 "openai_compatible": true|false|null,
 "api": {"base_url": "exact documented base url", "includes_v1": true|false|null, "chat_path": "path appended to base_url for chat completions, e.g. /chat/completions", "models_path": "e.g. /models or null", "models_list_requires_auth": true|false|null, "auth_header": "e.g. Authorization: Bearer", "other_protocols": ["anthropic-messages at <url>", ...]},
 "subscription_api": {"base_url": "...", "notes": "..."} or null,
 "access": {"signup_required": true, "key_type": "...", "subscription_key_differs_from_api_key": true|false|null, "kyc_or_waitlist": "..." },
 "billing": {"model": "allowance | metered | allowance_plus_metered | credits | free_tier | per_gpu_hour | per_second", "plans": [{"name": "...", "usd_per_month": number|null, "allowance": "...", "reset_window": "5h_rolling|daily|weekly|monthly|none|...", "on_exhaustion": "blocked|metered_overage|payg|unknown"}], "metered_overage": "none|opt_in|automatic|unknown", "auto_recharge": "off_by_default|on_by_default|n/a|unknown", "free_tier": "..."},
 "quotas": {"rate_limits": "...", "concurrency": "...", "context_caps": "..."},
 "restrictions": {"allowed_clients": ["..."] or null, "disallowed_uses": ["..."], "automation_allowed": true|false|null, "notes": "..."},
 "privacy": {"training_on_prompts": "...", "retention": "...", "zdr_available": true|false|null, "regions": "..."},
 "deployment": "subscription|api|serverless|gpu_pod|local",
 "modalities": ["text","code","vision","image","audio","embedding","rerank","tts","asr","video"],
 "notable_models": [{"id": "exact model id string used by the API", "family": "...", "open_weights": true|false|null, "license": "...", "refusal_profile": "standard|low|abliterated|unknown", "context_window": int|null, "notes": "..."}],
 "verified_findings": [{"claim": "...", "status": "confirmed|contradicted|unverified", "evidence": "short quote or paraphrase", "source": "url"}],
 "unknown": ["field names you could not verify"],
 "sources": [{"url": "...", "title": "...", "accessed": "2026-10-12", "official": true|false}],
 "notes": "..."
}

Batch id: E

Research these custom-model / multimedia hosting services: RunPod (pods + serverless + public endpoints), Vast.ai, Modal, Replicate, fal (fal.ai).
For each: what it hosts (arbitrary containers, GPU pods, serverless functions, prebuilt model endpoints), billing granularity, free credits, whether auto-recharge exists and its default, API base URLs (RunPod REST/GraphQL API, RunPod serverless OpenAI-compatible URL form https://api.runpod.ai/v2/ENDPOINT_ID/openai/v1, Vast.ai API, Modal web endpoints, Replicate https://api.replicate.com/v1 and any OpenAI-compatible support, fal queue API https://queue.fal.run/...), whether an OpenAI-compatible chat endpoint exists, and notable image (FLUX variants, Qwen-Image, etc.), video, ASR (Whisper large-v3/turbo, Parakeet), TTS (Kokoro, Chatterbox, etc.), embedding and reranking models available. Use category custom_hosting; deployment gpu_pod or serverless.
