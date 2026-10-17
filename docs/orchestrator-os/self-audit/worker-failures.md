# Worker failures and fixes (2026-10-17)

Why Sonnet workers failed or wasted turns in real runs, what was changed
deterministically, and what each change measured. All numbers are from real
runs or real-call replays on this machine; "n" is small throughout, so read
them as direction plus size, not as precise rates.

## Data
- 48 real worker calls: hr-cc-run4, mi-rights-gate, ab-maps-on/off and the
  prior-art sweep (`workers/*/stdout.log` and `state.json`), $21.45 in all.
- Sonnet editing calls: median 19 turns and 231k input tokens, about 10.7k
  per turn. Each turn re-reads the conversation, so turns drive cost.

## What went wrong
| Problem | Measured | Fix |
|---|---|---|
| Permission denials | 36 of 48 calls (28 of 28 Sonnet edit calls), 107 denials: 26 the task's own test run, 7 the scratch mkdir the rules ask for, the rest chained commands and heredocs | Editing workers get their validator commands and read-only commands pre-approved (`engine._worker_allowed_tools`, policy `worker_self_check`); rule: one command per call from the worktree root |
| Finished work parked as a host action | 13 of 48 calls ended `blocked_on_host`, almost all "pytest was denied". The engine deferred them: nothing merged, dependents waited (a run stalled two hours) | `blocked_on_host` with changed files is validated like `done`; only a step that changed nothing is deferred |
| Retry without the error | Retry prompts named failing tests only; 43% of hr-cc-run4 cost was frontier retries after validator failures | Validator keeps an excerpt (failing ids plus assertion/exception lines) and the retry prompt quotes it, noting when the failure did not change |
| Reviewer flip-flop | One file alternated between two exact versions over five reviews and three repairs, then a person was asked | A repair that restores an already-reviewed version stops the cheap loop (stronger reviewer, then a person); reviewers may not demand removing a change the assignment asks for |
| Refusals invisible | `stop_reason`/`safety_stops` were dropped; refusals looked like bad answers and were retried on the same model; `refusals.jsonl` was empty | Refusals are failure kind `refused`, recorded for `orchestrate refusals`, and the node fails over to another model class |
| Lost retry | A retry issued while another driver was mid-tick was saved over | Retries are recorded in run control and re-applied by any driver |

## Measurements of the fixes
- **Retry excerpt, real replay** of the two hr-cc-run4 `computer-tools`
  failures on Sonnet, 8 runs per arm: names only fixed 1/8 ($1.41 total,
  18.9 turns); with the excerpt 7/8 ($0.60, 9.0 turns). The original run
  escalated to frontier for $3.83 and still failed. Synthetic one-file bugs
  on Haiku: 12/12 both ways (easy bugs do not need it).
- **Self-check, worker replay** of the four ab-maps prompts, 2 runs each:
  denials 13 -> 1; statuses 2 `blocked_on_host` + 1 wrong `already_done` ->
  8/8 `done`; every worker ran its validator once; cost equal ($0.61 each
  arm); all 16 passed validation.
- **Self-check, end to end** (same four tasks through the orchestrator, one
  run per arm): on 15 calls $0.78; off 17 calls $1.47 including an extra
  completion fix after integrated code failed the full suite. The on arm's
  flip-flopping task (before the oscillation guard) ended at a gate.
- **Big tasks replayed** from their original base commits with the current
  worker setup, Sonnet: proactive-watcher passed first try (originally two
  attempts and a validator failure), no-self-approval passed ($0.43; the
  original ran on Opus for $1.39), computer-tools passed ($0.69; the
  original spent $5.44 on Opus then frontier and failed both times).

## Not changed, and why
- Material review findings were mostly real design problems (wrong home
  directory, unbounded reads, a fix for a bug that did not exist); no
  deterministic check replaces them.
- Machine-wide routing from refusal history: refusals depend on task
  content, and the task family for workers is coarse, so a refusal only
  moves that node to another model.
