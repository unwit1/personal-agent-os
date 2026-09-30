# Session foreman — progress report

Branch `orchestrator-os/session-foreman` (pushed). Updated 2026-09-29.

## What you can do now

GUI → Simple Mode → **Session foreman**, or `agent-os orchestrate foreman …`:

| Source | How | Cost |
|---|---|---|
| Claude | `foreman use claude [--model opus\|sonnet\|haiku]` | your subscription |
| ChatGPT | `foreman use chatgpt [--model …]` | your subscription |
| Local model | `foreman use local --base-url http://127.0.0.1:11434 [--model …]` (Ollama, LM Studio, llama.cpp, vLLM) | none |
| Hugging Face | `foreman deploy <hf link> --job-usd N` (rents the cheapest RunPod GPU that fits, within the job budget) | metered against the budget |

Every run you start while a foreman is set is planned by it. The foreman
chooses each task's capability class, and that class sets which model runs it.

- **Backup foreman**: if the foreman's provider hits its usage limit or trips
  the failure breaker, the next backup plans instead (default: the other
  subscription). If every foreman is limited, the run waits (PLANNING) until
  one resets, instead of failing.
- **Strategy by model**: `foreman strategy` lists every model's planning
  strength and what it should prioritize. Strength comes from measured foreman
  evals first, then benchmark evidence, then tier, then a size hint, so new
  models and benchmarks are picked up without code changes.
  - Strong foremen (Opus, gpt-6-astra) get a "precise specs, delegate to the
    cheapest tier" addendum.
  - Weak foremen (Luna, Haiku, small open models) get deterministic guards.
  - Playbooks are data: override them in `~/.agent-os/foreman-playbooks.json`.
- **Host model awareness**: the GUI shows which model you are using right now,
  read from the Claude Code session transcript and the Codex config (model
  fields only). It recommends spending a strong model on planning.
- **Plan fixes, applied to every foreman's plan without a model call**:
  - role normalization;
  - same-scope merge (cycle-safe): tasks that edit the same files become one
    task, which saves about 15k tokens of agent overhead per removed task;
  - for weak planners, a class guard that raises design/concurrency/security
    work to `reasoning` and lowers typo/docs work to `fast`.
