# Orchestrator Simple Mode, Continue Roadmap, and efficiency telemetry

Status: implemented 2026-09-22 (P1.2C); per-call overhead reduction and cross-run usage report 2026-09-23 (P1.2D). Part 1 is for everyone. Part 2 is for
developers.

---

## Part 1 — Using it

### Start

```powershell
agent-os orchestrate gui                          # opens http://127.0.0.1:8765/
agent-os orchestrate gui --project personal-agent-os
agent-os orchestrate gui --repo C:\path\to\a\repo  # a folder that is not registered
```

The window stays useful only while this command is running. Closing it stops
the agents from being supervised; nothing is lost, and pressing **Resume** or
**Continue Roadmap** later picks up where it stopped.

### The home screen

- **Project**, **Roadmap** (for example `5 / 22 stages complete`, with one
  small square per stage: green = done, amber = partly done, striped = on
  hold) and **Next task** in plain words.
- **CONTINUE ROADMAP** — the main button. It finds the next unfinished
  roadmap task and works on it automatically.
- **Keep going until the roadmap is done** — tick this to let it move on to
  the next task by itself after each one is finished and saved.
- **Start Specific Task** — type something you want done that is not on the
  roadmap.
- **View Progress**, **Pause Work**, **Stop Work**, **Settings**.

### "Tell me what to press"

The button at the top right looks at what is happening *right now* and gives
one recommendation, and highlights the button to press. Examples:

- "Press Continue Roadmap. Everything is ready."
- "Nothing needs your attention. Codex is still working."
- "Press Approve Commit. The work is finished and ready to save."
- "Press Resume. The previous run was interrupted."

### What happens after you press Continue Roadmap

The button changes to **Starting…** immediately, and a list of steps appears:

```
✓ Reading repository
✓ Checking roadmap
✓ Checking unfinished work
✓ Loading previous handoff
✓ Choosing the next task and agent
✓ Starting work
✓ Plan
● Implement        1 of 3
○ Test
○ Review
○ Fix findings
○ Commit
```

✓ done · ● happening now · ○ not yet · ! waiting for you · ✗ failed. There is
no made-up percentage: each tick is a real step that finished.

If something from last time was left unfinished, Continue Roadmap **resumes
it** instead of starting the same work again.

The **Agents** table shows who is doing what (for example `Codex — Working`,
`Claude — Reviewing`, `Agent OS — Monitoring`, `Git — Clean`). The
**Activity** list tells the story in plain sentences, newest first.

### When it needs you

A yellow card explains what happened, whether anything changed, what is
recommended, and what each choice does. **Explain This To Me** gives a longer
explanation (built in; it does not use an AI model). The raw technical detail
is under **Advanced Details**.

The most common card: **"The work is finished and ready to save."** The work
passed its tests and an independent review and is waiting on its own branch.
**Approve Commit** adds it to your main branch. Nothing is added to your main
branch without this approval.

### Auto Continue Until Done

With the box ticked, after each task is approved and saved, the next roadmap
task starts by itself. It stops when:

- you press Pause or Stop;
- something needs your approval (including saving finished work);
- a problem cannot be fixed automatically;
- no eligible roadmap work is left;
- a roadmap stage was worked on twice without being marked done (so it cannot
  loop forever), or ten runs were started in one go.

If one AI provider runs out of usage, that part moves to the other provider.

### "How much work did the models do?"

Open this section under a run. Every number is labelled:

- **measured / exact** — counted, or reported by the provider;
- **estimated** — calculated by Agent OS (explained below);
- **not available** — the provider did not report it. This is *not* zero.

The most important lines:

- **Model calls** and **Highest-cost model calls**;
- **Input / output tokens (provider-reported)**, including tokens served from
  the provider's cache;
- **Tokens agents spent beyond the prompt** — the difference between what the
  provider says it read and the size of the instructions Agent OS wrote. This
  is the agent tool's own built-in instructions plus the files it chose to
  open. In live runs this is usually most of the usage;
- **Context reduction** — how much smaller the project information in the
  prompt was than the full set of project documents;
- **Model calls avoided** and **Estimated tokens avoided** — only filled in
  where there is a real measurement to compare with; otherwise it says "not
  available".

### "Model usage across all runs"

A section on the home screen that adds up every run on this computer: model
calls, tokens the providers reported, calls that reported nothing, how much of
what the models read was the agent tools' own overhead, and calls avoided.

### Advanced Mode

The **Simple / Advanced** switch at the top right. Advanced Mode is the full
technical view: every agent, branch, model, effort level, override, review
finding and raw log line.

### Troubleshooting

