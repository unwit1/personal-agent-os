# Model services: catalog and provider presets

The source-backed catalog lives at
[`projects/personal-agent-os/research/model-services/catalog.json`](../projects/personal-agent-os/research/model-services/catalog.json).
It records services, plans, endpoints, model facts, media candidates, sources,
unknown fields, and findings. Read the [schema](../projects/personal-agent-os/research/model-services/SCHEMA.md),
[verification notes](../projects/personal-agent-os/research/model-services/VERIFICATION.md),
[research batches](../projects/personal-agent-os/research/model-services/raw/), and
[catalog index](../projects/personal-agent-os/research/model-services/README.md)
before relying on a plan or price. A stale review warning means the source
needs checking again. If the catalog has not been compiled, the services list
and GUI say so; presets need the compiled file.

## Review and configure

```powershell
python agent.py orchestrate services list
python agent.py orchestrate services list --category subscription_allowance
python agent.py orchestrate services show nanogpt
python agent.py orchestrate services validate
python agent.py orchestrate secrets set secrets://<service>/default
python agent.py orchestrate services discover <service> --endpoint <endpoint>
python agent.py orchestrate services add <service> --model <exact-model-id> --classes fast,balanced
python agent.py orchestrate services add <service> --model <exact-model-id> --classes fast,balanced --plan <plan-id> --write
python agent.py orchestrate services bridge <service> --plan <plan-id> --model-map sonnet=<exact-model-id>
python agent.py orchestrate services bridge <service> --plan <plan-id> --model-map sonnet=<exact-model-id> --write
```

Use the IDs printed by `list` and `show`; the examples with angle brackets
are placeholders. `show` gives plan terms, endpoint IDs and secret references.
Store the key for the selected endpoint; a nondefault endpoint normally uses
`secrets://<service>/<endpoint>`. MiniMax, Kimi and Z.ai coding plan keys may
differ from their pay as you go API keys: check each catalog record and store
the appropriate key under its endpoint reference. Secrets live in the local
keyring or environment, never in the provider registry.

`discover` makes a read-only GET to a documented model-list path and caches
model IDs under the local orchestrator home in `service-models/`. It errors when
no list path is documented or a required key is missing. `add` and
`bridge` preview a registry entry by default; inspect it, then use `--write`
to register it locally. `--ack-terms` records that you read terms when
automation permission is unclear. Explicitly forbidden automation is refused
even with that flag. A plan limited to named coding clients cannot be added
as a generic OpenAI endpoint. Choose a plan and endpoint deliberately; the
presets do not add vendor provider-selection request parameters.

### Which setup path fits

| Service type | Setup |
|---|---|
| Subscription allowance with an OpenAI-compatible endpoint | Check plan allowance, reset and overage in `show`; store the endpoint key, preview `services add`, then write. |
| Coding plan that lists Claude Code | Store its coding-plan key, preview `services bridge --plan ...`, then write. The bridge configures Claude Code's `ANTHROPIC_BASE_URL`, optional model aliases, and a secret reference for `ANTHROPIC_AUTH_TOKEN`. It needs a documented Anthropic Messages endpoint and Claude Code available locally. |
| Hosted text/code API | Review prices and restrictions, store its API key, discover model IDs when supported, then add the exact model ID. |
| Custom hosting | Provision and serve the model separately, then use `orchestrate model-add` with its base URL, model ID, secret reference and path style. The service catalog itself does not provision GPUs. |

The GUI's **Model services** panel shows the same catalog and offers model
listing, preview and registration. Opening it reads local catalog data; the
vendor model-list request starts only when you select **List models**.

## Endpoint paths and billing

`path_style` controls the URL built for OpenAI-compatible calls. `root` uses
the base URL as the API root, such as `https://api.groq.com/openai/v1` plus
`/chat/completions`. `append_v1` adds `/v1` first, such as a base
`https://api.novita.ai/openai`; it adds `/v1` even if the base already ends in
a version segment. `auto` keeps a final version segment like `/v1` or `/v4`,
otherwise adds `/v1`. Model-list paths are relative to the
resolved API root. Check the documented full URL, especially for endpoints
with a nonstandard prefix.

An allowance records its unit, amount if known, reset window, and overage.
`blocked` means the allowance cannot incur usage charges after exhaustion;
`metered` can. An `unknown` overage is treated as paid by the provider gate,
so `allow_paid_spend=false` blocks it. The catalog does not meter your
remaining allowance or enforce a vendor's balance.

NanoGPT's subscription endpoint is separate from its ordinary API endpoint.
Its verified docs say explicit provider selection bypasses subscription
coverage and bills pay as you go; the preset does not set provider selection.
Poe API usage consumes subscription points, with additional points available
for purchase. Featherless Chat excludes coding agents and background
automation, while its Developer plan is metered. Chutes Plus and Pro have
bundled daily quotas with metered overage; reported dollar-value caps are
secondary-source claims, not a verified API limit. Coding-plan client lists
and automation terms vary by service: review them before writing a preset.

