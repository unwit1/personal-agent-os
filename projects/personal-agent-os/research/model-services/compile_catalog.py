"""Compile catalog.json from raw/batch-*.json and VERIFICATION.md (stdlib only).

    python projects/personal-agent-os/research/model-services/compile_catalog.py

The compiler also regenerates README.md's counts, gaps and service table.
The raw batches are untrusted research DATA; they are parsed as JSON and never
executed. Mechanical fields are mapped as-is. The judgement calls the raw
schema cannot express (endpoint ids and path styles, per-plan billing blocks,
integration status, privacy enums, operator spot checks from VERIFICATION.md)
live in SERVICES below, one entry per service, so a re-run is deterministic and
every decision is reviewable next to its reason.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "catalog.json"
README = HERE / "README.md"
REVIEWED_AT = "2026-10-12"
INTERVAL = 60
SERVICE_BATCHES = "ABCDE"
SERVICE_MODALITIES = ("text", "code", "vision", "image", "audio", "multimodal", "embedding", "rerank", "tts", "asr", "video")
NULL_MEANS_NONE = {"base_model", "refusal_evidence", "abliteration_method", "vs_base", "hf_repo", "notes", "catalog_model"}

# Names used in batch F/G served_by -> catalog service id.
SERVICE_NAMES = {
    "OpenRouter": "openrouter", "NanoGPT": "nanogpt", "HF Inference Providers": "hugging-face-inference-providers",
    "Novita": "novita-ai", "DeepInfra": "deepinfra", "Featherless": "featherless", "Chutes": "chutes", "Venice": "venice",
    "Synthetic": "synthetic", "Cerebras": "cerebras-inference", "Groq": "groq", "Alibaba": "alibaba-cloud-model-studio",
    "Z.ai": "z-ai-glm-coding-plan", "Together": "together-ai", "Fireworks": "fireworks-ai", "MiniMax": "minimax-m-plan",
    "Kimi": "kimi-code", "NVIDIA": "nvidia-nim-api", "Poe": "poe-api", "Mistral": "mistral-la-plateforme",
    "Nebius": "nebius-token-factory",
}

# Crosswalks whose native spelling differs from the HF router ID. These IDs
# must also be present in the staged service's notable_models; no IDs are
# synthesized from an HF repository name.
NATIVE_MODEL_IDS = {
    ("fireworks-ai", "glm-5.3"): "accounts/fireworks/models/glm-5p3",
    ("fireworks-ai", "minimax-m3"): "accounts/fireworks/models/minimax-m3",
    ("fireworks-ai", "kimi-k3"): "accounts/fireworks/models/kimi-k3",
    ("fireworks-ai", "qwen3-embedding-8b"): "accounts/fireworks/models/qwen3-embedding-8b",
    ("fireworks-ai", "qwen3-reranker-8b"): "accounts/fireworks/models/qwen3-reranker-8b",
    ("novita-ai", "minimax-m3"): "minimax/minimax-m3",
}


def ep(eid, protocol, base_url, path_style="root", models_path=None, auth=None, notes=""):
    return {"id": eid, "protocol": protocol, "base_url": base_url, "path_style": path_style, "models_path": models_path,
            "models_list_requires_auth": auth, "notes": notes}


def bill(mode, unit=None, amount=None, reset=None, overage="unknown", triggers=()):
    allowance = None if unit is None else {"unit": unit, "amount": amount, "reset_window": reset}
    return {"mode": mode, "allowance": allowance, "overage": overage, "metered_triggers": list(triggers)}


def plan(pid, endpoint, billing, *, automation="service", clients=None, notes="", name=None):
    """``automation='service'`` inherits the record's restrictions.automation_allowed;
    ``name`` is only needed for plans the raw batch does not list by name."""
    return {"id": pid, "endpoint": endpoint, "billing": billing, "automation_allowed": automation,
            "allowed_clients": clients, "notes": notes, "name": name}


def finding(claim, status, evidence, source):
    return {"claim": claim, "status": status, "evidence": evidence, "source": source}


V = "VERIFICATION.md #{}: "
PROVIDER_SELECTION = "Never add provider-selection or routing parameters to requests."

# Per-service decisions. ``plans`` maps the raw plan name to its catalog plan;
# raw plans absent from the map are custom-contract tiers whose billing mode
# the sources do not state, so they are listed in notes/unknown, not modelled.
SERVICES = {
    "synthetic": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Subscription packs allow any agent framework; OpenAI endpoint works with `services add`.",
        endpoints=[
            ep("default", "openai_chat", "https://api.synthetic.new/openai/v1", models_path="/models", auth=False,
               notes="Primary documented base. Getting Started also uses https://api.synthetic.new/v1."),
            ep("anthropic", "anthropic_messages", "https://api.synthetic.new/anthropic",
               notes="Anthropic SDK base derived from the documented messages URL https://api.synthetic.new/anthropic/v1/messages."),
        ],
        plans={"Subscription Packs": plan("subscription-pack", "default", bill("allowance", "requests", 500, "5h_rolling", "blocked"),
                                          notes="Also $24 of API usage credits per week per pack (weekly incremental regeneration); one concurrent request per model. Listed clients are examples, not an exclusive list.")},
        weights_note="First-party hosting is stated, but documented embeddings route through Fireworks.",
    ),
    "nanogpt": dict(
        status="preset_ready", training="unknown", weights="third_party",
        integration="Use the `subscription` endpoint and plan. " + PROVIDER_SELECTION + " Explicit provider selection is always billed pay-as-you-go.",
        endpoints=[
            ep("default", "openai_chat", "https://api.nano-gpt.com/api/v1", models_path="/models", auth=False,
               notes="Recommended by API Hosts; the website API page still documents https://nano-gpt.com/api/v1. Pay-as-you-go unless the key policy limits it."),
            ep("subscription", "openai_chat", "https://nano-gpt.com/api/subscription/v1", models_path="/models",
               notes="Subscription-only base (VERIFICATION.md #1); GET /models filters to subscription-included text models. Same API key as default. "
                     "Do not send explicit provider selection or X-Billing-Mode: paygo; both bill pay-as-you-go."),
            ep("anthropic", "anthropic_messages", "https://api.nano-gpt.com/api",
               notes="Anthropic SDK base (messages at /api/v1/messages). Subscription coverage through this base is not documented."),
        ],
        plans={"PRO": plan("pro", "subscription",
                           bill("allowance", "tokens", 60000000, "weekly", "blocked",
                                ["explicit provider selection (always pay-as-you-go)", "X-Billing-Mode: paygo header",
                                 "'Use balance after limits' with an API-key policy that permits balance spending"]),
                           notes="Also 100 included images per day. Subscription use is personal and non-commercial. Subscription keys keep returning 429 at exhaustion unless balance spending is enabled.")},
        verification=[(1, "NanoGPT has a subscription-only endpoint; explicit provider selection causes metered billing", "confirmed"),
                      (7, "NanoGPT API paths use /api/v1 and /api/subscription/v1", "confirmed")],
    ),
    "arli-ai": dict(
        status="preset_ready", training="unknown", weights="vendor",
        integration="Flat-rate plans allow coding agents and OpenAI-compatible frontends; one concurrent request on most tiers.",
        endpoints=[ep("default", "openai_chat", "https://api.arliai.com/v1", models_path="/models/textgen-models", auth=True,
                      notes="Text-generation model list at /v1/models/textgen-models. Image generation uses the SDNext-compatible https://api.arliai.com/sdapi/v1/txt2img.")],
        plans={
            "Free": plan("free", "default", bill("free", "requests", 5, "unknown"), notes="Five test requests per model every two days; delayed responses."),
            "Starter": plan("starter", "default", bill("allowance", "requests", None, "none"), notes="Unlimited requests and tokens; models up to 31B; 16384-token context."),
            "Core": plan("core", "default", bill("allowance", "requests", None, "none"), notes="Unlimited requests and tokens; models up to 355B; 32768-token context."),
            "Plus": plan("plus", "default", bill("allowance", "requests", None, "none"), notes="Unlimited requests and tokens; models up to 355B; 131072-token context."),
            "Pro": plan("pro", "default", bill("allowance", "requests", None, "none"), notes="Unlimited requests and tokens; two concurrent requests; 262144-token context."),
            "Max": plan("max", "default", bill("allowance", "requests", None, "none"), notes="Unlimited requests and tokens; six concurrent requests; 524288-token context."),
        },
        weights_note="Weights run on Arli's own on-premises servers; many fine-tunes are served as extracted LoRAs.",
    ),
    "venice": dict(
        status="preset_restricted", training="unknown", weights="unknown",
        integration="Terms conflict on third-party automation (section 12(d)); `services add` needs --ack-terms.",
        endpoints=[ep("default", "openai_chat", "https://api.venice.ai/api/v1", models_path="/models", auth=False)],
        plans={
            "Free": plan("free", "default", bill("free"), notes="10 web text prompts/day and 15 web image prompts/day; the API allowance is unverified, not a daily prompt quota."),
            "Pro": plan("pro", "default", bill("allowance", "usd_value", 1, "monthly", "metered", ["spendable USD or DIEM balance is consumed after bundled credits"]),
                        notes="100 monthly credits (100 credits = $1) shared across premium features and API. HTTP 402 when all balances are insufficient."),
            "Pro Plus": plan("pro-plus", "default", bill("allowance", "usd_value", 75, "monthly", "metered", ["spendable USD or DIEM balance is consumed after bundled credits"]),
                             notes="7500 monthly credits; two-month credit banking."),
            "Max": plan("max", "default", bill("allowance", "usd_value", 225, "monthly", "metered", ["spendable USD or DIEM balance is consumed after bundled credits"]),
                        notes="22500 monthly credits; three-month credit banking."),
        },
        weights_note="Private models run without retention; Anonymous models expose prompt content to the upstream provider.",
        extra_findings=[finding("Venice Free includes an API allowance", "unverified",
                                "Batch A's 10 daily text prompts and 15 daily image prompts are web allowances only. API access is advertised, but its allowance is not verified; billing.allowance stays null.",
                                "https://venice.ai/pricing")],
    ),
    "chutes": dict(
        status="preset_restricted", training="no", weights="unknown",
        integration="Subscriptions allow manual and low-volume API use only; production or highly automated work must use PAYG. `services add` needs --ack-terms.",
        endpoints=[ep("default", "openai_chat", "https://llm.chutes.ai/v1", models_path="/models", auth=False)],
        plans={
            "Plus": plan("plus", "default", bill("allowance", "requests", None, "daily", "metered", ["usage beyond the bundled daily quota is billed PAYG (6% discount)"]),
                         notes="Bundled daily request quota (count not published). A 5x-fee monthly usage-value cap is in the February announcement only (VERIFICATION.md #4)."),
            "Pro": plan("pro", "default", bill("allowance", "requests", None, "daily", "metered", ["usage beyond the bundled daily quota is billed PAYG (10% discount)"]),
                        notes="Larger bundled daily request quota (count not published). Same usage-value cap caveat as Plus."),
        },
        verification=[(4, "Chutes subscription overage beyond the bundled daily quota is metered PAYG, not blocked", "confirmed")],
        extra_findings=[finding(
            "Chutes usage-value caps (5x plan price per month, 4-hour rolling window) are documented only by secondary sources",
            "contradicted",
            "VERIFICATION.md #4 found the dollar caps only on a secondary blog, not on https://chutes.ai/pricing; batch A cites the official February announcement "
            "for a 5x monthly cap. The cap amount is not modelled (allowance.amount null).",
            "https://chutes.ai/news/community-announcement-february")],
    ),
    "poe-api": dict(
        status="preset_ready", training="unknown", weights="third_party",
        integration="API calls spend subscription compute points; exhaustion returns HTTP 402 unless add-on points exist.",
        endpoints=[
            ep("default", "openai_chat", "https://api.poe.com/v1", models_path="/models", auth=False,
               notes="500 rpm; response_format json_schema unsupported; n must be 1 (VERIFICATION.md #2). Batch A reports a public /models; the page checked in VERIFICATION.md #2 does not document it."),
            ep("anthropic", "anthropic_messages", "https://api.poe.com", notes="Anthropic SDK base; only official Anthropic bots are supported."),
        ],
        plans={
            "10 thousand points/day": plan("points-10k-daily", "default", bill("allowance", "points", 10000, "daily", "blocked", ["purchased add-on points are spent when subscription points run out"])),
            "660 thousand points/month": plan("points-660k-monthly", "default", bill("allowance", "points", 660000, "monthly", "blocked", ["purchased add-on points are spent when subscription points run out"])),
            "1.65 million points/month": plan("points-1650k-monthly", "default", bill("allowance", "points", 1650000, "monthly", "blocked", ["purchased add-on points are spent when subscription points run out"])),
            "3.3 million points/month": plan("points-3300k-monthly", "default", bill("allowance", "points", 3300000, "monthly", "blocked", ["purchased add-on points are spent when subscription points run out"])),
            "8.25 million points/month": plan("points-8250k-monthly", "default", bill("allowance", "points", 8250000, "monthly", "blocked", ["purchased add-on points are spent when subscription points run out"])),
        },
        verification=[(2, "Poe API can use subscription points; exhaustion is blocked (HTTP 402) unless add-on points exist", "confirmed"),
                      (7, "Poe's OpenAI-compatible base is https://api.poe.com/v1", "confirmed")],
        extra_findings=[finding("Poe documents a models-list endpoint", "unverified",
                                "Batch A says /models is public; VERIFICATION.md #2 found no models-list endpoint on the OpenAI-compatible API page.",
                                "https://creator.poe.com/docs/external-applications/openai-compatible-api")],
    ),
    "featherless": dict(
        status="preset_ready", training="unknown", weights="vendor",
        integration="Use the Developer plan; the Chat plan forbids coding agents, API traffic and background automation.",
        endpoints=[ep("default", "openai_chat", "https://api.featherless.ai/v1", models_path="/models", auth=False)],
        plans={
            "Chat": plan("chat", "default", bill("allowance", "requests", None, "none"), automation=False,
                         clients=["SillyTavern", "RisuAI", "Wyvern", "other OpenAI-compatible frontends for human-driven interaction"],
                         notes="$25/mo: unlimited tokens and requests for interactive, human-driven use only. Coding agents: No. Production API: No. Background automation: No."),
            "Developer": plan("developer", "default", bill("credits", "usd_value", 50, "monthly", "blocked"), automation=True,
                              notes="$50/mo prepaid credits billed per token; calls stop at zero balance until credits are added; unused credits roll over."),
        },
        verification=[(3, "Featherless Chat plan excludes coding agents and background automation; Developer is metered", "confirmed")],
    ),
    "minimax-m-plan": dict(
        status="preset_restricted", training="unknown", weights="vendor",
        integration="Needs the M Plan Subscription Key (sk-cp-), not a pay-as-you-go key. Positioned for individual interactive use; `services add` needs --ack-terms. A Claude Code bridge is also available.",
        endpoints=[
            ep("default", "openai_chat", "https://api.minimax.io/v1", models_path="/models", auth=True,
               notes="Same base for pay-as-you-go and M Plan; billing follows the key type. Store the Subscription Key here."),
            ep("anthropic", "anthropic_messages", "https://api.minimax.io/anthropic",
               notes="Claude Code setup: ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic with ANTHROPIC_AUTH_TOKEN=<subscription key> (VERIFICATION.md #5)."),
        ],
        plans={
            "Go": plan("go", "default", bill("allowance", "unknown", None, "5h_rolling", "metered", ["eligible purchased credits are consumed automatically after the plan allowance"]),
                       notes="5-hour and 7-day windows start on first use and reset independently; absolute quantity not published."),
            "Explore": plan("explore", "default", bill("allowance", "unknown", None, "5h_rolling", "metered", ["eligible purchased credits are consumed automatically after the plan allowance"]),
                            notes="3x Go usage."),
            "Build": plan("build", "default", bill("allowance", "unknown", None, "5h_rolling", "metered", ["eligible purchased credits are consumed automatically after the plan allowance"]),
                          notes="7.5x Go usage."),
        },
        verification=[(5, "MiniMax subscription keys differ from standard API keys", "confirmed"),
                      (7, "MiniMax's Anthropic base is https://api.minimax.io/anthropic", "confirmed")],
    ),
    "kimi-code": dict(
        status="catalog_only", training="yes", weights="vendor",
        integration="Kimi Code is personal interactive use only and forbids non-interactive automation, so no automated preset or bridge is offered.",
        endpoints=[
            ep("default", "openai_chat", "https://api.kimi.ai/coding/v1", notes="Overseas coding base. Pay-as-you-go Moonshot platform is https://api.moonshot.ai/v1 (different key)."),
            ep("anthropic", "anthropic_messages", "https://api.kimi.ai/coding", notes="Overseas Anthropic base, documented as https://api.kimi.ai/coding/."),
            ep("cn", "openai_chat", "https://api.kimi.com/coding/v1", notes="China coding base."),
            ep("cn-anthropic", "anthropic_messages", "https://api.kimi.com/coding", notes="China Anthropic base; documented full endpoint https://api.kimi.com/coding/v1/messages."),
        ],
        plans={name: plan(name.lower(), "default", bill("allowance", "unknown", None, "5h_rolling", "blocked", ["Extra Usage (optional)"]), automation=False,
                          notes="Shared monthly membership credit pool metered by usage; absolute quantity not verified. Exhausted quota blocks until reset unless Extra Usage is enabled.")
               for name in ("Plus", "Pro", "Max", "Ultra")},
    ),
    "z-ai-glm-coding-plan": dict(
        status="bridge_claude_code", training="unknown", weights="vendor",
        integration="Coding Plan benefits apply only in the listed tools, which include Claude Code; use `services bridge` (--ack-terms: automation terms are unclear, VERIFICATION.md #6).",
        endpoints=[
            ep("default", "openai_chat", "https://api.z.ai/api/paas/v4", notes="General pay-as-you-go API, documented as https://api.z.ai/api/paas/v4/ (trailing slash stripped). No plan in the batch bills through it."),
            ep("coding", "openai_chat", "https://api.z.ai/api/coding/paas/v4", notes="Dedicated Coding Plan base for OpenAI Chat Completions."),
            ep("anthropic", "anthropic_messages", "https://api.z.ai/api/anthropic", notes="Coding Plan Anthropic base for Claude Code."),
        ],
        plans={
            "Lite": plan("lite", "coding", bill("allowance", "points", 2000, "5h_rolling", "blocked"), automation=None,
                         notes="2,000 credits per 5h and 10,000 per week (credits from input, cached-input, output tokens and MCP calls). Off-peak usage billed at 50%."),
            "Pro": plan("pro", "coding", bill("allowance", "points", 12000, "5h_rolling", "blocked"), automation=None, notes="12,000 credits per 5h and 60,000 per week."),
            "Max": plan("max", "coding", bill("allowance", "points", 28000, "5h_rolling", "blocked"), automation=None, notes="28,000 credits per 5h and 140,000 per week."),
        },
        plan_clients="raw",
        verification=[(6, "The Z.ai GLM Coding Plan restricts supported clients; credits per 5h/week; overview states no rule for use outside listed tools", "confirmed")],
        extra_findings=[finding("Z.ai Coding Plan permits automated use (batch B: automation_allowed true)", "unverified",
                                "VERIFICATION.md #6: the overview states no rule for use outside the listed tools, so automation_allowed is null and a bridge needs --ack-terms.",
                                "https://docs.z.ai/devpack/overview")],
    ),
    "alibaba-cloud-model-studio": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="The pay-as-you-go Model Studio API allows application integration. The Coding Plan (sk-sp- key, coding endpoints) forbids automated scripts and backends, so it has no preset.",
        endpoints=[
            ep("default", "openai_chat", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", auth=True,
               notes="Singapore pay-as-you-go base. Native authenticated model list is GET https://dashscope-intl.aliyuncs.com/api/v1/models (different root). Keys are region-specific."),
            ep("anthropic", "anthropic_messages", "https://dashscope-intl.aliyuncs.com/apps/anthropic", notes="Pay-as-you-go Anthropic base (Singapore)."),
            ep("coding", "openai_chat", "https://coding-intl.dashscope.aliyuncs.com/v1", notes="Coding Plan base; sk-sp- key; model enumeration via API is explicitly unsupported."),
            ep("coding-anthropic", "anthropic_messages", "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic", notes="Coding Plan Anthropic base."),
        ],
        plans={"Coding Plan Pro": plan("coding-plan-pro", "coding", bill("allowance", "requests", 6000, "5h_rolling", "blocked"), automation=False, clients="raw",
                                       notes="Up to 6,000 requests per 5h, 45,000 per week and 90,000 per month, all applied simultaneously. Interactive use only; limited daily subscription slots.")},
        extra_plans=[plan("payg", "default", name="Model Studio pay-as-you-go API", billing=
                          bill("metered", "tokens", 1000000, "none", "metered", ["after the free quota, unless Free Quota Only is enabled (disabled by default)"]),
                          automation=True,
                          notes="Pay-as-you-go Model Studio API, from batch B's free_tier and restriction notes (the batch lists no named plan for it). "
                                "Eligible Singapore models get 1,000,000 free tokens per model for 90 days.")],
    ),
    "together-ai": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Prepaid serverless API; requests need a positive balance.",
        endpoints=[ep("default", "openai_chat", "https://api.together.ai/v1", models_path="/models", auth=True)],
        plans={"Serverless": plan("serverless", "default", bill("credits", overage="blocked"), notes="Prepaid credit; minimum first purchase $15, then $5.")},
        weights_note="Passthrough models send content to upstream providers.",
    ),
    "fireworks-ai": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Prepaid serverless API. Fire Pass (closed to new subscriptions) is limited to personal, non-production agentic coding in named clients.",
        endpoints=[
            ep("default", "openai_chat", "https://api.fireworks.ai/inference/v1", auth=True, notes="No inference-base GET /models was verified; use the management API."),
            ep("anthropic", "anthropic_messages", "https://api.fireworks.ai/inference",
               notes="Anthropic SDK base derived from the documented messages URL https://api.fireworks.ai/inference/v1/messages."),
            ep("us", "openai_chat", "https://us.api.fireworks.ai/inference/v1", auth=True, notes="US-only serverless with specified US router ids."),
            ep("fire-pass", "openai_chat", "https://api.fireworks.ai/inference/v1", auth=True, notes="Same base, Fire Pass fpk_ key and enabled router ids only."),
        ],
        plans={
            "Serverless": plan("serverless", "default", bill("credits", overage="blocked"), notes="Prepaid credits consumed by token usage."),
            "Fire Pass": plan("fire-pass", "fire-pass", bill("allowance", "unknown", None, "unknown"), automation=None,
                              clients=["Claude Code", "OpenCode", "Pi", "Cursor IDE", "VS Code Chat", "GitHub Copilot app/CLI", "DeepSeek Harness"],
                              notes="Covered requests to enabled open-weight routers; allowance, reset and exhaustion unknown. No production workloads, no key sharing."),
        },
    ),
    "groq": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Free and postpaid Developer tiers on the same OpenAI-compatible base.",
        endpoints=[ep("default", "openai_chat", "https://api.groq.com/openai/v1", models_path="/models", auth=True)],
        plans={
            "Free": plan("free", "default", bill("free", "requests", None, "daily", "blocked"), notes="Model-specific per-minute and daily request, token and audio limits."),
            "Developer": plan("developer", "default", bill("metered", overage="metered"), notes="Postpaid; charged at month end or at progressive usage thresholds."),
        },
    ),
    "cerebras-inference": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Prepaid PayGo credits; Developer tier is not intended for production.",
        endpoints=[ep("default", "openai_chat", "https://api.cerebras.ai/v1", models_path="/models", auth=True)],
        plans={
            "Free Trial": plan("free-trial", "default", bill("credits", "usd_value", 5, "none", "blocked"),
                               notes="One-time $5 credit after adding a payment method; expires after 30 days; no automatic paid enrolment."),
            "Developer": plan("developer", "default", bill("credits", overage="metered", triggers=["brief negative balances from usage spikes are charged at period end"]),
                              notes="Prepaid credits; zero balance normally blocks requests; purchased credits expire after one year."),
        },
    ),
    "deepinfra": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Metered API; the self-serve prepaid/postpaid default and zero-balance behaviour are unknown.",
        endpoints=[
            ep("default", "openai_chat", "https://api.deepinfra.com/v1/openai", notes="Chat URL is base + /chat/completions. No documented REST model-list URL."),
            ep("anthropic", "anthropic_messages", "https://api.deepinfra.com/anthropic",
               notes="Anthropic SDK base derived from the documented messages URL https://api.deepinfra.com/anthropic/v1/messages."),
        ],
        plans={},
        extra_plans=[plan("payg", "default", bill("metered"), automation=True, name="Pay-as-you-go API",
                          notes="Batch C lists no named plan; billing.model is metered and metered_overage unknown.")],
    ),
    "novita-ai": dict(
        status="preset_ready", training="no", weights="vendor",
        integration="Use the Model API plan. Coding Plan use outside supported tools (CI, scripts) is described as prohibited, so the coding plans have no preset.",
        endpoints=[
            ep("default", "openai_chat", "https://api.novita.ai/openai", path_style="append_v1", models_path="/models", auth=True,
               notes="Documented SDK base; REST chat URL is https://api.novita.ai/openai/v1/chat/completions and models GET /openai/v1/models."),
            ep("anthropic", "anthropic_messages", "https://api.novita.ai/anthropic", notes="Anthropic-compatible SDK base."),
        ],
        plans={
            "Model API": plan("model-api", "default", bill("credits", overage="blocked"), notes="Prepaid credit; manual top-up above $10."),
            "Coding Plan Lite": plan("coding-plan-lite", "default", bill("allowance", "tokens", 50000000, "monthly", "metered", ["Coding Plan quota is used first, then the API balance"]),
                                     automation=False, notes="Base-rate-equivalent tokens (model weights apply). No separate subscription endpoint verified; supported-tool list not verified."),
            "Coding Plan Pro": plan("coding-plan-pro", "default", bill("allowance", "tokens", 150000000, "monthly", "metered", ["Coding Plan quota is used first, then the API balance"]),
                                    automation=False, notes="Base-rate-equivalent tokens."),
            "Coding Plan Max": plan("coding-plan-max", "default", bill("allowance", "tokens", 750000000, "monthly", "metered", ["Coding Plan quota is used first, then the API balance"]),
                                    automation=False, notes="Base-rate-equivalent tokens."),
        },
        extra_findings=[finding("Novita Coding Plan forbids use from CI or scripts outside supported tools", "unverified",
                                "An official October 12 comparison article says so; the exact contractual scope is not confirmed. Coding plans are recorded with automation_allowed false.",
                                "https://blogs.novita.ai/ai-coding-plans/")],
    ),
    "nebius-token-factory": dict(
        status="preset_ready", training="unknown", weights="vendor",
        integration="Usage-priced inference; a bank card is mandatory and auto-recharge is on by default.",
        endpoints=[ep("default", "openai_chat", "https://api.tokenfactory.nebius.com/v1", models_path="/models", auth=True,
                      notes="Documented as https://api.tokenfactory.nebius.com/v1/ (trailing slash stripped)."),],
        plans={"Starter Plan": plan("starter", "default", bill("metered", overage="metered", triggers=["auto-recharge is on by default"]),
                                    notes="New signups get $1 trial credit for 30 days.")},
    ),
    "nvidia-nim-api": dict(
        status="preset_ready", training="yes", weights="vendor",
        integration="Hosted API trial credits, subject to trial-purpose terms; the trial terms permit using content to improve NVIDIA models.",
        endpoints=[ep("default", "openai_chat", "https://integrate.api.nvidia.com/v1", models_path="/models")],
        plans={"API Catalog trial": plan("trial", "default", bill("credits", overage="blocked"), notes="Current universal credit grant not verified.")},
    ),
    "mistral-la-plateforme": dict(
        status="preset_ready", training="opt_out", weights="vendor",
        integration="Plans apply across Studio, API and Vibe; included usage first, optional prepaid PAYG extends it.",
        endpoints=[ep("default", "openai_chat", "https://api.mistral.ai/v1", models_path="/models", auth=True,
                      notes="Global endpoint. Regional api.eu.mistral.ai and api.us.mistral.ai hosts exist; their full base paths were not recorded.")],
        plans={name: plan(pid, "default", bill("allowance", "unknown", None, "monthly", "unknown", ["optional prepaid pay-as-you-go (opt-in)"]), notes=note)
               for name, pid, note in (("Free mode", "free", "Limited access to Studio and Vibe; API allowance not verified."),
                                       ("Pro", "pro", "Price and allowance not reliably extracted."),
                                       ("Education", "education", "$14.99 shown alongside Education eligibility."),
                                       ("Team", "team", "Per user per month, excluding taxes."),
                                       ("Enterprise", "enterprise", "Custom."))},
    ),
    "deepseek-api": dict(
        status="preset_ready", training="unknown", weights="vendor",
        integration="Prepaid token-priced API; downstream application integration is permitted.",
        endpoints=[
            ep("default", "openai_chat", "https://api.deepseek.com", models_path="/models", auth=True,
               notes="Chat URL is https://api.deepseek.com/chat/completions. https://api.deepseek.com/v1 is a documented alternative."),
            ep("anthropic", "anthropic_messages", "https://api.deepseek.com/anthropic", notes="Anthropic-compatible base."),
        ],
        plans={"Prepaid API usage": plan("prepaid", "default", bill("credits", overage="blocked"), notes="Granted balance is used before topped-up balance.")},
    ),
    "openrouter": dict(
        status="preset_ready", training="unknown", weights="third_party",
        integration="Gateway with prepaid credits. " + PROVIDER_SELECTION + " Defaults include allow_fallbacks=true and data_collection=allow.",
        endpoints=[ep("default", "openai_chat", "https://openrouter.ai/api/v1", models_path="/models",
                      notes="Business/Enterprise regional routing uses eu.openrouter.ai and us.openrouter.ai.")],
        plans={
            "Free": plan("free", "default", bill("free", "requests", 50, "daily", "blocked"), notes=":free models only; 1,000/day after a one-time $10 purchase; paid fallbacks can incur charges."),
            "Standard Pay-as-you-go": plan("payg", "default", bill("credits", overage="blocked"), notes="Prepaid USD credits; 5.5% platform fee on purchases."),
            "Business Pay-as-you-go": plan("business-payg", "default", bill("metered"), notes="Usage-priced; 8% platform fee."),
        },
    ),
    "hugging-face-inference-providers": dict(
        status="preset_ready", training="unknown", weights="third_party",
        integration="Chat-only OpenAI-compatible router. " + PROVIDER_SELECTION + " (no :cheapest/:preferred/:provider suffixes); custom provider keys bypass included credits.",
        endpoints=[ep("default", "openai_chat", "https://router.huggingface.co/v1", models_path="/models")],
        plans={
            "Free account": plan("free", "default", bill("free", overage="blocked"), notes="No included monthly credits on the current pricing page."),
            "PRO": plan("pro", "default", bill("allowance", "usd_value", 2, "monthly", "metered", ["purchased credits after the included credits"]),
                        notes="$2/month compute credits shared with other eligible Hugging Face compute."),
            "Team": plan("team", "default", bill("allowance", "usd_value", 2, "monthly", "metered", ["purchased credits after the included credits"]), notes="$2/month per seat, pooled."),
            "Enterprise": plan("enterprise", "default", bill("allowance", "usd_value", 2, "monthly", "metered", ["purchased credits after the included credits"]), notes="$2/month per seat, pooled."),
        },
    ),
    "runpod": dict(
        status="deferred", training="unknown", weights="unknown",
        integration="Needs a deployed serverless endpoint (custom container) and paid provisioning. The OpenAI-compatible base is the template https://api.runpod.ai/v2/ENDPOINT_ID/openai/v1, so it is not an endpoint here.",
        endpoints=[ep("default", "vendor", "https://rest.runpod.io/v1", notes="REST management API (OpenAPI at /v1/openapi.json). The GraphQL API passes the key in the query string; avoid it.")],
        plans={"Pay-as-you-go prepaid credits": plan("prepaid", None, bill("credits"), notes="Pods and Serverless billed per second; public endpoints per output unit.")},
    ),
    "vast-ai": dict(
        status="deferred", training="unknown", weights="self",
        integration="GPU marketplace; needs paid provisioning and a container. Serverless uses a /route/ handshake, not the OpenAI path form.",
        endpoints=[ep("default", "vendor", "https://console.vast.ai/api/v0", notes="Management API.")],
        plans={
            "Prepaid credit; On-Demand": plan("on-demand", None, bill("credits", overage="blocked"), notes="Market prices; billed per second; bandwidth per TB."),
            "Interruptible": plan("interruptible", None, bill("credits", overage="blocked"), notes="50%+ cheaper; instances can be preempted."),
        },
        weights_note="Hosts are third-party providers; trust varies by host.",
    ),
    "modal": dict(
        status="deferred", training="unknown", weights="self",
        integration="Hosts your own code; an OpenAI-compatible surface exists only if you deploy one (vLLM, SGLang). Endpoint URLs are per deployment: https://<workspace>--<app>-<function>.modal.run.",
        endpoints=[],
        plans={
            "Starter": plan("starter", None, bill("allowance", "usd_value", 30, "monthly", "metered", ["compute beyond the free credits"]), notes="$30/month free credits; 10 GPU concurrency."),
            "Team": plan("team", None, bill("allowance", "usd_value", 100, "monthly", "metered", ["compute beyond the free credits"]), notes="$100/month free credits; 50 GPU concurrency."),
        },
    ),
    "replicate": dict(
        status="catalog_only", training="unknown", weights="vendor",
        integration="Prediction API, not chat completions; no openai_chat preset.",
        endpoints=[ep("default", "vendor", "https://api.replicate.com/v1", models_path="/models", notes="POST /v1/predictions; GET /v1/models lists public models.")],
        plans={
            "Prepaid credit": plan("prepaid", "default", bill("credits", overage="blocked"), notes="Valid one year; non-refundable."),
            "Postpaid (billed in arrears)": plan("postpaid", "default", bill("metered"), notes="Previous month's usage charged at the start of each month."),
        },
    ),
    "fal": dict(
        status="catalog_only", training="unknown", weights="vendor",
        integration="Queue-based media model API (Authorization: Key), not chat completions; no openai_chat preset.",
        endpoints=[ep("default", "vendor", "https://queue.fal.run", notes="POST /{model_id}, then poll /requests/{request_id}/status.")],
        plans={
            "Prepaid credits (Model APIs per output unit; serverless GPUs per hour)": plan("prepaid", "default", bill("credits", overage="blocked"),
                                                                                          notes="Requests are rejected below the lock threshold until credits are added; credits expire after 365 days."),
            "Invoice billing (higher volume)": plan("invoice", "default", bill("metered"), notes="Not subject to automatic locking."),
        },
    ),
}

VERIFICATION_SOURCES = {
    1: ["https://docs.nano-gpt.com/api-reference/miscellaneous/provider-selection.md", "https://docs.nano-gpt.com/api-reference/endpoint/chat-completion.md",
        "https://docs.nano-gpt.com/api-reference/miscellaneous/billing-override.md"],
    2: ["https://creator.poe.com/docs/external-applications/openai-compatible-api"],
    3: ["https://featherless.ai/pricing"],
    4: ["https://chutes.ai/pricing"],
    5: ["https://platform.minimax.io/docs/coding-plan/intro", "https://platform.minimax.io/docs/m-plan/claude-code"],
    6: ["https://docs.z.ai/devpack/overview"],
    7: [],
}
SECONDARY_SOURCES = {4: ["https://blog.patshead.com/2026/03/squeezing-more-value-from-low-cost-coding-plans-models-and-context.html"]}
VERIFICATION_PRIMARY = {7: {"nanogpt": 1, "poe-api": 2, "minimax-m-plan": 5}}


def verification_rows() -> dict[int, dict[str, str]]:
    rows = {}
    for line in (HERE / "VERIFICATION.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            rows[int(cells[0])] = {"claim": cells[1], "result": cells[2].replace("*", ""), "evidence": cells[3]}
    return rows


def first_id(raw: str) -> str | None:
    candidate = raw.split(" (")[0].split(";")[0].strip()
    return None if not candidate or " " in candidate else candidate


def source_obj(item, official_hosts: set[str], publisher_orgs: set[str]) -> dict:
    if isinstance(item, dict):
        return item
    match = re.match(r"^(\S+)(?: \(accessed (\d{4}-\d{2}-\d{2})\))?", item)
    url, accessed = match.group(1), match.group(2) or REVIEWED_AT
    parts = urlsplit(url)
    org = parts.path.strip("/").split("/")[0].lower() if parts.hostname == "huggingface.co" else None
    official = (org in publisher_orgs) if org is not None else (parts.hostname or "") in official_hosts
    return {"url": url, "title": parts.hostname + parts.path, "accessed": accessed, "official": official}


def with_unknown(record: dict) -> dict:
    unknown = list(record.get("unknown", []))

    def visit(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                field = f"{path}.{key}" if path else key
                # These nulls express absence rather than missing research.
                meaningful = (key in NULL_MEANS_NONE or key == "allowed_clients"
                              or key == "secret_ref" and value.get("protocol") == "vendor"
                              or key == "endpoint" and "billing" in value
                              or key == "allowance" and value.get("mode") in ("metered", "credits", "free", "local", "per_gpu_time"))
                if child is None and not meaningful and field not in unknown:
                    unknown.append(field)
                elif child is not None and key not in ("unknown", "findings", "sources", "native_evidence"):
                    visit(child, field)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(record)
    record["unknown"] = unknown
    for number, served in enumerate(record.get("served_by") or []):
        for key in ("model_id", "endpoint", "pricing"):
            if key not in served or served[key] is not None:
                continue
            field = f"served_by[{number}].{key}"
            if field not in unknown:
                unknown.append(field)
            entry_unknown = served.setdefault("unknown", [])
            if key not in entry_unknown:
                entry_unknown.append(key)
            record.setdefault("findings", []).append(finding(
                f"{field} for {served['service']} is verified.",
                "unverified", served.get("notes") or f"No verified {key} was captured.",
                served.get("source") or record["sources"][0]["url"],
            ))
    return record


def service_record(raw: dict, spec: dict, rows: dict[int, dict[str, str]], model_index: dict) -> dict:
    sid = raw["id"]
    restrictions = raw.get("restrictions") or {}
    unknown = list(raw.get("unknown") or [])
    notes = [raw.get("notes") or ""]

    endpoints = []
    for item in spec["endpoints"]:
        item = dict(item)
        item["base_url"] = item["base_url"].rstrip("/")
        if item["protocol"] in ("openai_chat", "anthropic_messages"):
            item["secret_ref"] = f"secrets://{sid}/{item['id']}"
        else:
            item["secret_ref"] = None
        endpoints.append(item)

    plans, skipped = [], []
    for raw_plan in (raw.get("billing") or {}).get("plans") or []:
        decided = spec["plans"].get(raw_plan["name"])
        if decided is None:
            skipped.append(raw_plan["name"])
            continue
        plans.append(build_plan(decided, raw_plan, raw, spec))
    for decided in spec.get("extra_plans", []):
        plans.append(build_plan(decided, None, raw, spec))
    # Plans whose terms allow automation from any client come first, so
    # `services add <id>` without --plan picks a usable one (stable otherwise).
    plans.sort(key=lambda item: not (item["automation_allowed"] is True and item["allowed_clients"] is None))
    missing = set(spec["plans"]) - {p["name"] for p in (raw.get("billing") or {}).get("plans") or []}
    if missing:
        raise SystemExit(f"{sid}: plan names not in raw batch: {sorted(missing)}")
    if skipped:
        notes.append(f"Custom-contract plans not modelled (billing mode not stated): {', '.join(skipped)}.")
        unknown.extend(f"plans.{name}.billing" for name in skipped)

    findings = [dict(item) for item in raw.get("verified_findings") or []]
    sources = list(raw.get("sources") or [])
    for number, claim, status in spec.get("verification", []):
        row = rows[number]
        urls = VERIFICATION_SOURCES[number] or VERIFICATION_SOURCES[VERIFICATION_PRIMARY[number][sid]]
        findings.append(finding(claim, status, V.format(number) + f"{row['result']}. {row['evidence']}", urls[0]))
        for url in urls + SECONDARY_SOURCES.get(number, []):
            if url not in {item["url"] for item in sources}:
                sources.append({"url": url, "title": f"VERIFICATION.md #{number} spot check", "accessed": REVIEWED_AT,
                                "official": url not in SECONDARY_SOURCES.get(number, [])})
    findings.extend(spec.get("extra_findings", []))

    models, unlisted = [], []
    for item in raw.get("notable_models") or []:
        if not item.get("id"):
            unlisted.append(f"{item.get('family')}: {item.get('notes')}")
            continue
        models.append({
            "id": item["id"], "catalog_model": link_model(sid, item["id"], model_index), "family": item.get("family"),
            "open_weights": item.get("open_weights"), "license": item.get("license"),
            "refusal_profile": item.get("refusal_profile") or "unknown", "context_window": item.get("context_window"),
            "notes": item.get("notes"),
        })
    if unlisted:
        notes.append("Notable models without a verified API id: " + " | ".join(unlisted))

    modalities = map_nullable(raw.get("modalities"), lambda item: item if item in SERVICE_MODALITIES else None, drop_none=True)
    dropped = [item for item in raw.get("modalities") or [] if item not in SERVICE_MODALITIES]
    if dropped:
        notes.append(f"Raw modalities outside the schema enum: {', '.join(dropped)}.")

    privacy_raw = raw.get("privacy") or {}
    privacy = {
        "training_on_prompts": spec["training"], "retention": privacy_raw.get("retention"), "zdr": privacy_raw.get("zdr_available"),
        "weights_location": spec["weights"], "training_notes": privacy_raw.get("training_on_prompts"), "regions": privacy_raw.get("regions"),
    }
    if spec.get("weights_note"):
        privacy["weights_notes"] = spec["weights_note"]

    record = {
        "id": sid, "name": raw["name"], "category": raw["category"], "homepage": raw["homepage"], "reviewed_at": REVIEWED_AT,
        "integration_status": spec["status"], "integration_notes": spec["integration"], "deployment": raw["deployment"],
        "modalities": modalities, "openai_compatible": raw.get("openai_compatible"), "endpoints": endpoints, "plans": plans,
        "access": raw.get("access"), "privacy": privacy,
        "restrictions": {"disallowed_uses": restrictions.get("disallowed_uses"), "documented_clients": restrictions.get("allowed_clients"),
                         "automation_allowed": restrictions.get("automation_allowed"), "notes": restrictions.get("notes")},
        "quotas": raw.get("quotas"),
        "billing_notes": {key: value for key, value in (raw.get("billing") or {}).items() if key != "plans"},
        "models": models, "findings": findings, "unknown": unknown, "sources": sources,
        "notes": " ".join(item for item in notes if item) or None,
    }
    if record["openai_compatible"] is None:
        record["unknown"].append("openai_compatible")
    if record["access"] is None:
        record["unknown"].append("access")
    if sid == "venice":
        free_index = next(i for i, item in enumerate(plans) if item["id"] == "free")
        record["unknown"].append(f"plans[{free_index}].billing.allowance")
    if record["restrictions"]["disallowed_uses"] is None:
        findings.append(finding("restrictions.disallowed_uses is verified", "unverified",
                                "The raw batch did not verify disallowed uses; null does not mean no restrictions.",
                                sources[0]["url"]))
    return with_unknown(record)


def build_plan(decided: dict, raw_plan: dict | None, raw: dict, spec: dict) -> dict:
    automation = decided["automation_allowed"]
    if automation == "service":
        automation = (raw.get("restrictions") or {}).get("automation_allowed")
    clients = decided["allowed_clients"]
    if clients == "raw" or (clients is None and spec.get("plan_clients") == "raw"):
        raw_clients = (raw.get("restrictions") or {}).get("allowed_clients")
        clients = None if raw_clients is None else list(raw_clients)
    billing = dict(decided["billing"], plan=decided["id"])
    billing = {"mode": billing["mode"], "plan": billing["plan"], "allowance": billing["allowance"],
               "overage": billing["overage"], "metered_triggers": billing["metered_triggers"]}
    raw_notes = ""
    if raw_plan is not None:
        raw_notes = (f" Raw allowance: {raw_plan.get('allowance')}. Raw reset_window: {raw_plan.get('reset_window')}."
                     f" Raw on_exhaustion: {raw_plan.get('on_exhaustion')}.")
    return {
        "id": decided["id"], "name": raw_plan["name"] if raw_plan else decided["name"],
        "usd_per_month": raw_plan.get("usd_per_month") if raw_plan else None, "endpoint": decided["endpoint"], "billing": billing,
        "automation_allowed": automation, "allowed_clients": clients, "notes": (decided["notes"] + raw_notes).strip(),
    }


def link_model(sid: str, model_id: str, index: dict) -> str | None:
    key = model_id.lower().removeprefix("hf:")
    for candidate in (key, re.sub(r"-(tee|fp8)$", "", key)):
        if candidate in index["repos"]:
            return index["repos"][candidate]
        if (sid, candidate) in index["served"]:
            return index["served"][(sid, candidate)]
    return None


def served_entry(item: dict, record_id: str, native_models: dict) -> dict:
    name = item["service"]
    if name not in SERVICE_NAMES:
        raise SystemExit(f"served_by service {name!r} has no catalog id")
    entry = {"service": SERVICE_NAMES[name], "model_id": first_id(item.get("model_id") or "")}
    # An HF router ID is exact for HF itself, but is not evidence of the
    # backing provider's native ID. Reconcile it with staged service research.
    router_only = (urlsplit(item.get("source") or "").hostname == "router.huggingface.co"
                   or "via HF router" in (item.get("model_id") or ""))
    native = native_models.get(entry["service"], {})
    candidate = NATIVE_MODEL_IDS.get((entry["service"], record_id), entry["model_id"])
    verified = next((value for key, value in native.items()
                     if candidate and key.lower() == candidate.lower()), None)
    if entry["service"] != "hugging-face-inference-providers" and (router_only or entry["model_id"] is None and verified):
        entry["model_id"] = verified["id"] if verified else None
        if verified:
            entry["native_evidence"] = verified
        else:
            entry["unknown"] = ["model_id"]
    for key in ("endpoint", "pricing"):
        if key in item:
            entry[key] = item[key]
    if item.get("model_id") and item["model_id"] != entry["model_id"]:
        entry["notes"] = item["model_id"]
        if router_only and entry["model_id"] is None:
            entry["notes"] += "; native provider model ID not verified in staged service research."
    if item.get("source"):
        entry["source"] = item["source"]
    for key in ("endpoint", "pricing"):
        value = entry.get(key)
        if not isinstance(value, str):
            continue
        uncertain = re.search(r"\b(unverified|unknown|not found|not captured|not verified|did not|cannot)\b", value, re.I)
        documented_path = re.match(r"^(?:(?:GET|POST|PUT|PATCH|DELETE)\s+)?(?:https://\S+|/\S+)", value)
        if uncertain or key == "endpoint" and not documented_path:
            entry[key] = None
            explanation = f"Unverified {key}: {value}"
            entry["notes"] = "; ".join(filter(None, (entry.get("notes"), explanation)))
    return entry


def map_nullable(items, mapper, *, drop_none=False):
    """Map known lists without turning an explicit unknown into an empty list."""
    if items is None:
        return None
    mapped = [mapper(item) for item in items]
    return [item for item in mapped if item is not None] if drop_none else mapped


def compile_catalog() -> dict:
    batches, gaps = {}, []
    for letter in "ABCDEFG":
        path = RAW / f"batch-{letter}.json"
        if not path.exists():
            gaps.append({"batch": letter, "reason": f"raw/{path.name} is missing; its records are not in the catalog"})
            continue
        batches[letter] = json.loads(path.read_text(encoding="utf-8"))
    rows = verification_rows()

    raw_services = [record for letter in SERVICE_BATCHES if letter in batches for record in batches[letter]["records"]]
    native_models = {
        record["id"]: {
            item["id"]: {"id": item["id"], "batch": f"raw/batch-{letter}.json", "notes": item.get("notes")}
            for item in record.get("notable_models") or [] if item.get("id")
        }
        for letter in SERVICE_BATCHES if letter in batches for record in batches[letter]["records"]
    }
    undecided = {record["id"] for record in raw_services} - set(SERVICES)
    if undecided:
        raise SystemExit(f"raw service records without a decision in SERVICES: {sorted(undecided)}")

    official_hosts = set()
    for record in raw_services:
        official_hosts.add(urlsplit(record["homepage"]).hostname)
        official_hosts.update(urlsplit(item["url"]).hostname for item in record["sources"] if item.get("official"))
    official_hosts.discard("huggingface.co")

    models = []
    index = {"repos": {}, "served": {}}
    for raw in batches.get("F", {}).get("records", []):
        orgs = {repo.split("/")[0].lower() for repo in raw.get("hf_repos") or []}
        record = dict(raw)
        record["served_by"] = map_nullable(raw.get("served_by", []), lambda item: served_entry(item, raw["id"], native_models))
        record["sources"] = map_nullable(raw.get("sources", []), lambda item: source_obj(item, official_hosts, orgs))
        models.append(with_unknown(record))
        for repo in raw.get("hf_repos") or []:
            index["repos"].setdefault(repo.lower(), raw["id"])
        for item in record["served_by"] or []:
            if item["model_id"] is None:
                continue
            # Qualified router notes must never enter the native-ID index.
            aliases = item["model_id"]
            if not item.get("native_evidence"):
                aliases = item.get("notes") or aliases
            for part in aliases.split(";"):
                model_id = first_id(part)
                if model_id:
                    index["served"].setdefault((item["service"], model_id.lower()), raw["id"])

    media = []
    for raw in batches.get("G", {}).get("records", []):
        orgs = {raw["hf_repo"].split("/")[0].lower()} if raw.get("hf_repo") else set()
        record = dict(raw)
        record["served_by"] = map_nullable(raw.get("served_by", []), lambda item: served_entry(item, raw["id"], native_models))
        record["sources"] = map_nullable(raw.get("sources", []), lambda item: source_obj(item, official_hosts, orgs))
        media.append(with_unknown(record))

    services = [service_record(raw, SERVICES[raw["id"]], rows, index) for raw in raw_services]
    return {
        "schema": "personal-agent/model-service-catalog/v1",
        "reviewed_at": REVIEWED_AT,
        "review_interval_days": INTERVAL,
        "compiled_from": [f"raw/batch-{letter}.json" for letter in batches] + ["VERIFICATION.md"],
        "gaps": gaps,
        "services": services,
        "models": models,
        "media": media,
    }


def billing_summary(plans: list[dict]) -> str:
    summaries = []
    for item in plans:
        billing = item["billing"]
        price = item["usd_per_month"]
        label = item["name"] + (f" (${price:g}/month)" if price is not None else " (price unknown)")
        allowance = billing["allowance"]
        if allowance is None:
            usage = billing["mode"]
            if billing["mode"] in ("free", "allowance"):
                usage += "; allowance unknown"
        else:
            amount = allowance["amount"]
            usage = (f"{amount:g}" if amount is not None else "amount unknown")
            usage += f" {allowance['unit']} / {allowance['reset_window']}"
        summaries.append(f"{label}: {usage}; overage {billing['overage']}")
    return "; ".join(summaries) if summaries else "Unknown"


def render_readme(catalog: dict) -> str:
    """Generate the index from the same data as the catalog, including gaps."""
    counts = ", ".join(f"{len(catalog[key])} {key}" for key in ("services", "models", "media"))
    lines = [
        f"# Model service research (reviewed {catalog['reviewed_at']})", "",
        "Generated by `compile_catalog.py` from staged research and operator spot checks.", "",
        "| File | What it is |", "|---|---|",
        f"| [catalog.json](catalog.json) | Compiled `personal-agent/model-service-catalog/v1`: {counts}. Holds no secrets. |",
        "| [SCHEMA.md](SCHEMA.md) | Catalog schema, preset rules and discovery rules. |",
        "| [VERIFICATION.md](VERIFICATION.md) | Operator spot checks; override conflicting batch claims. |",
        "| [IMPLEMENTATION-SPEC.md](IMPLEMENTATION-SPEC.md) | Assignment specifications, including endpoint path rules. |",
        "| [compile_catalog.py](compile_catalog.py) | Deterministic compiler for catalog.json and this index. Per-service decisions are in `SERVICES`. |",
        "| `raw/batch-A.json` through `raw/batch-E.json` | Verbatim service research: A-D hosted/subscription services, E custom hosting. |",
        "| `raw/batch-F.json`, `raw/batch-G.json` | Verbatim model and media research. |",
        "| `raw/prompts/prompt-*.md` | Prompts used to produce each research batch. |", "",
        "## Re-running", "",
        "1. Read SCHEMA.md and re-run the matching `raw/prompts/prompt-<batch>.md`; stage the JSON as `raw/batch-<batch>.json` (shape: `{batch, records, open_questions}`).",
        "2. Update VERIFICATION.md spot checks and the compiler's source-backed decisions as needed.",
        "3. Run `python projects/personal-agent-os/research/model-services/compile_catalog.py`. Both catalog.json and README.md are regenerated. A service without a decision or a decided plan absent from its batch fails compilation.",
        "4. Run `python -m unittest tests.test_model_service_catalog tests.test_model_services tests.test_model_services_research_files` or inspect with `agent-os orchestrate services list|show|validate`.", "",
        "## Research gaps", "",
        "Missing batches appear in the catalog's top-level `gaps`; their records are omitted.", "",
    ]
    if catalog["gaps"]:
        lines.extend(f"- `batch-{gap['batch']}.json`: {gap['reason']}" for gap in catalog["gaps"])
    else:
        lines.append("**Current gaps: none.** All batches A-G are present.")
    lines.extend([
        "", "Batch G is partial: see its `open_questions` for provider coverage, voice-cloning and diarization candidates, and missing privacy/pricing research. Other unresolved fields remain in each record's `unknown` and `findings`.", "",
        "## Compilation rules", "",
        "- Preserve nulls and raw unknown lists. Unknown restrictions do not mean no restrictions. Custom-contract plans whose billing mode is unverified are named in service notes and unknown lists.",
        "- Unverified served-by endpoint/pricing prose becomes null, with the original explanation in notes, exact field paths in unknown and an unverified finding.",
        "- Venice Free's 10 text prompts/day and 15 image prompts/day apply to the web. Its API allowance remains unknown.",
        "- Overage is blocked only when sources say requests stop, metered when paid usage is documented, otherwise unknown. Unknown overage counts as paid under `allow_paid_spend=false`.",
        "- OpenAI endpoint path styles are explicit (`root`, or `append_v1` for Novita). Model-list paths are relative to the API root; base URLs have no trailing slash.",
        "- Chat endpoints hold `secrets://<service-id>/<endpoint-id>` references. Extra endpoints have their own references, even when they use the same key as default.",
        "- Anthropic SDK bases derived from documented full messages URLs omit the `/v1/messages` suffix and retain a note.",
        "- HF router IDs identify HF routes. Backing-provider native IDs require staged service evidence (`native_evidence`); otherwise model_id is null and router qualifications stay in notes and findings.", "",
        "## Services", "",
        "| service id | category | integration_status | billing summary | key restriction |",
        "|---|---|---|---|---|",
    ])
    for service in catalog["services"]:
        restriction = service["restrictions"]["notes"] or service["integration_notes"]
        cells = (service["id"], service["category"], service["integration_status"],
                 billing_summary(service["plans"]), restriction)
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", " ") for cell in cells) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    catalog = compile_catalog()
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    README.write_text(render_readme(catalog), encoding="utf-8")
    counts = ", ".join(f"{len(catalog[key])} {key}" for key in ("services", "models", "media", "gaps"))
    print(f"wrote {OUT.name} and {README.name}: {counts}")


if __name__ == "__main__":
    main()