| You see | Do this |
|---|---|
| "INTERRUPTED — not running" | Press **Resume** (or Continue Roadmap). |
| "An agent may still be working, but nothing is collecting its result" | Press **Resume**; the result is picked up when it finishes. |
| "has run out of usage for now" | Wait, or press **Try Again** later; the other provider is used if available. |
| "No roadmap found" | Add `ROADMAP.md` with `### P0.1 — Title` headings and `Status:` lines. |
| "Not saved to main: … checked out with uncommitted changes" | Commit or stash your own changes, then approve again. |
| Numbers say "not available" | That provider did not report usage for that call. |

---

## Part 2 — Developer details

### Components

| Concern | Module |
|---|---|
| Roadmap scanning, Continue Roadmap preparation, campaigns | `src/agent_os/orchestrator/roadmap.py` |
| Plain-English view model, problem cards, advice | `src/agent_os/orchestrator/simple.py` |
| Per-run telemetry ledger + transcript + summary | `src/agent_os/orchestrator/ledger.py` |
| Provider usage normalization | `src/agent_os/orchestrator/usage.py` |
| Benchmark | `src/agent_os/orchestrator/benchmark.py` |
| API (`/api/home`, `/api/roadmap/continue`, `/api/prep/<id>`, `/api/runs/<id>/simple`, `/api/runs/<id>/efficiency`, `/api/runs/<id>/fresh`) | `src/agent_os/orchestrator/server.py` |
| GUI | `gui/simple.js` (DOM), `gui/simple-core.js` (pure, Node-tested), `gui/app.js` (Advanced) |

There is still one orchestration engine; Simple Mode, the roadmap campaign and
the benchmark all drive `engine.Orchestrator`.

### Immediate feedback

`POST /api/roadmap/continue` returns a preparation id at once; the work runs
on a thread and reports each step through `GET /api/prep/<id>`. The GUI also
updates the button, the run panel and the step list synchronously in the
click handler before any request (measured 6–7 ms click→visible change in
headless Chrome), and any request slower than 0.7 s shows "Still working:
<what> (Ns)".

### Continue Roadmap algorithm

1. resolve the repository (`--project` or `--repo`), branch, dirty state;
2. parse the master roadmap: `###` headings (and `## P<n>` sections without
   sub-stages) → stages; status from the section's `Status:` line
   (`complete`/`implemented` → complete; `foundation`/`partial`/`steps` →
   partial; `deferred` → on hold), else `Current bounded …` → in progress,
   else not started;
3. unfinished orchestrated runs for the project → resume the newest (or
   report that it needs you); unmerged branches named after a stage
   (`p0.4-recovery`) → skip that stage (`loop_guard: duplicate_roadmap_work`);
4. latest handoff's `remaining` items;
5. the earliest eligible stage; goal = instructions + that stage's section
   only (≤ 2,600 chars), told not to re-read the roadmap and to update the
   stage's status line in its last task;
6. `create_run(planning=auto, final_integration=merge_to_base, origin={kind:
   roadmap, stage_id…})`. Unregistered repos get `python -m unittest discover
   -s tests` when `tests/test_*.py` exists; otherwise integration asks.

Campaigns (`.agent-local/orchestrator/campaigns/<project>.json`) repeat this
after each run is COMPLETE and landed, with the stop conditions listed in Part
1 (`MAX_RUNS_PER_STAGE = 2`, `max_runs = 10`).

CLI: `agent-os orchestrate roadmap`, `agent-os orchestrate continue-roadmap
[--until-done] [--fresh] [--no-drive]`.

### Telemetry

Files (gitignored runtime state):

```
.agent-local/orchestrator/runs/<run>/telemetry.jsonl   structured events
.agent-local/orchestrator/runs/<run>/transcript.log    the same, in plain English
.agent-local/orchestrator/runs/<run>/events.jsonl      pre-existing engine event log
.agent-local/orchestrator/benchmarks/<utc>/results.json + report.md
```

Each record: `{schema, at, seq, run_id, type, node, data}`. Types:
`run_started roadmap_scanned task_selected handoff_loaded context_selected
cache_hit skill_selected local_execution routing_decision model_selected
model_started model_completed model_failed model_escalated retry fallback
review_started review_completed tests_started tests_completed
checkpoint_created commit_created work_avoided loop_guard approval_required
run_paused run_resumed run_completed run_failed note`.

