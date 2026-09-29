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

The held-out split (`--split holdout`, 6 cases never tuned on) is the check
against overfitting. Its results are below once they are in.

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

- A rented GPU model can plan and serve inline tasks, but it cannot edit
  repositories: it has no tool harness. Driving an open model as a coding agent
  (e.g. an OpenAI-compatible coding CLI pointed at the pod) is the next step
  toward using the whole GPU for development.
- The watchdog runs inside the GUI / `foreman deploy` process. If this computer
  is off, a pod bills until the GUI next starts, and is then deleted if past
  its deadline.
- Adding RunPod credit from a saved card is a payment action I will not take;
  top up in the RunPod console if needed.