## Use a registered provider as foreman

The GUI's **Session foreman** panel offers **Registered provider** and shows
eligible providers and models. The CLI uses the foreman's existing parser:

```powershell
python agent.py orchestrate foreman use registered --provider <provider-id> --model <optional-model-id>
```

An eligible provider must be enabled, available to its adapter probe,
allowed the planner role, and use a supported API or coding CLI adapter. A
`services add` preset defaults to the `inline` role, so include
`--roles inline,planner` when previewing and writing an endpoint that should
serve as foreman. A `services bridge` preset includes `planner` by default.
The foreman uses the existing provider; paid provider gating still applies.

## Plan headroom: routing by what is left

`orchestrate headroom` shows how much of each subscription allowance is left
and how routing treats it. `--refresh` rereads every source now.

| Plan | Source | Windows |
|---|---|---|
| Codex (ChatGPT) | last `rate_limits` in `~/.codex/sessions` logs (free) | 5 hours, weekly |
| Claude Code | `rate_limit_event` from a one-line Haiku probe, at most every 20 minutes, in the background | 5 hours, weekly |
| NanoGPT subscription | `GET /api/subscription/v1/usage` with the endpoint key (free) | weekly (and daily when set) |

Every NanoGPT provider entry shares one account allowance. The engine and
`work_delegate` read the cache (`~/.agent-os/headroom.json`) at most every
30 seconds and apply it in `router.select`:

- **exhausted**: a window is 98% or more used. The provider is skipped until
  that window resets, and a backup foreman plans instead.
- **tight**: under 15% left, or well ahead of an even pace with under half
  left. Relative cost is multiplied by 3, so a plan with room wins.
- **expiring**: the window resets within 10% of its length with over 40%
  unused. Cost is multiplied by 0.6, so allowance that would be lost is used.
- **ok** or **unknown**: cost is unchanged.

Reactive cooldowns after a refusal (`provider_health.py`) still apply. A 429
that says the model is overloaded counts as `unavailable` (a short breaker),
not `quota`, so a busy model does not bench the whole plan.

## Sensitive runs

The run policy key `sensitive_data` (`true`, `false` or `"auto"`, the
default) keeps work and personal records on your own subscriptions and local
models. For a sensitive run, no node, the foreman included, may use a
third-party host or a per-token API: the foreman's backup plans instead.
`"auto"` is true for runs in the repositories listed in
`model_profile.DEFAULT_SENSITIVE_REPOS` (HR GUI, RTEC-HR, Job Applicant
Dashboard, OvertimeParser, ScanRenamer, agentos-ambient-capture,
iphone-message-archive). A JSON list in `~/.agent-os/sensitive-repos.json`
replaces that list. NanoGPT's subscription is for one person's
non-commercial use, which is a second reason to keep work runs off it.

## Research: which included model for which task

```powershell
python agent.py orchestrate services research nanogpt
python agent.py orchestrate services research nanogpt --family planning
python agent.py orchestrate services research nanogpt --measure-multiplier <model-id>
```

The command reads the live subscription catalog and allowance, ranks
included models per task family (planning, coding_agent, long_context,
extraction, triage, vision, uncensored_writing), and writes
`projects/personal-agent-os/research/model-services/nanogpt-fit.json`.
Ranking uses measured evidence first (pooled `orchestrate foreman eval`
reports, by Wilson lower bound, and capability observations), then cited
priors in `nanogpt-priors.json`, then declared capabilities and recency.
`--measure-multiplier` finds whether a model counts 1x or 2x against the
allowance, which the catalog does not publish. It makes one short request and
compares the change in weekly units with the prompt tokens. A reading taken
while other work uses the account is marked `noisy`.

To evaluate a candidate foreman without letting it take over routing,
register it with a high relative cost and run the eval:

```powershell
python agent.py orchestrate services add nanogpt --endpoint subscription --plan pro --model <id> --provider-id nanogpt-ev-<name> --classes reasoning,balanced --roles planner --cost 50 --write
python agent.py orchestrate foreman eval --provider nanogpt-ev-<name> --split dev
```

## Model evidence

Open weights describe availability of model weights; a license governs their
use. Low-refusal tuning describes observed behavior. Abliteration is a
specific modification claim and needs evidence; none of these labels prove
task competence. Public benchmarks are useful priors. Use
`orchestrate eval-queue plan` and `orchestrate eval-queue run` for queued
served models, and `orchestrate foreman eval` for labeled foreman choices.
Compare task-family validation, refusals and cost before changing routing.
