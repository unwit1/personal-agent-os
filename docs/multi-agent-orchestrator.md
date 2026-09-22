# Multi-agent coding orchestrator

Status: implemented (P1.2A), 2026-09-22.

Submit one coding goal. Agent OS plans it, picks a provider, model and
reasoning effort for each part, runs Claude Code and Codex CLI workers in
isolated Git worktrees, validates each change, has a *different* agent review
it, routes findings back for repair, integrates only work that passed both
checks, and — with **Auto Continue** — keeps going until the task is complete,
a declared approval gate is reached, you pause it, or it is genuinely blocked.

The staged workflow runner (`docs/staged-workflows.md`) *prepares* model
stages and hands them to whoever is running. The orchestrator closes that gap
for local coding CLIs: it launches the workers itself.

## Quick start

```powershell
# 1. Tell Agent OS which coding CLIs this machine has (adds missing entries only)
agent-os orchestrate providers --suggest --write
agent-os orchestrate providers           # probe status + what the router would pick

# 2a. GUI
agent-os orchestrate gui                 # http://127.0.0.1:8765/ ; Ctrl+C stops driving

# 2b. Headless: Start Recommended + Auto Continue, driven in the foreground
agent-os orchestrate start-recommended --goal "Add retry to the mail sync" `
    --project personal-agent-os
```

With `--project`, the project's registered `validation_commands` become the
default validators. With a bare `--repo`, pass them yourself:
`--validator "python -m unittest discover -s tests"`. If no validator is
declared, the change is not integrated automatically. Instead, a
`policy_restricted_action` gate asks you whether to integrate it without test
evidence.

## Architecture

```
GUI (gui/)  ─┐
CLI          ├─> orchestrator.service ─> orchestrator.engine (scheduler, auto-continue, gates)
MCP tools   ─┘                              │
                     ┌──────────────┬───────┼──────────────┬──────────────┐
                  router         worktrees  validators    review        store
              (capability ->   (branch +   (deterministic (structured   (.agent-local,
               provider/model/  worktree    evidence)      findings)     no transcripts)
               effort)          per worker)
                     │
                 adapters/  ── claude_code.py, codex_cli.py, synthetic.py
```

| Component | Module | Responsibility |
|---|---|---|
| OrchestratedRun | `model.py` | run/node/policy vocabulary, states, scopes |
| Scheduler + AutoContinueController | `engine.py` | ticks, dispatch, retries, failover, gates, completion |
| ModelRouter / ProviderRegistry | `router.py` | capability + effort → provider/model/effort, overrides |
| ProviderAdapter | `adapters/` | the only place CLI syntax and vendor names live |
| WorktreeManager | `worktrees.py` | per-worker branch/worktree, checkpoints, merge, cleanup |
| ValidatorRunner | `validators.py` | declared validators + editable-scope check |
| ReviewCoordinator | `review.py` + `engine.py` | structured findings, repair, re-review |
| IntegrationManager | `engine.py` (`_integrate`, `_land`) | validated-only merges, conflict gates |
| EventStream | `store.py` events + `server.py` SSE | structured state changes for clients |

The GUI is a client. Every button maps to one engine call, and nothing in
`gui/` decides policy.

## What one tick does

```
reconcile -> honour stop/pause -> poll workers -> collect result
  -> checkpoint Git state -> validators -> review? -> repair? -> integrate
  -> completion check -> dispatch runnable nodes -> derive run state -> persist
```

`run_loop` repeats ticks. With `auto_continue`, it runs until the run reaches
`COMPLETE`, `PAUSED`, `APPROVAL_REQUIRED` or `BLOCKED`. Without it, the loop
stops at the next stage boundary: the tick in which a stage passes integrates
that stage and launches nothing new. This matches the staged workflow runner.

Run states: `CREATED PLANNING READY RUNNING VALIDATING REVIEWING INTEGRATING
APPROVAL_REQUIRED PAUSED BLOCKED FAILED COMPLETE`.
Node states: `PENDING RUNNABLE CLAIMED LAUNCHING RUNNING WAITING_FOR_RESULT
VALIDATING NEEDS_REPAIR WAITING_FOR_REVIEW APPROVAL_REQUIRED PASSED
FAILED_RETRYABLE FAILED_FINAL CANCELLED`.

## Planning

Plans are chosen in this order, cheapest first:

1. **Explicit tasks** (`--tasks tasks.json`) need no model call.
2. **`planning: single`** creates one implementer node for the whole goal.
3. **`planning: auto`** (Start Recommended) runs a read-only planner node at
   `balanced`/`medium`. Its structured output expands into the graph. A planner
   can never inject a shell command (the deterministic path is caller-only) and
   can never request `frontier`.

A task looks like this:

```json
{"id": "api", "goal": "Add the endpoint", "role": "implementer",
 "depends_on": ["schema"], "scope": ["src/api"],
 "capability_class": "balanced", "effort": "medium",
 "validators": [{"kind": "command", "command": "python -m unittest tests.test_api"}],
 "review_required": true,
 "approval_gate": {"kind": "destructive_action", "reason": "drops a column"}}