- **Learned model availability**: when a model returns `invalid_model`
  (e.g. `gpt-6.1-sol` "not supported when using Codex with a ChatGPT
  account"), it stops being routed for 7 days, machine-wide.
- **GPU spend safety** (all verified live):
  - the job budget is enforced from RunPod's own rate;
  - the pod is torn down before 95% of the cap, when idle, or on Stop;
  - a crash-log reporter and crash-loop detection end a failing pod quickly;
  - orphan pods are recovered;
  - cost per unit is shown: busy %, $/request, $/M tokens, $ spent idle.

## Live measurements (7 dev cases; the guards were tuned on these)

| Foreman | Raw judgement / valid | With its strategy | Agent launches | Tokens in/out per plan | Median time |
|---|---|---|---|---|---|
| Claude Opus 5.5 (strong) | 85.7% / 100% | 100% / 100% | 25 → 20 | 9.2k / 2.2k | 21.5 s |
| ChatGPT gpt-6-astra (strong) | 71.4% / 100% | 85.7% / 100% | 24 → 20 | 17.2k / 0.9k | 29 s |
| Qwen2.5-14B on 1× RTX PRO 6000 (weak) | 28.6% / 71% | 100% / 100% | 16 → 18 | 1.7k / 0.7k | 18 s, $0.06 of GPU for all 7 |

### Held-out split (6 cases written before tuning, never tuned on)

| Foreman | Raw judgement | With its strategy | Valid plans (after strategy) | Median time | Tokens in |
|---|---|---|---|---|---|
| Claude Opus 5.5 | 83.3% | 83.3% | 100% | 18.8 s | 9.2k |
| ChatGPT gpt-6-astra | 83.3% | 83.3% | 100% | 23.5 s | 17.3k |
| Qwen2.5-14B on GPU | 50% | **83.3%** | 100% | 9.2 s | 1.7k |

The deterministic strategy generalizes. On unseen cases the cheap GPU model
plans as well as Opus and gpt-6-astra, using 1/5 to 1/10 of the input tokens.
The whole held-out run, including loading the pod, cost $0.17. Neither strong
foreman was hurt by the guard.

The one miss every foreman shares is splitting a tiny two-file change
(version bump + changelog) into two tasks. I have not added a rule for it:
a rule tuned on the held-out set would stop it from measuring overfitting. It
needs new held-out cases first.

RunPod spend so far: see `agent-os orchestrate budget show` (about $1.25 of $10
at the time of writing, across 4 deployments, including one crash-looping pod
that led to the crash reporter).

## Found and fixed during live testing

1. The registry mapped ChatGPT's reasoning tier to a model the account cannot
   use. Such failures are now learned machine-wide.
2. RunPod had no capacity for the cheapest GPU. Each request now lists every
   affordable type per (GPU count, tier) group. Types priced over 1.5× the
   group's cheapest are left out, after RunPod once picked a card at 2.4×.
3. vLLM crash-looped silently for 16 minutes. The wrapper now serves the
   redacted crash log, and uptime resets are detected.
4. Every foreman over-split same-file work, so the same-scope merge was added.
   A cycle bug in the merge showed up on real data and was fixed.
5. A 14B foreman invented roles, so role normalization was added.

## Not done yet / honest limits

- **GPU coding agent: working (live 2026-09-30).** `foreman deploy <hf link>
  --coding-agent` also registers `<foreman>-agent`, a Codex CLI worker that
  drives the rented model with repository tools through a Responses-API custom
  provider.
  - Live on Qwen2.5-14B: one orchestrated task (add a function in a throwaway
    repo), PASSED on the first attempt, 7 tool calls, 26 s, validator green.
  - Zero Claude/ChatGPT quota used; the whole deploy + test cost $0.096.
  - Earlier attempts hit the context window; fixed by the Codex tool trim below
    and a 64k (YaRN) context for agent pods.
  - Cost research still applies: per-token OpenRouter is usually cheaper than a
    rented pod. The GPU agent pays off when the pod is already busy, or for
    models no API serves.
- The watchdog runs inside the GUI / `foreman deploy` process. If this computer
  is off, a pod bills until the GUI next starts, and is then deleted if past
  its deadline.
- Adding RunPod credit from a saved card is a payment action I will not take;
  top up in the RunPod console if needed.

## Cost research: RunPod vs OpenRouter vs Vast.ai (2026-09-30)

Measured on this machine, not only list prices:

| Option | What it really cost | Per foreman plan (about 1.7k in / 0.5k out) |
|---|---|---|
| RunPod pod, Qwen2.5-14B | Listed from $0.16/h, but the cheap cards were rarely obtainable. Rented at $0.80, $1.58 and $1.64/h, plus about $0.15–0.30 of load time per deployment | about **$0.03** (7 plans for about $0.17–0.23) |
| Vast.ai | List prices similar to RunPod (RTX 3090 $0.12/h, A5000 $0.23/h, A100-40GB $0.40/h), with host reliability 0.93–0.999 | same economics as a pod |
| OpenRouter `qwen/qwen3-14b` | $0.12/M in, $0.24/M out, no load, no idle | about **$0.0003** |
| OpenRouter `qwen/qwen3-235b-a22b-2507` | $0.087/M in, $0.35/M out | about $0.0003, and a much stronger model |
| OpenRouter `openai/gpt-oss-120b` | $0.037/M in, $0.17/M out | about $0.0001 |

**Conclusion: for planning and small inline tasks, a per-token API is about 100×
cheaper than renting a GPU.**

- A $1.20/h pod only breaks even at roughly 3,000+ plans per hour, which means
  sustained batch saturation.
- OpenRouter aggregates Together, DeepInfra, Fireworks and others, so one
  integration covers them. OpenRouter is now a foreman source (`foreman use
  openrouter --model …`, GUI list with live prices).
- It needs an OpenRouter key: openrouter.ai → Keys, then store it with
  `orchestrate secrets setup`. Put a credit limit on the key; that limit is the
  hard spend cap.

Rent a GPU only when:
- a batch job keeps it saturated (throughput beats the per-token price only
  near full utilization);
- training or fine-tuning (LoRA);
- image or audio models no API serves;
- custom or abliterated weights no API hosts;
- you want no third-party inference API in the data path.

The existing quote engine (`orchestrate quote`) already compares API vs GPU
pod vs serverless for a described workload.

## Per-worker request size (measured 2026-09-30 with local fake endpoints; no quota used)

| Worker | Before | After |
|---|---|---|
| Codex CLI (lean config) | 455 KB, 27 tools: 443 KB of schemas (ChatGPT apps connectors such as Gmail, Drive, GitHub, Outlook, Notion and Spotify, plus multi-agent, goals, plugins and web search) | **31.7 KB, 4 tools (−93%)**: unused feature families are disabled (only names the installed CLI reports as enabled) and `web_search=disabled` is set |
| Claude Code worker | 21.9 KB, 6 tools (`--strict-mcp-config`, lean `--tools`: already optimal) | unchanged |
| Plain `claude -p` for comparison | 757 KB, 306 tools | — |

The Codex fix applies to every ChatGPT/Codex worker the orchestrator
launches. Cached tokens still count toward usage limits, so this directly
stretches your Codex quota. It is also what makes the GPU coding agent fit
in a vLLM context window: 455 KB is roughly 110k tokens, which a 32k/64k
pod rejected.

## OpenRouter foreman, live (2026-09-30): `qwen/qwen3-235b-a22b-2507`

| Split | Judgement raw → with strategy | Valid plans | Median time | Tokens in/out | Cost |
|---|---|---|---|---|---|
| dev (7) | 14% → 43% | 86% | 25.5 s | 1.4k / 1.2k | $0.0033 for all 13 plans |
| holdout (6) | 0% → 0% | 67% | 16.2 s | 1.4k / 0.9k | |

A large model is not automatically a good foreman. This one mostly chose
sensible classes per task, but it over-split heavily: 8–16 tasks where 1–5 fit.
It also proposed an unapproved deterministic command, and two calls failed with
an upstream provider error (HTTP 400 via OpenRouter).

Its strength rating moved automatically from "medium" (235B size hint) to
"weak" (measured judgement 7.7%, valid 77%), so it now gets the weak-planner
guards. I un-set it as the session foreman. Candidates to try next as a cheap
foreman, for about $0.005 each: `openai/gpt-oss-120b`,
`deepseek/deepseek-v4-flash`, `qwen/qwen3-32b`.

## OpenRouter foreman bake-off and a GEPA-style spike (2026-09-30)

All 13 cases per model, live on OpenRouter. "Strategy" means what the engine
actually runs: role normalization, the class-safe overlapping-scope merge, and
the class guard for weak planners.

| Foreman | Dev: raw → strategy | Held-out: raw → strategy | Valid (raw) | Median s | Out tokens |
|---|---|---|---|---|---|
| Claude Opus 5.5 (subscription) | 86% → 100% | 83% → 83% | 100% | 19–22 | 2.0–2.2k |
| ChatGPT gpt-6-astra (subscription) | 71% → 100% | 83% → 83% | 100% | 23–29 | 0.8–0.9k |
| Qwen2.5-14B on a rented GPU | 29% → 100% | 50% → 83% | 71–83% | 9–18 | 0.5–0.7k |
| `deepseek/deepseek-v4-flash` | 86% → 100% | 50% → 50% | 100% | 45 | 6.3k |
| `openai/gpt-oss-120b` | 57% → 86% | 33% → 50% | 85% | 37–56 | 1.5–2.1k |
| `qwen/qwen3-235b-a22b-2507` | 14% → 43% | 0% → 50% | 77% | 16–26 | 0.9–1.2k |

Takeaways:
- On held-out cases no cheap per-token model has yet matched the subscription
  foremen. The rented Qwen2.5-14B with its strategy has. Each strength rating
  moved from a size guess to its measured value automatically.
- A bug found by the bake-off and fixed: the overlapping-scope merge folded a
  `reasoning` design task into its `fast` implementation tasks. That moves
  cheap work onto the expensive model and dropped plans below their useful
  size. Reasoning/frontier tasks are now never merged with cheaper tasks.
  Re-scored on every saved live answer, no case is worse than its raw plan.
- GEPA-style spike (`foreman_optimize.py`: a reflector model rewrites a cheap
  foreman's instructions):
  - qwen3-235b dev improved from 85.7% to 100%, but held-out stayed at 50%.
  - It overfit the 7 dev cases, so the rewrite was not adopted. PA-gepa is
    now DEFER until there are at least 30 labelled dev cases.
  - About $0.02.
