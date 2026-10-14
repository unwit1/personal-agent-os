# NanoGPT subscription: models, limits and routing (2026-10-14)

How the orchestrator divides work between the NanoGPT subscription, Claude
Code and Codex, and what the evidence says about each NanoGPT model. Refresh
the model rankings with `orchestrate services research nanogpt`; check live
allowance with `orchestrate headroom`.

## Your plan limits

| Plan | Allowance | Resets | Past the limit |
|---|---|---|---|
| NanoGPT PRO ($12/month, period ends 2026-11-14) | 60,000,000 input-token units per week; 100 images per day | Monday 00:00 UTC | blocked (429): `allowOverage` and paid overage are off |
| Claude (Claude Code) | 5-hour and weekly windows, reported as a utilization fraction | rolling 5 hours; weekly | blocked: overage rejected |
| ChatGPT Plus (Codex) | 5-hour and weekly windows, reported as a used percentage | rolling 5 hours; weekly | blocked: no credits |

NanoGPT counts **input** tokens only, and cached input still counts. Some
models count 2x. The catalog does not say which, so it is measured with
`--measure-multiplier`. `deepseek/deepseek-v4-pro-0813` counts **2x**.
`Gemma-4-31B-Cognitive-Unshackled`, `z-ai/glm-5.3` and
`qwen/qwen3.8-27b-obliterated:thinking` count 1x. All of today's research and
evals used about 168K of the 60M weekly units.

**Current foreman: `Gemma-4-31B-Cognitive-Unshackled`** (operator choice,
2026-10-14), with backups Claude, then Codex. Rate limits: 60 requests per minute, a burst
of 10 per 10 seconds, and at most 10 concurrent requests. The subscription is
for one person's personal, non-commercial use.

NanoGPT bills pay as you go only through explicit provider selection, the
`X-Billing-Mode: paygo` header, or "Use balance after limits". The presets
use none of these. For defense in depth, set the API key's billing mode to
"Subscription only" in the NanoGPT dashboard; your key's policy currently
allows balance spending (`paidSpendPolicyAllowsBalance: true`).

## Who does what

| Work | Goes to | Why |
|---|---|---|
| Planning (foreman) | the NanoGPT foreman, with backups Claude, then Codex | Planning calls are short (~1.7K input tokens), so they cost the subscription almost nothing and spare Claude and Codex |
| Planning a sensitive run (HR, payroll, applicants, personal archives) | Claude, then Codex | `sensitive_data` keeps third-party hosts off work and personal records |
| Implementing, testing, repairing, reviewing (file edits) | Claude or Codex, whichever has more headroom | NanoGPT models are registered for the planner role only; editing needs a coding CLI agent |
| A plan whose 5-hour or weekly window is nearly used | the other plan | a `tight` plan's cost is multiplied by 3; an `exhausted` plan is skipped until it resets |
| Allowance about to reset unused | the plan with the expiring allowance | an `expiring` plan's cost is multiplied by 0.6 |

The router's order is unchanged: role and requirements filter, then the
cheapest relative cost wins. Headroom only scales that cost or removes an
exhausted plan.

At 14:22 UTC today, both Claude (5-hour window 62% used with 34% of it
elapsed) and Codex (84% used with 32% elapsed) were `tight`, and NanoGPT was
`ok` (0.2% of the week used).

## Foreman evaluation (dev split, 7 labeled planning cases)

`valid` is the share of cases that produced a usable plan. `judge` is the
share sized correctly: the right number of tasks and the right capability
class. `guarded` is the same after the orchestrator's deterministic
corrections (`foreman_strategy`). `cost` is routing cost relative to the
labeled ideal, so 1.0 is ideal.

| Model | Type | valid | judge | guarded | cost | median s |
|---|---|---|---|---|---|---|
| Claude Opus (baseline) | Claude plan | 1.00 | 0.86 | 1.00 | 1.00 | 17.5 |
| z-ai/glm-5.3 | NanoGPT | 1.00 | 0.29 | 1.00 | 1.88 | 34.6 |
| deepseek/deepseek-v4-pro-0813 (2x) | NanoGPT | 1.00 | 0.43 | 0.86 | 1.22 | 10.0 |
| deepseek/deepseek-v4.1-flash | NanoGPT | 1.00 | 0.00 | 0.57 | 2.92 | 17.5 |
| z-ai/glm-5.3-flash | NanoGPT | 1.00 | 0.29 | 1.00 | 1.57 | 138.2 |
| xiaomi/mimo-v2.6-pro | NanoGPT | 0.86 | 0.14 | 0.86 | 2.10 | 115.3 |
| qwen/qwen3.8-27b | NanoGPT base | 0.57 | 0.29 | 0.43 | 1.15 | 24.0 |
| **Gemma-4-31B-Cognitive-Unshackled** | NanoGPT uncensored | 0.86 | **0.57** | 0.86 | 1.24 | 56.1 |
| z-ai/glm-5.3-flash-uncensored | NanoGPT uncensored | 0.86 | 0.29 | 0.86 | 1.51 | 141.6 |
| Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-Derestricted | NanoGPT derestricted | 0.86 | 0.14 | 0.71 | 1.48 | 140.8 |
| huihui-ai/Llama-3.3-70B-Instruct-abliterated | NanoGPT abliterated | 0.71 | 0.43 | 0.57 | 1.15 | 118.3 |
| qwen/qwen3.8-27b-obliterated:thinking | NanoGPT abliterated | 0.71 | 0.43 | 0.43 | 1.00 | 7.0 |
| huihui-ai/DeepSeek-R1-Distill-Llama-70B-abliterated | NanoGPT abliterated | 0.43 | 0.29 | 0.43 | 1.00 | 195.0 |
| qwen/qwen3.8-27b-obliterated | NanoGPT abliterated | 0.29 | 0.29 | 0.29 | 1.00 | 3.5 |