`agent-os orchestrate report <run>` prints the summary computed from the file
(plus `reconciliation` against the run record's own usage totals);
`--transcript` prints the readable log.

Telemetry fails open: write errors are counted and shown as
`telemetry_warning` in the run status; the run continues. Malformed lines are
skipped and counted (`malformed_lines`). Prompts, diffs, stdout and
transcripts are never written; strings are redacted.

### How token counts are obtained

| Provider | Source | Accuracy |
|---|---|---|
| Claude Code | `claude -p --output-format json` result `usage` | exact |
| Codex CLI | sum of `turn.completed.usage` in `exec --json` | exact (if the CLI emits it) |
| Synthetic (tests/benchmark) | scripted | labelled `synthetic`, never counted as measured |
| any, when missing | — | `unavailable`; counts are null, never 0 |

Normalized fields: `input_tokens` = **all** input the model processed
(Claude: `input_tokens + cache_read_input_tokens +
cache_creation_input_tokens`; Codex: `input_tokens`, which already includes
`cached_input_tokens`), `uncached_input_tokens`, `cache_read_tokens`,
`cache_write_tokens`, `output_tokens`, `reasoning_tokens`, `cost_usd` (Claude
only; list price, not subscription billing), `turns`, `tool_calls` (Codex).

Before this change the Claude adapter recorded only the *uncached*
`input_tokens`: a real planner call that processed 1,725,628 input tokens was
recorded as 38.

### Which numbers are estimates

- prompt tokens: exact characters written by Agent OS ÷ 4;
- context sizes: characters measured, tokens ÷ 4;
- "tokens agents spent beyond the prompt": exact provider input − prompt
  estimate;
- tokens avoided: only when a measured cost exists for the same kind of call
  in the same run (the average exact tokens of that role's calls, or the
  measured cost of the reused planner call); otherwise null;
- the benchmark baseline (below).

### How context reduction is calculated

`reduction = (candidate − selected) / candidate`, per event, summed per run.

- Worker prompts: candidate = every registered context file and skill of the
  project (`compile_context`'s `naive_all_registered_context_*`); selected =
  the compact slice placed in the prompt.
- Continue Roadmap: candidate = the master roadmap plus the detailed roadmaps
  in the same folder; selected = the quoted stage section (instructions are
  not counted as roadmap content).

It measures what Agent OS *puts in the prompt*. It says nothing about files an
agent CLI then opens by itself, which is why the "beyond the prompt" line
exists.

### Avoided work (`work_avoided`)

| category | when |
|---|---|
| `nothing_to_do` | no eligible stage, so no planner is started |
| `resume` | an unfinished run is continued instead of re-planned |
| `no_change` | a worker reported `already_done` and changed nothing, so no review is requested |
| `validation_cache` | identical code (Git tree) + identical validators already tested in this run: no model call, saves test time |
| `deterministic` | a planned deterministic command replaced a model worker |

### Loop guards (`loop_guard`)

`unchanged_code_retest` (no new code since a failed test run: tests not
re-run), `no_change_reported_done` (a worker said "done" but changed no
files: treated as a failed attempt and escalated, never integrated; seen live
with gpt-6-luna at low effort in 2 of 9 runs), `escalation_limit`, `retry_limit`, `review_rounds` (reviewer/repairer
ping-pong), `launch_budget`, `duplicate_roadmap_work`, `stage_repeat`,
`campaign_run_limit`.

### Model routing and escalation

Routing is the P1.2B router (cheapest provider for the requested capability
class, then least loaded). Each launch now records a `routing_decision` with
the tier (`cheap/fast`, `stronger`, `high-reasoning`, `highest-capability`),
the requested class/effort, the chosen provider/model/effort and one sentence
of why (planned class, escalation after failed validation, reviewer
minimum, override). Escalation order is unchanged and validator-driven:
deterministic step → (skill: not yet executable, see limits) → cached result →
fast → balanced → reasoning → frontier, raising effort before class.

### Benchmark

```powershell
agent-os orchestrate benchmark                      # offline, ~10 s, free
agent-os orchestrate benchmark --scenario roadmap_continuation
agent-os orchestrate benchmark --live               # small_code_change with real providers
```

Offline scenarios run the real engine, worktrees, validators, review and
integration on a throwaway fixture repo with scripted workers. They measure
calls, tiers, local operations, cache hits, escalations, prompt size, context
selection and runtime. Workers report **no** tokens, so offline token usage is
"unavailable". The baseline is a **modeled estimate**: every call (including
avoided ones) on the highest tier with the whole tracked project text in the
prompt, and no reuse of test results. Relative cost units use the registry's
configured `costs` weights, which are not prices.

### Per-call overhead (P1.2D)

Measured finding: the prompt Agent OS writes is ~1% of what the agent CLIs
read. The rest is each CLI's fixed per-call context (system prompt, tool
definitions, skill/plugin listings) plus its own exploration. The adapters
now trim the fixed part, using only flags the installed CLI advertises:

| Provider | Default now | Registry option to change it |
|---|---|---|
| Claude Code | `--tools Bash,Read,Edit,Write,Glob,Grep` (read-only workers: `Bash,Read,Glob,Grep`), `--disable-slash-commands` | `options.lean_tools` (false, or a tool list), `options.disable_skills` |
| Claude Code | not used: `--exclude-dynamic-system-prompt-sections` (no measured cache benefit), `--setting-sources` (~2%, but drops user permission rules), `--bare` (ignores OAuth logins) | `options.shared_prompt_cache`, `options.setting_sources` |
| Codex | `--ignore-user-config`, carrying over `windows.sandbox` from your config with `-c` (without it every command is "blocked by policy") | `options.use_user_config: true`, `options.carry_config_keys`, `options.disable_features` |

Ignoring `~/.codex/config.toml` also drops interactive-only settings such as
plugins, MCP servers, notify hooks and `service_tier = "priority"`: background
workers run on the standard tier.

**Measurement 1 — fixed cost per call** (`agent-os orchestrate overhead`:
trivial prompt, no tool use, two different worktrees, exact provider usage,
2026-09-23, Claude Code 2.1.280 / haiku, codex-cli 0.155.1 / gpt-6-luna):

| Variant | Input tokens per call |
|---|---|
| Claude, previous flags | 25,177 |
| Claude, lean tool set | 14,331 (−43%) |
| Claude, skills disabled only | 22,565 (−10%) |
| Claude, dynamic sections excluded | 25,032 (no cache gain in the 2nd worktree) |
| Claude, project settings only | 24,616 (−2%) |
| Codex, with user config | 19,007 (15,167–19,007 uncached) |
| Codex, `--ignore-user-config` | 14,022 (3,014 uncached) |

**Measurement 2 — real task, A/B** (`benchmark --live --scenario
small_code_change`, 3 runs each; every run verified that `farewell()` exists
on the integration branch):

| | Lean (new defaults) | Previous settings |
|---|---|---|
| Task input tokens | 85,940 · 147,768* · 100,513 (median 100,513) | 328,175* · 161,847 · 142,928 (median 161,847) |
| Claude sonnet review, per call | 42,114 · 41,756 · 41,679 | 84,345 · 84,995 · 172,442 (multi-turn) |
| Codex luna implementer, per call | 43,826 – 59,246 (mean 52,168) | 57,933 – 77,987 (mean 72,792) |
| Claude list-price cost per review | $0.053 – $0.060 | $0.097 – $0.130 |

\* one extra implementer attempt after `no_change_reported_done`.

Three runs per arm is a small sample and agent behaviour varies; the per-call
fixed-cost numbers (measurement 1) are deterministic, the task totals are not.

### Cross-run usage report (P1.1)

```powershell
agent-os orchestrate usage-report [--since 2026-09-01T00:00:00] [--include-benchmarks]
```

Reads every run's `telemetry.jsonl` and reports provider-reported tokens by
role, tier, provider/model and origin (roadmap vs task), expensive-tier calls
by role, retries/escalations/fallbacks/loop guards, calls avoided by
category, prompt-vs-provider input (overhead share), and coverage (calls with
exact tokens, calls without a report, synthetic calls excluded). Written to
`.agent-local/orchestrator/reports/usage-<utc>.json`; the GUI shows the same
totals under **Model usage across all runs** (`GET /api/usage`).

### Tests

| Suite | Kind |
|---|---|
| `tests/test_orchestrator_telemetry.py` | unit (usage, ledger, aggregation) + integration (engine) |
| `tests/test_orchestrator_roadmap.py` | roadmap unit, Continue Roadmap / campaign integration, Simple Mode view model, HTTP API, Node GUI tests |
| `tests/test_orchestrator_benchmark.py` | benchmark regression |
| `tests/test_orchestrator_overhead.py` | adapter overhead flags, config carry-over, usage report |
| `agent-os orchestrate overhead` | provider measurement (real calls; spends usage) |
| `tests/gui/simple_core.test.js` | GUI state (`node --test tests/gui/simple_core.test.js`) |
| `agent-os orchestrate benchmark --live` | provider smoke test (opt-in; uses real usage) |

### Known limits

- Stage status is read from roadmap prose. A stage whose `Status:` line is
  not updated is picked again (bounded by `stage_repeat`).
- Skills are instruction-only `SKILL.md` files with no deterministic runner,
  so `skill_reuse` is always 0.
- What an agent CLI reads on its own is not observable per file; only its
  total input tokens are.
- Claude reports a list-price `cost_usd`; Codex reports no cost.
- Campaign and GUI drivers live in the GUI process (or the foreground CLI);
  they do not survive a reboot.
- `seq` ordering uses wall-clock nanoseconds per process.
