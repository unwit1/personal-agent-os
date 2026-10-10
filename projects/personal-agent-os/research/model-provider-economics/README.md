# Model / provider economics and external benchmarks

**Snapshot 2026-10-10.** Cited desk research for IMP-0015 Model Infrastructure Manager / Compute Broker. **No new Agent OS inference benchmarks executed.** This directory is a dated research corpus, NOT runtime routing configuration or permission to spend.

## Agent entrypoints

| File | Content |
|---|---|
| [model-prices-2026-10-10.json](model-prices-2026-10-10.json) | 26 model + provider pairs with exact API IDs, USD per million input/output tokens, context, source and caution notes |
| [provider-gpu-prices-2026-10-10.json](provider-gpu-prices-2026-10-10.json) | 16 subscription plans with limits and usage eligibility, 24 GPU rental quotes, storage/fees |
| [published-benchmarks-2026-10-10.json](published-benchmarks-2026-10-10.json) | 24 published coding, reasoning and agentic metrics with model variants, eval config, evidence type; **not** Agent OS measurements |
| [openrouter-low-refusal-2026-10-10.json](openrouter-low-refusal-2026-10-10.json) | 9 OpenRouter/Venice low-refusal model candidates with exact slugs, price, tool API availability and claim confidence |
| [openrouter-low-refusal-analysis.md](openrouter-low-refusal-analysis.md) | Research conclusions, GLM vs Heretic A/B design, misadvertised tool support, low-refusal and coding eval methodology |

Filter these records by project requirements and potential candidates, not by dumping entire catalogs into prompts. Reuse the current Orchestrator capability, evaluator, router, budget gate and FreeComputeBroker instead of implementing duplicate machinery. Source of truth for implementation: [model infrastructure](../../../../docs/model-infrastructure.md), [free broker](../../../../docs/free-compute-broker.md), and the IMP-0015 roadmap.

## Expanded research pass — 2026-10-10

**Research-only, committed in multiple checkpoints.** This expands the earlier reference without changing routing, paying providers, or running new model inference. The new catalog entries are source-backed but remain incomplete relative to the global market.

| New artifact | Scope | Count |
|---|---|---:|
| [Open-weight publisher artifacts](open-weight-artifacts-2026-10-10.json) | Exact Hugging Face weight IDs/quantized variants with publisher source and license-check status; **not** hosted API IDs | 77 across 13 families |
| [Open-weight benchmark evidence](open-weight-benchmark-evidence-2026-10-10.json) | Scores from Gemma 4 official tables, GLM and gpt-oss model cards; publisher claims distinguished from Hub evals | 41 |
| [Provider official API quotes](provider-official-api-quotes-2026-10-10.json) | Together, Fireworks, Cerebras public listed token input/output rates (runnable API identifiers still unverified) | 31 |
| [Provider/subscription mechanics](service-commercial-mechanics-2026-10-10.json) | API vs interactive subscription vs GPU billing, eligibility, quota windows, technical caveats | 25 services |
| [Benchmark suite methods](benchmark-methodologies-2026-10-10.json) | Independent benchmark URLs, comparable harness/version rules, evaluator limitations | 12 |
| [Continuous Discovery Plan](CONTINUOUS-DISCOVERY-PLAN.md) | No-dependency-first Model Radar ingestion, price+terms refresh, eval/approval gates and testable milestones | One architecture guide |
| [Model catalog adapter contract](model-catalog-adapter-contract-2026-10-10.md) | Exact Models.dev `models.json`/`api.json`/`catalog.json`, LiteLLM USD/token conversion, OpenRouter endpoints, cross-source validation and safe read-only import requirements | One source/schema guide |
| [Paperclip and related orchestration](../prior-art/paperclip-integration-analysis-2026-10-10.md) | Atomic checkouts, heartbeats, agent budgets, scoped skills/goals and optional bridge | 13 repo/data-service candidates in [structured discovery](../prior-art/discovery-paperclip-and-model-data-2026-10-10.json) |

