# OpenRouter low-refusal / abliterated-model research (2026-10-10)

**Status: catalog research only, no new paid inference or direct model comparisons.** Supplements IMP-0015, the [provider model price catalog](model-prices-2026-10-10.json), and the separate [candidate metadata](openrouter-low-refusal-2026-10-10.json).

## Executive result

OpenRouter has **low-refusal, uncensored fine-tuned models** (Nous Hermes, Cognitive Computations Dolphin, Venice Uncensored, TheDrummer). A model being described as uncensored does **not** establish that its weights were abliterated, that the OpenRouter endpoint has live capacity, or that its endpoint accepts native tool calls. As of this research, no live OpenRouter listing for the **specific community-abliterated GLM 4.7 Flash Heretic** endpoint was validated. It **is** documented on **Venice directly**. Do not invent an OpenRouter slug for it or assume a normal GLM request calls the modified weights.

## Candidate matrix

| Route / model slug | Prompt / completion $ per 1M | Context | Native API tools, confirmed? | Proper experimental role |
|---|---:|---:|---|---|
| [OpenRouter GLM 4.7 Flash](https://openrouter.ai/z-ai/glm-4.7-flash) `z-ai/glm-4.7-flash` | $0.06 / $0.40 | 200K | **Yes (OpenRouter FAQ)** | Baseline coding/tool use |
| [Venice GLM 4.7 Flash Heretic](https://cdn.venice.ai/models/olafangensan-glm-4-7-flash-heretic) `olafangensan-glm-4.7-flash-heretic` | $0.07 / $0.40 | 200K | **Yes (Venice claim)** | **First abliterated A/B candidate**; **Venice API not OpenRouter** |
| [OpenRouter Hermes 4 405B](https://openrouter.ai/nousresearch/hermes-4-405b) `nousresearch/hermes-4-405b` | $1.00 / $3.00 | 131K | **NO per serving endpoint FAQ**; model description claims support | Expensive reasoning/text-only or offline JSON experiment |
| [OpenRouter Dolphin 3.0 R1](https://openrouter.ai/cognitivecomputations/dolphin3.0-r1-mistral-24b:free) `cognitivecomputations/dolphin3.0-r1-mistral-24b:free` | FREE-listed | 33K | Unknown; no live tool parameter evidence | Cheap isolated reasoning/text pilot, if endpoint responds |
| [OpenRouter Dolphin 3.0](https://openrouter.ai/cognitivecomputations/dolphin3.0-mistral-24b:free) `cognitivecomputations/dolphin3.0-mistral-24b:free` | FREE-listed | 33K | Unknown | Isolated text/instruction pilot, if endpoint responds |
| [OpenRouter Venice Uncensored 24B](https://openrouter.ai/cognitivecomputations/dolphin-mistral-24b-venice-edition) `cognitivecomputations/dolphin-mistral-24b-venice-edition` | $0.20 / $0.90 | 128K | **NO per OpenRouter FAQ** | Uncensored text-only specialist |
| [OpenRouter TheDrummer Cydonia 24B](https://openrouter.ai/thedrummer/cydonia-24b-v4.1) `thedrummer/cydonia-24b-v4.1` | $0.30 / $0.50 | 131K | **NO per OpenRouter FAQ** | Creative/non-coding tasks |
| [OpenRouter Hermes 4 70B](https://openrouter.ai/nousresearch/hermes-4-70b) `nousresearch/hermes-4-70b` | Unpriced at current page | 131K | Unknown (model claims yes) | Research queue pending active endpoint |
| [OpenRouter Dolphin Llama 3 70B](https://openrouter.ai/cognitivecomputations/dolphin-llama-3-70b) `cognitivecomputations/dolphin-llama-3-70b` | Unpriced at current page | 8K | Unknown | Low priority: too little context and no live quote |

**Verification level** matters: Free-listed model cards are not equivalent to successful inference; a model’s training dataset and model-card capability claims do not prove the provider’s `supported_parameters` includes `tools`. OpenRouter Hermes 4 405B illustrates a direct contradiction: model description touts function calling while its endpoint FAQ explicitly says `tools` are unsupported. Endpoint-specific structured output enforcement also varies. Fail closed for native tool requirements.

## Economics for an identical 10M-uncached-input / 1M-output workload

OpenRouter base GLM 4.7 Flash **$1.00**; Venice Heretic **$1.10**; OpenRouter Venice Uncensored **$2.90**; Cydonia **$3.50**; Hermes 4 405B **$13.00**. Token-only assumptions; not equal quality, speed, retries, availability or verified tasks. OpenRouter Standard has [5.5% platform fee](https://openrouter.ai/pricing) associated with funding; avoid counting it twice. Venice Heretic [lists $0.04/M cached input](https://cdn.venice.ai/models/olafangensan-glm-4-7-flash-heretic), OpenRouter base GLM [lists $0.01/M](https://openrouter.ai/z-ai/glm-4.7-flash) for an eligible caching endpoint. Do not assume cache hits.

At a 10:1 workload, the Heretic derivative has **10% higher nominal spend** than standard GLM ($1.10 vs $1.00); the difference is primarily input cost. The right decision hinges on legitimate refusal frequency, tool/JSON fidelity, and repeat work. Example: if standard success probability is 0.70 and Heretic 0.80 on identical authorized tasks, simple independent-retry approximation gives $1.00/0.70 = **$1.43** versus $1.10/0.80 = **$1.38** per accepted task. **Illustration only, not observed success probabilities.** Model failures and retries often correlate, so use direct measured task-level totals rather than assuming geometric success.

## Public low-refusal methodology evidence — NOT a GLM benchmark

The open-source [Heretic tool](https://github.com/izikeros/heretic) presents a reproducible Gemma 3 12B comparison: a base model refused 97/100 selected harmful prompts and a Heretic variant refused 3/100, with lower harmless-prompt KL divergence than two other abliterations (0.16 versus 1.04 and 0.45). These results are from a **different model and evaluation configuration**. They do **not** prove GLM Flash Heretic refusal suppression, sustained coding quality, harmless false-refusal rate, or OpenRouter/Runpod compatibility. For Orchestrator, prioritize **benign authorized refusal over-trigger measurements and code correctness**; do not make harmful-prompt compliance a reason for production promotion.

## Suggested rigorous first experiment (existing EVS/CAP/EVR only)

1. Check existing capability registry, EVS suites, price snapshot and consent/budget controls; deduplicate. No new eval harness, no protected holdout changes.
2. Read live [OpenRouter GET models](https://openrouter.ai/docs/api/api-reference/models/get-models) and [per-model endpoints](https://openrouter.ai/docs/client-sdks/typescript/api-reference/endpoints). Match exact IDs, providers, advertised `supported_parameters`, `tools`, structured outputs, max output, current prices, context and region/privacy flags. Filter with `provider.require_parameters=true` where relevant. Probe one harmless native `tools` call per eligible endpoint; never let the router silently ignore it.
3. Against Venice Heretic, use the direct Venice OpenAI-compatible endpoint and exactly documented ID; do not assume both can be billed under one OpenRouter key or that the standard model equals the modified model.
4. Pin a repeatable set of benign tasks: fix a known seeded bug, generate and execute unit tests in sandbox, check schema/tool-call arguments, decompose an issue into a task DAG, generate a safe SQL migration plan (no deployment), summarize repository changes. Pair identical context, time budgets, tool schemas, output lengths and sample counts. Use legitimate ambiguous tasks to measure unwanted refusals; separately identify provider moderation, model refusal, unsupported tools, network errors and authorization-denied actions.
5. Pilot 3 samples per case, then at least 10 labeled cases per task family and >=3 repeats for any routing candidate; confidence intervals and held-out validation. Track actual prompt/cache/completion token splits, per-call billed charge, retries, pass/fail of unit tests, downstream validation overhead, TTFT, latency, code patch mergeability and refusal category.
6. Calculate **cost per independently verified completed task**, not price/M tokens, response length, preference scores or compliance rate alone. Preserve task failures and sample-level traces with sanitized content and evidence records. Refuse promotion if code correctness/authorization floors regress.
7. Optional secondary cohort: Hermes 4 405B **text only** (no tools), free Dolphins only if an actual endpoint and requested capabilities exist, and OpenRouter Uncensored/Cydonia only for matched legitimate specialist tasks. These are not substitutes for native coding agents.

## Guardrails and provider differences

OpenRouter itself cautions that [upstream providers may moderate differently](https://openrouter.ai/blog/tutorials/sillytavern-openrouter/). A model’s lower-refusal training does not trump host policy. For sensitive source code or personal data, eligibility should check [ZDR](https://openrouter.ai/docs/guides/get-started/sovereign-ai), provider data collection, and existing project privacy boundaries before price. Do not send work/employer files to public providers without authorization. Deterministic controls for secrets, spending, privileged commands, file modification and incident audit remain outside model influence.

**Information quality:** these are publicly documented model descriptors and endpoint FAQs fetched October 10, 2026. No authenticated OpenRouter catalog scan, real inference call, measured refusal rate, GPU throughput or confirmed free-provider acceptance was performed. OpenRouter public catalog API search could not be retrieved through the available web access. Re-evaluate both model and provider separately when pricing/availability changes.