```

`execution_path: "deterministic"` together with `command` runs a local command
in the node's worktree with no model involved.

## Worktrees, scope and integration

- Every editing node gets a branch `agent-os/<run>/<node>` and a worktree
  under `.agent-local/orchestrator/worktrees/<run>/`. Two editors never share
  a writable tree. A repair node takes over its subject's worktree, with
  explicit ownership recorded.
- A worker's tree is branched from the **current integration head** when the
  worker launches, so a dependent task sees the work it depends on.
- Editable **scopes** that overlap are serialized, not raced. The second node
  waits until the first has been integrated, then branches from the result.
  Edits outside a node's declared scope fail validation.
- The orchestrator commits (checkpoints) whatever a worker leaves behind.
  Workers are told not to commit, push, merge or rebase.
- Integration merges a node into `agent-os/<run>/integration` only when:
  - its validators passed (never on the worker's say-so);
  - required independent review approved it, or you explicitly accepted the
    open findings;
  - at least one validator was actually declared, unless you approved
    integrating without one.
- A merge conflict aborts cleanly and opens a `semantic_merge_conflict` gate.
  Approving it re-runs the node on top of the current integration head. The
  conflicting branch is kept for inspection.
- Once every node is integrated, the **completion validators** run on the
  integration branch. If they fail, the orchestrator schedules a bounded
  `final-fix` node; if that fails too, the run is `BLOCKED`.
- By default the run ends `COMPLETE` with the integration branch ready to land
  (`git merge --ff-only agent-os/<run>/integration`). With `final_integration:
  merge_to_base`, a `consequential_repository_write` gate appears in the GUI
  as **Approve Merge**. It fast-forwards the base branch only if the base has
  not moved and its checkout is clean.
- Integrated workers' worktrees are removed and their merged branches deleted
  with `git branch -d`, which never deletes unmerged work. Failed workers'
  branches and worktrees are left in place for recovery.

## Cross-review

After an editing node passes validation, the orchestrator adds a reviewer node.
The reviewer prefers a **different provider** from the author: Claude reviews
Codex's work and Codex reviews Claude's. It runs read-only (Claude Code
`--permission-mode plan`, Codex `-s read-only`) in the author's worktree and
gets the diff in its prompt. It must return:

```json
{"status": "done", "verdict": "approved | changes_requested | blocked",
 "findings": [{"id": "1", "severity": "critical|high|medium|low|info",
   "path": "...", "summary": "...", "evidence": "...",
   "recommended_action": "...", "validator_needed": true}]}