**Source note:** Current Artificial Analysis [Coding Agent Index v1.5 methodology](https://artificialanalysis.ai/methodology/coding-agents-benchmarking) contains DeepSWE v1.1 + Terminal-Bench **4.0** + SWE-Atlas-QnA; the older Terminal-Bench 2.1 and older index values already present elsewhere are not interchangeable. Always record benchmark revision. Pricing examples are dated observations with per-provider endpoints, and model-weight file IDs are not directly routable API strings.

**Next agent:** Use `CONTINUOUS-DISCOVERY-PLAN.md` as IMP-0015 guidance. First implement read-only multi-source ingestion into existing Research Radar, and reconcile the current source snapshot with live OpenRouter endpoints. Never auto-upgrade a subscription or provision a GPU. Separate interactive-coding-only plans from automated production inference. Candidate real benchmarks require the existing EVS/CAP/EVR harness and explicit spend limits.

---

## Select API price comparisons

Rates in USD per 1 million tokens; discounts and routing can change. They exclude OpenRouter platform fees, taxes, tools, prompt caching, failures and retries.

| Provider / model | Input | Output | Reference |
|---|---:|---:|---|
| OpenRouter DeepSeek V4 Flash 0731 | $0.03 | $0.13 | [quote](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) |
| OpenRouter GLM 4.7 Flash | $0.06 | $0.40 | [quote](https://openrouter.ai/z-ai/glm-4.7-flash) |
| Venice GLM 4.7 Flash Heretic | $0.07 | $0.40 | [provider model IDs](https://github.com/veniceai/api-docs/blob/main/models/text.mdx) |
| OpenRouter DeepSeek V4.1 Flash | $0.13 | $0.52 | [quote](https://openrouter.ai/deepseek/deepseek-v4.1-flash) |
| OpenRouter MiniMax M2.7 | $0.21 | $0.84 | [quote](https://openrouter.ai/minimax/minimax-m2.7) |
| Venice Abliterated Large V2 | $3.00 | $5.00 | [provider model IDs](https://github.com/veniceai/api-docs/blob/main/models/text.mdx) |

**Pricing drift observed:** The OpenRouter GLM 5.2 direct-open page on October 10 presented a $0.06/$7 routing headline, in sharp contrast to a cached prior quote of $0.4875/$1.56. Keep both figures as historical evidence in the JSON row; before any runtime use, retrieve current per-endpoint quote and exclude anomalous listings until verified. Same model name does not guarantee same provider or effective price.

**Illustrative scenario** with 10M uncached input and 1M output tokens (10:1); multiply by 10 for 100M input + 10M output: OpenRouter DeepSeek V4 Flash 0731 **$0.43**; GLM 4.7 Flash **$1.00**; Venice Flash Heretic **$1.10**; DeepSeek V4.1 Flash **$1.82**; MiniMax M2.7 **$2.94**; Venice Abliterated Large V2 **$35.00**. Arithmetic only, NOT equivalent task quality or actual measured performance.

**OpenRouter fees:** [current pricing](https://openrouter.ai/pricing) lists Standard at 5.5% platform fees and a limited free tier (50 requests/day). Confirm fee mechanics on funding; avoid counting it both as a top-up fee and a per-inference surcharge. Direct Z.ai [model prices](https://docs.z.ai/guides/overview/pricing) offer free GLM-4.7-Flash under unspecified operational limits—confirm per-key rate/eligibility/health live.

## Coding plans vs actual unattended compute

- [MiniMax Token Plan](https://platform.minimax.io/subscribe/token-plan): Plus $20/mo, Max $50/mo, Ultra $120/mo. Claimed ~1.7B, 5.1B and 12.5B M3-equivalent monthly tokens are **provider estimates**; 5-hour/weekly quota windows and concurrent-agent limits apply. Intended mainly for individual interactive coding, not general-purpose production API farming. Direct pay-as-you-go is separate.
- [Z.ai Coding Plan](https://docs.z.ai/devpack/overview): starts at $18 Lite; public tracked Pro $80 and Max $168 ([price change evidence](https://www.usagepricing.com/blueprint/activity/zhipu-ai-2026-09-07-coding-plan-team-pricing)). Lite 2,000 credits/5h and 10,000/week; Pro 12,000/60,000; Max 28,000/140,000. Credits are weighted by model input, cached input and output, and older model aliases may resolve to GLM-5.3 or GLM-5.3-Flash. Reconfirm Pro/Max price before purchasing.
- [Kimi membership](https://www.kimi.ai/help/membership/membership-overview): $19/$39/$99/$199 monthly tiers; [Kimi Code](https://www.kimi.com/en/help/kimi-code/membership-guide) has third-party coding-tool keys, shared credits and rolling limits. Generic product APIs use a separate billing plan.
- [Chutes pricing](https://chutes.ai/pricing): $10 Plus and $20 Pro, daily quota and discounted PAYG; [5x PAYG-equivalent cap](https://chutes.ai/news/community-announcement-february) can be applied in short windows. Not unlimited.
- [Featherless](https://featherless.ai/pricing): **$25 Chat is ineligible for coding agents, automation or benchmarking**; $50 Developer is prepaid credits with token metering and explicitly allows background agents. Do not confuse prepaid balance with free inference.
- [Alibaba coding plan](https://www.alibabacloud.com/help/en/model-studio/coding-plan): $50/month, capped 6,000/5h, 45,000/week, 90,000/month; [automated scripts and noninteractive backend use explicitly prohibited](https://docs.modelstudio.console.alibabacloud.com/en/model-studio/coding-plan). Ineligible for unattended Orchestrator workflows.

Provider restrictions are first-class route eligibility filters, before price optimization. No quota evasion, shared account usage, client impersonation, silent subscription or auto-purchasing.

## GPU prices and break-even rules

[Runpod GPU pricing](https://www.runpod.io/pricing) public Oct snapshot: Pod A5000 24GB $0.27/h, 4090 24GB $0.89/h, A40 48GB $0.59/h, A100 PCIe 80GB $1.79/h, H100 PCIe 80GB $2.89/h; Serverless 4090 $1.10/h, A100 $2.72/h, H100 $4.79/h. [Modal](https://modal.com/pricing) examples derived by converting per-second rates: L4 $0.7992/GPU-h, L40S $1.9512/GPU-h, A100 80GB $2.4984/GPU-h, H100 SXM5 $3.9492/GPU-h, **excluding CPU, RAM, egress and storage**. Also investigate [Lambda](https://lambda.ai/pricing) and live supply-priced [Vast](https://vast.ai/pricing).

Compare GPU with APIs only after validating model+quantization+context KV cache+parallel workers fit VRAM. A $0.89/h 4090 does NOT imply it can run a 500B+ parameter model. Estimate API cost = uncached input M * price + cached input M * cache rate + output M * price + tool charges + retries + fees. GPU total = (startup + warmup + busy + idle billed GPU time) * GPU rate + CPU/RAM + storage + network + downtime/retries. Decision metric: **total actual dollars per independently verified accepted task**, subject to capability, correctness and authorization floors. Never invent tokens/s or cache hit rates; measure them.

## What published benchmarks mean

Selected evidence: GLM 4.7 Flash GPQA Diamond 58.1% (Artificial Analysis reasoning; [source](https://openrouter.ai/z-ai/glm-4.7-flash)); DeepSeek V4.1 Flash SciCode 51.9% (Artificial Analysis max reasoning; [source](https://openrouter.ai/deepseek/deepseek-v4.1-flash)); GLM 5.2 AA Coding Index 68.8 and Terminal-Bench **2.1** 77.9% (max reasoning; [source](https://openrouter.ai/z-ai/glm-5.2)); MiniMax M2.7 SWE-**Pro** 56.2% and Terminal Bench **2** 57% (**vendor claims**, not independently verified harness; [source](https://openrouter.ai/minimax/minimax-m2.7)). These are NOT directly comparable across different benchmarks, variants, harnesses or effort levels. Neither Heretic nor Abliterated Large V2 has verified matched coding scores in this catalog; do not inherit base model metrics.

## Existing Orchestrator handoff: next actions

1. Read IMP-0015, the current registry, CAP/EVR and FreeComputeBroker, and deduplicate; do not build another routing/eval system.
2. Refresh live price, selected provider endpoint, rate limits, terms and model ID before spending or auto-routing; retain historical conflicting quotes.
3. Use existing paired EVS task cases and holdouts. In a controlled low-risk trial, compare standard GLM 4.7 Flash vs Venice Flash Heretic and DeepSeek V4 Flash 0731; escalate to DeepSeek V4.1 Flash and MiniMax M2.7 only if quality merits.
4. Capture provider/model revision, quantization, tool schema, prompt context, task family, token split/cache, TTFT, throughput, refused vs unsupported vs timeout, retry, cost, validator success and wall time. Run >=3 samples per case and enough distinct cases to report uncertainty, not just one demo.
5. Compare cost per verified successful task, quality floor, reliability and caps. Store append-only EVR/CAP/EXP; negative results remain. GPU quotes require measured warmup/throughput/utilization.
6. Do not buy a plan, spin up GPU, touch protected eval paths or promote routing without the established approval/validation gates. Publication of future discoveries should reuse Model Research Radar, not overwrite this dated snapshot.

**Refresh targets (proposed, not implemented):** prices <=24 hours before paid routing; eligibility/quotas/spot GPU availability immediately before actions; subscription terms at purchase and at least every 30 days; model benchmark priors per revision at least monthly. Preserve provenance and drift.

**Scope and limitations:** a representative, source-backed comparison rather than every model/provider in the world. Zero subscriptions purchased, GPU hours consumed or new benchmark runs. Quotes can be volatile, based on model and serving endpoint. All research files are static data, not instructions to circumvent policy or remove guardrails.