`GLM-4.6-Derestricted-v5` and `z-ai/glm-5.3-flash-apex-abliterated` had not
finished: their calls were repeatedly refused as overloaded. Latency is
NanoGPT's, measured during an overload period, so the slow models may be
faster at other times.

Among the uncensored models, Gemma-4-31B-Cognitive-Unshackled has the best
raw judgment of every NanoGPT model tested. None of them matches Claude
Opus.

Seven cases give wide confidence intervals: treat differences under about
30 points as unproven. The foreman ranking uses the Wilson lower bound over
all pooled cases, so more evals sharpen it.

What the failures look like: the abliterated Qwen often narrated its next
step ("let me grep for secrets first") and returned an empty task list. It
behaved as if it had tools it was not given. Abliteration roughly halved the
base model's valid-plan rate. That matches published findings that Qwen
models degrade more after abliteration than other families do.

In a real run, an empty plan is not fatal. After two malformed planner
responses from the same provider, the engine excludes that provider for the
node, and the normal planner (Claude Opus) plans instead. The cost of a weak
foreman is mostly a few wasted, fast NanoGPT calls plus Claude planning the
runs the foreman fumbles.

## Which subscription model for which task

From `nanogpt-fit.json`, measured evidence first, then cited priors. These
are public benchmark priors, mostly secondary sources; verify before
routing real work.

- **Planning**: `z-ai/glm-5.3` (guarded 1.00) and
  `deepseek/deepseek-v4-pro-0813` (0.86, counts 2x). Pooled older evals also
  rate `deepseek/deepseek-v4-flash` at 0.865 guarded.
- **Long context (around 1M tokens)**: `xiaomi/mimo-v2.6-pro`,
  `z-ai/glm-5.3-flash`, `deepseek/deepseek-v4.1-flash`.
- **Coding (needs a coding CLI bridge)**: `deepseek/deepseek-v4-pro-0813`
  (SWE-bench Verified 80.6, secondary source), `minimax/minimax-m3` (80.5),
  `moonshotai/kimi-k2.6` (80.2), `deepseek/deepseek-v4.1-flash` (LiveBench
  agentic coding 77.3, secondary source).
- **Extraction and structured output**: `xiaomi/mimo-v2.6-pro`,
  `minimax/minimax-m3`, `z-ai/glm-5.3-flash`.
- **Triage and short summaries**: `z-ai/glm-5.3-flash`,
  `qwen/qwen3.8-27b`, `deepseek/deepseek-v4.1-flash`.
- **Uncensored writing**: 23 abliterated, derestricted or uncensored models.
  No published comparisons exist; use the foreman eval or `orchestrate eval`
  for the task you care about.

## Not done yet

- **NanoGPT models as workers.** Registering a cheap NanoGPT model for
  `inline` delegations would move classification and summarization off
  Claude Haiku. `work_delegate` has no sensitive-data guard yet, though, so
  HR text could reach a third-party host. Add that guard first.
- **NanoGPT as a coding agent.** This would go through Codex CLI with a
  custom provider, or a Claude Code bridge. NanoGPT does not document
  subscription coverage through its Anthropic endpoint.
- **Live allowance metering for every call.** Headroom is sampled: Codex and
  NanoGPT every 30 to 300 seconds, Claude every 20 minutes. A burst of work
  inside one sample can overshoot a window before the next reading.

## Sources

- NanoGPT: [subscription usage endpoint](https://docs.nano-gpt.com/api-reference/endpoint/subscription-usage), [models endpoint](https://docs.nano-gpt.com/api-reference/endpoint/models), [support and subscription FAQ](https://nano-gpt.com/support), [provider selection](https://docs.nano-gpt.com/api-reference/miscellaneous/provider-selection)
- Benchmarks: [Artificial Analysis Intelligence Index v4.3](https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3), [GLM-5.2 on the AA index](https://artificialanalysis.ai/articles/glm-5-2-is-the-new-leading-open-weights-model-on-the-artificial-analysis-intelligence-index), [Vellum open LLM leaderboard](https://www.vellum.ai/open-llm-leaderboard), [Pinggy coding LLMs](https://pinggy.io/blog/best_open_source_self_hosted_llms_for_coding/), [Morph open source LLMs](https://www.morphllm.com/best-open-source-llm)
- Abliteration: [Comparative Analysis of LLM Abliteration Methods](https://arxiv.org/abs/2512.13655), [Qwen3.8-27B-abliterated model card](https://huggingface.co/hotdogs/Qwen3.8-27B-abliterated)
- Usage signals: [ccusage (Claude usage sources)](https://pypi.org/project/ccusage/0.1.10/), [codex-ratelimit (Codex session logs)](https://github.com/xiangz19/codex-ratelimit). Each was confirmed locally against your own Claude and Codex output.