```

Free text such as "looks good" is a malformed result, not an approval, and is
retried. An approval that lists a critical or high finding is treated as
`changes_requested`. Material findings (policy `material_severities`) create a
repair node in the author's worktree. The repairer marks each finding
`fixed`, or `rejected` with a reason. The change is then revalidated and
re-reviewed. After `max_review_rounds`, remaining material findings open an
`unresolved_review_findings` gate. **Review Again** requests another round for
a validated change that has not been integrated yet.

Set `require_distinct_review_provider: true` to forbid same-provider review. By
default, a machine with only one provider still gets a separate review
session, and the review record says `independent_provider: false`.

## Routing: provider, model, effort

Stages request a provider-neutral capability class and effort. The router
works as follows:

- It applies the run's `preference`: `economy` moves one rung down (never below
  `fast`), `quality` moves one rung up.
- It considers only providers that are enabled, pass their probe, are under
  `max_concurrency`, are allowed for the role, and are not excluded for this
  node after a provider failure.
- It picks the configured model for the class. If no provider covers that
  class, it uses the nearest *stronger* covered class, and only then a weaker
  one.
- It maps effort through the provider's `effort_map`.

It never spends a model call to decide which model to launch, and every
selection carries a one-line reason.

**Overrides** (`agent-os orchestrate override`, GUI override panel, or
Reassign) are stored in run state at run, role or node level; node overrides
beat role overrides, which beat run overrides. They never modify workflow
manifests or task files.

The registry is `~/.agent-os/providers.json` (override with
`AGENT_OS_PROVIDERS`), the same file the staged workflow runner reads, extended
with these fields:

```json
{
  "providers": [
    {
      "id": "claude-code", "enabled": true, "adapter": "claude_code", "executable": "claude",
      "models": {"fast": "haiku", "balanced": "sonnet", "reasoning": "opus", "frontier": "fable"},
      "effort_map": {"none": "low", "low": "low", "medium": "medium", "high": "high"},
      "max_concurrency": 2,
      "options": {"permission_mode": "acceptEdits", "read_only_permission_mode": "plan"}
    },
    {
      "id": "codex", "enabled": true, "adapter": "codex_cli", "executable": "codex",
      "models": {"fast": "<model>", "balanced": "<model>", "reasoning": "<model>", "frontier": "<model>"},
      "effort_map": {"none": "low", "low": "low", "medium": "medium", "high": "high"},
      "max_concurrency": 2,
      "options": {"sandbox": "workspace-write", "read_only_sandbox": "read-only"}
    }
  ]
}
```

Values that still start with `<` are treated as unconfigured placeholders.
Optional provider fields: `priority`, `roles`, `env_allowlist`,
`options.allowed_tools`, and `options.persist_sessions`.

## Adapters

Adapters implement `probe / resolve_invocation / start / poll / cancel /
collect` (`adapters/base.py`). The core passes a structured
`AgentLaunchRequest` and receives an `AgentResult` with outcome, failure kind,
summary, structured result, usage and duration.

| Adapter | Verified against | Invocation |
|---|---|---|
| `claude_code` | Claude Code 2.1.280 `--help` | `claude -p --output-format json --model M --effort E --permission-mode acceptEdits|plan --permission-prompts none --no-session-persistence < prompt.md` |
| `codex_cli` | codex-cli 0.155.1 `exec --help` | `codex exec -m M -c model_reasoning_effort="E" -s workspace-write|read-only -C WT --json -o last-message.md --ephemeral - < prompt.md` |
| `synthetic` | — | in-process scripted worker for tests and dry runs |

Optional flags are passed only when the probed `--help` output advertises
them. Workers receive an **allowlisted environment**: system basics plus the
adapter's own credential prefixes and anything in `env_allowlist`. The display
command never contains secrets.

Adding another CLI means one module in `adapters/` plus an `ADAPTERS` entry.
The scheduler does not change.

## Failures, retries, failover, restart

- A worker failure is classified as one of: `process_error`, `quota`,
  `unavailable`, `invalid_model`, `timeout`, `malformed`, `cancelled`,
  `interrupted`.
- **Provider failures** (`quota`, `unavailable`, `invalid_model`, or the same
  process error twice) exclude that provider **for that node**. The node keeps
  its worktree and partial work, which is committed as a checkpoint, and is
  re-routed to an allowed alternative. Retries are bounded by
  `max_stage_retries`.
- A **validator failure** escalates the node one capability rung, up to
  `max_escalations`, and then marks it `FAILED_FINAL`.
- A user **Stop** cancels running workers without consuming the retry budget.
  **Resume** re-dispatches them, and their partial work is still in their
  worktrees.
- **Restart reconciliation**: when a run is loaded by a process that did not
  start its workers, a worker that is no longer alive is marked
  `interrupted`, never complete. Its checkpoint and worktree are kept and it
  is retried. A worker whose PID is still alive is left alone and reported.
  Passed nodes are never rerun.
- **Single driver**: only one live process may drive a run
  (`runs/<id>/driver.json`). Status reports who is driving, if anyone.

Auto Continue drives the run only while an orchestrator process is running it:
`orchestrate run`, `start-recommended`, `orchestrate.advance`, or the GUI
server. Nothing continues in the background after that process exits. The next
driver resumes from persisted state.

## Approval gates

| Gate | Opened when | Approve | Reject |
|---|---|---|---|
| `destructive_action`, `credential_or_secret_entry`, `consequential_external_write`, `policy_restricted_action` (declared) | a node declaring the gate becomes runnable | the node runs | node `CANCELLED`, run `BLOCKED` |
| `policy_restricted_action` (no validator) | a change with no declared validator is about to be integrated | integrate without test evidence | node fails, run `BLOCKED` |
| `semantic_merge_conflict` | merging into the integration branch conflicts | redo the node on the current integration head | run `BLOCKED` |
| `unresolved_review_findings` | material findings remain after `max_review_rounds` | accept the findings (recorded) and integrate | run `BLOCKED` |
| `agent_needs_decision` | a worker reports `needs_decision` with a question | re-run, with your note included in the prompt | node `CANCELLED` |
| `budget_exhausted` | `max_launches` worker launches have been used | raise the budget | run stays stopped |
| `consequential_repository_write` | `final_integration: merge_to_base` and everything passed | fast-forward the base branch (Approve Merge) | keep the integration branch only |

A gate is never converted into a failure and never skipped. While any gate is
open, nothing new is dispatched.

## Run policy

`agent-os orchestrate create --set key=value` or `--policy policy.json`:

```json
{
  "auto_continue": true, "max_parallel_editors": 2, "require_isolated_worktrees": true,
  "require_independent_review_for_model_edits": true, "require_distinct_review_provider": false,
  "validation_required_before_integration": true, "provider_failover": true,
  "max_stage_retries": 2, "max_escalations": 2, "max_review_rounds": 2, "max_final_repairs": 1,
  "material_severities": ["critical", "high", "medium"], "preference": "balanced",
  "planning": "auto", "max_planned_tasks": 8, "final_integration": "branch", "max_launches": 40,
  "poll_interval_seconds": 2.0, "worker_timeout_seconds": 3600,
  "default_validators": [], "completion_validators": [],
  "announce_claims": true, "telemetry": true, "cleanup_worktrees": true
}
```

Unknown keys are rejected. `require_isolated_worktrees` cannot be turned off.

## Headless commands

```powershell
agent-os orchestrate create --goal "..." --repo . --tasks tasks.json --start --auto-continue
agent-os orchestrate run <run>                 # exit 0 COMPLETE, 3 PAUSED, 4 gate, 5 BLOCKED
agent-os orchestrate status|result|events|list <run>
agent-os orchestrate pause|resume|stop <run>
agent-os orchestrate approve|reject <run> <gate> --note "..."
agent-os orchestrate retry|review-again <run> <node>
agent-os orchestrate reassign <run> <node> --provider codex --effort high
agent-os orchestrate override <run> --role reviewer --provider claude-code --model opus
```

MCP tools (same engine): `orchestrate.providers`, `.create`, `.status`,
`.list`, `.advance` (drives for a bounded time), `.control`, `.decide`,
`.retry`, `.reassign`, `.review_again`, `.override`, `.result`.

## GUI

`agent-os orchestrate gui` serves `gui/` and a JSON API on loopback only. Each
server process has a session token: the page embeds it, and every API call must
send it in a header. Requests with an unexpected Host header are refused, which
blocks DNS rebinding. Together these stop other web pages in the same browser
from driving a run.

The GUI provides:
- a new-task form with **Start Recommended** and **Auto Continue**;
- run state, progress, and who is driving the run;
- Drive, Step, Pause, Resume and Stop;
- a provider/model/effort override;
- agent cards showing provider, model, effort, capability, branch, scope,
  attempts, route reason, validator evidence and reviews, with Retry,
  Reassign and Review Again;
- approval gates with Approve, Reject and Approve Merge;
- cross-review findings, validation and integration results, and a live event
  log over server-sent events.

**Deviation from the bootstrap suggestion (Tauri + React).** This machine has
no Rust toolchain, and the repository has no frontend build. The first GUI is
therefore dependency-free HTML/JS served by the Python backend. The API is the
contract, so a Tauri shell can wrap the same URL later without touching
orchestration code.

## Privacy

- Run state lives in `.agent-local/orchestrator/runs/<run>/state.json`, which
  is gitignored, because it contains machine paths and PIDs.
- `RunStore` refuses to write inside canonical repository paths and refuses
  any `transcript`, `messages`, `history` or `conversation` key at any depth.
  It also redacts obvious secrets in every string it stores.
- Worker prompts and raw CLI output stay in local `workers/<node>-<attempt>/`
  files. The run record holds only a short, redacted summary.
- Telemetry goes through the existing metadata-only `TelemetryEvent`:
  provider, model, capability, execution path, tokens, duration, retries,
  escalations, validator outcome and whether an override was used.
- Editing workers are announced through `work-claim`, scoped to their editable
  paths, and the claim is released on integration. Other agents therefore see
  orchestrated workers exactly as they see each other.

## Known limits

- Auto Continue needs a live driver process (see above). There is no daemon
  or OS service.
- A worker whose process outlives a crashed orchestrator cannot be reattached
  to collect its exit status. After it exits it is treated as interrupted and
  retried, with its partial work kept.
- Routing uses configuration plus per-run failure evidence. It does not yet
  learn from historical telemetry across runs.
- Token usage is reported only when a CLI reports it; cost is not computed.
- Planner quality depends on the model; the plan is validated structurally,
  not semantically.
- Run records are local. Durable outcomes reach Git through handoffs, not by
  committing run state.
