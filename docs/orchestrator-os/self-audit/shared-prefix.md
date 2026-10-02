# Shared run-level prompt prefix (IMP-0018 Phase 1) — design

Status: design for implementation. Tracked improvement: **IMP-0018**, Phase 1.
Evidence that motivates it: EVR-0018 (the context-economy baseline from
[context-economy.md](context-economy.md)). Duplicated fixed per-worker overhead
is 253.4M of 255.8M worker input tokens (share 0.9905), and the median
cache-read share is 0.84. Companion audit: [context-anatomy.md](context-anatomy.md)
(`context_anatomy.MARKERS` names the prompt sections used below).

Today `prompts.build_measured` (`src/agent_os/orchestrator/prompts.py`) puts
per-node text near the top of every prompt. The role line comes first, then
`cwd`, then `Your assignment`. So two workers of the same run share only a few
dozen leading characters, and the rest of the run-level text (goal, rules,
project context) cannot be served from a provider prefix cache. Phase 1
reorders, and does not remove, that text. Every block that is identical for a
role family of a run moves into a byte-stable **prefix**. Per-node text follows
it in a **suffix**.

## 0. API

```python
FAMILIES = {"implementer": "worker", "test_author": "worker", "repairer": "worker",
            "reviewer": "reviewer", "planner": "planner"}
SHARED_PREFIX_END = "--- End of shared run instructions; your role and assignment follow. ---"
SHARED_CONTEXT_BUDGET = {"worker": 1200, "reviewer": 1200, "planner": 1600}

def family(role: str) -> str | None                     # FAMILIES.get(role)
def shared_prefix(run: dict, family: str) -> str        # pure function of the run record
def build_measured(run, node, *, diff=None, findings=None, repo_map=None, cwd=None,
                   prefix: str | None = None) -> tuple[str, dict | None]
```

- `prefix=None` is the current code path. Its output must stay **byte-identical
  to today**. The rule texts move into module constants `WORKER_RULES` and
  `REVIEWER_RULES` (tuples of lines), and both paths read the same tuples, so
  parity holds by construction.
- With `prefix` given, `build_measured` returns `prefix + "\n".join(suffix_lines)`.
  So `prompt.startswith(prefix)` always holds. It does not emit the blocks that
  the prefix already carries.
- Engine call site (`engine.py`, the `prompts.build_measured(...)` call in the
  launch path):
  `prefix = prompts.shared_prefix(record, fam) if policy.get("shared_prefix") and (fam := prompts.family(node["role"])) else None`.
  A role with no family gets `prefix=None`. Text that the engine appends after
  `build_measured` (prior attempts, run-history note, foreman addendum, inline
  note) already sits at the end, so it stays in the suffix with no change.
- Policy: add `"shared_prefix": False` to `model.DEFAULT_POLICY` and to the
  boolean list in `model._check_policy`. `model.py` is not a protected path.

## 1. Prefix: ordered run-level blocks

`shared_prefix(run, family)` emits these blocks, in this order. Blocks are
joined with `"\n"`, and a blank line ends each block:

| # | Block | Content | Present when |
|---|---|---|---|
| P1 | header | `` Agent OS orchestrated run `<run_id>`: shared instructions for every agent in this run. Your own role and assignment follow them. `` | always |
| P2 | goal | `Overall goal: <run['goal']>` (the same line as today) | always |
| P3 | project context | `Project context:` + packet text, built **once** per run from `load_state(project)` directly (no task, no `compile_context`, no `_fit`), cut to `SHARED_CONTEXT_BUDGET[family] * 4` characters (§1.7) | `run['project']` set and packet non-empty |
| P4 | family rules | worker: `Rules:` + every line of `WORKER_RULES`; reviewer: every line of `REVIEWER_RULES`; planner: nothing | family is worker or reviewer |
| P5 | operator messages | the current heading and the last 5 non-empty messages, `[:600]` each, in record order | any message exists |
| P6 | separator | `SHARED_PREFIX_END` | always |

The prefix string is `"\n".join(lines)`. It ends with `SHARED_PREFIX_END + "\n\n"`.

Decisions:

1. **One prefix per role family** (worker = implementer, test_author, repairer;
   reviewer; planner). Each family's prefix is byte-identical for every node of
   that family in the run. Implementers, test authors and repairers today get
   the same `Rules:` block, so they share one family.
2. **Order: cross-family blocks first, family blocks next, volatile blocks
   last.** P1 to P3 are identical across all three families, so a provider with
   token-granular prefix caching also shares them across families. P4 is
   per-family. P5 can change mid-run when the operator posts a message. Because
   it comes last, a change invalidates only P5 and P6, and every later worker of
   the family shares the new prefix again. This differs from the flag-off
   order (rules before context), which is allowed (§3).
3. **P1 is role-neutral.** It contains no role and no family label, so it stays
   cross-family. The role line `You are the <role> ...` is per-node and goes
   in the suffix.
4. **`WORKER_RULES`** contains every line of today's `Rules:` list except the
   per-node ones. These are kept: `- Work only inside this worktree...`,
   `- Do not commit, push...`, the 4-line nested-orchestrator rule,
   `- Do not print, store, or request credentials...`, the 3-line
   command-completion rule, the 2-line `Everything you need is in this prompt...`
   rule, `- If a decision would materially change...`, and
   `- If the assignment is already fully done...`. They are excluded (and stay in
   the suffix): `- Edit only paths inside your scope: ...`,
   `- Your work will be validated with:`, and its command lines.
5. **`REVIEWER_RULES`** contains the 10 static lines from
   `You are an independent reviewer; ...` through
   `Report evidenced problems only, ...`. They have no per-node values.
6. **Planner rules stay in the planner suffix.** They interleave the per-call
   `repo_map` argument (`Do not edit files...` / map / `Then break the goal into
   the`). `shared_prefix(run, family)` takes no `repo_map`. The planner is 23 of
   666 calls (3.5%) in EVR-0018. The planner prefix is therefore P1, P2, P3, P5,
   P6, and it is still byte-identical across planner attempts.
7. **Project context built once, from project state, not from a task.** Today's
   per-node packet is **not** task-independent. `_context_packet` prints only
   `packet["summary"]` and `state.constraints` / `state.validation_commands`, but
   `compile_context` runs `_fit` over the whole JSON packet first. That packet
   also holds the task text, `search_matches`, `matched_skills`,
   `development_context` and `profile_context`, all selected from the task. A
   long or match-rich node goal makes `_fit` prune `state` keys
   (`validation_commands` first, then `constraints`), so two nodes of one run can
   get different packet lines today. Compiling once from `run['goal']` would give
   a third, different text, and that breaks line-for-line parity on real
   projects. So the shared packet does not call `compile_context` or `_fit`.
   A module helper `_shared_packet(run_id, project, budget)` (no task argument)
   wrapped in `functools.lru_cache(maxsize=16)`. The cache key includes
   `run_id`, so the cache is **run-scoped**: `run_id` is used only as the key,
   and every new run in a long-lived orchestrator process misses and reads
   current project state. Only workers of the same run reuse a packet. The
   helper:
   - resolves `get_project(project)` and `load_state(project)`. Any exception
     returns `("", None)`, as `_context_packet` does;
   - emits the same lines as `_context_packet`, in the same order and format:
     `Project summary: <state['summary']>`, then for `constraints` and
     `validation_commands` the capitalised heading and `- <item>` for the first
     8 values. The line-building loop moves into a shared private helper
     `_packet_lines(summary, state)` that both paths call, so the format cannot
     drift;
   - cuts the joined text to `budget * 4` characters, as today;
   - returns `(text, measurement)` with the same keys as `_context_packet`.
     `selected_*` come from the text. `candidate_*` use the task-independent
     naive formula that `compile_context` uses (`state['context_files']` that
     exist plus `discover(project_path, state['skill_roots'])`), with no git,
     search, profile or handoff reads.

   **Why this is a superset of today.** `_fit` prunes whole state keys from the
   end of the printed order (`validation_commands`, then `constraints`). It
   clears `packet["summary"]` only after `state` is already empty, and then the
   per-node text is `""`. So today's untruncated per-node text is always a
   line prefix of the unpruned state text. With the same budget, both are cut at
   `budget * 4`, so **today's per-node packet text is a string prefix of the
   shared packet text** (`shared.startswith(off_packet)`). Every complete line
   of today's packet appears verbatim in the shared packet. The last line,
   when today's cut falls inside it, appears as the start of a shared line.
   §3 tests this property instead of exact line equality.

   Both `shared_prefix` and `build_measured(prefix=...)` call the cached helper
   with `run['run_id']`, so there is one state read per (run, project, budget).
   `build_measured(prefix=...)` returns a `copy.deepcopy` of that measurement, so
   the engine's `context_selected` event keeps its keys. Its `selected_*` values
   now describe the shared packet. A state edit while a run is live does not
   reach that run's prefix, which keeps the prefix byte-stable for the run (the
   provider cache scope). The next run, in the same process or a new one, reads
   the edited state. If an in-flight run is resumed in a new process, its first
   launch is one cache miss and the prefix may change once, with no parity loss.
   `maxsize=16` bounds memory: it allows 16 concurrent (run, project, budget)
   keys, which covers the three family budgets of several runs, and older runs
   are evicted. An eviction only costs a re-read. Tests on the flag-on path call
   `prompts._shared_packet.cache_clear()` in `setUp`. The flag-off path never touches the cache and keeps calling
   `_context_packet(project, node['goal'], ...)`.
8. **Budget override.** The superset property in §1.7 needs equal budgets. When
   `node.get("context_budget", default)` differs from
   `SHARED_CONTEXT_BUDGET[family]` (only possible when a planner task sets it),
   that node also gets its own flag-off packet,
   `_context_packet(project, node['goal'], node_budget)`, in the suffix (§2,
   S8), in the current format. The prefix stays family-identical, and parity
   holds line for line for that packet.
9. **Output contract stays in the suffix**, at the very end, as today. It differs
   between implementer/test_author and repairer, and the end of the prompt is
   where a worker looks for it.

## 2. Suffix: per-node blocks, in order

| # | Block | Content (verbatim from today's code) |
|---|---|---|
| S1 | role line | `` You are the <role> for Agent OS orchestrated run `<run_id>`. `` + blank |
| S2 | working directory | the two `Your working directory is <cwd>...` lines + blank, when `cwd` is given. `cwd` differs per worktree, so it **must** be in the suffix |
| S3 | assignment | `Your assignment (<id>): <node goal>` + blank |
| S4 | assignment rules (worker family) | `Assignment rules:` (new line), `- Edit only paths inside your scope: ...`, then `- Your work will be validated with:` and the command lines when validators exist, + blank |
| S5 | siblings (reviewer) | `_sibling_lines(run, node)`. It excludes the node's own subject and grows as tasks are added, so it is per-node |
| S6 | diff (reviewer) | `Change under review:` + fenced diff + blank |
| S7 | findings | reviewer: `Earlier review rounds left these findings unresolved...` + items; repairer: `Address these review findings...` + items |
| S8 | planner rules / own packet | planner: the whole current planner block, including `repo_map`; any family: own `Project context:` packet only in the budget-override case (§1.8) |
| S9 | output contract | `_contract(role)` |

## 3. Required-section parity (test contract)

Workers must still receive every rule they get today. Only order may change.
The parity test sits next to the prompt tests, as a new test module or a class in
an existing non-orchestrator test file. For each fixture node it builds
`off = build_measured(run, node, ...)` and
`on = build_measured(run, node, ..., prefix=shared_prefix(run, family(role)))`,
with the same `diff`, `findings`, `repo_map` and `cwd`. It asserts:

Packet text is the lines after a `Project context:` heading up to the next
blank line. `build_measured` emits the heading only when the packet is
non-empty. A flag-on prompt can hold two packets, so they are named by their
position relative to the `SHARED_PREFIX_END` line:

- `K(off)`: the packet after the only `Project context:` heading in `off`, or
  `""` if `off` has no heading.
- `K_prefix(on)`: the packet after the `Project context:` heading that
  precedes `SHARED_PREFIX_END` (block P3), or `""` if there is none.
- `K_suffix(on)`: the packet after the `Project context:` heading that follows
  `SHARED_PREFIX_END` (block S8, budget-override case only), or `""` if there
  is none.

Let `L(off)` be the multiset of non-empty lines of `off` (`line.strip() != ""`,
compared without stripping) outside `K(off)`. Let `L(on)` be the same for `on`,
outside both `K_prefix(on)` and `K_suffix(on)`. The `Project context:` headings
themselves are counted in `L`.

1. **Line multiset inclusion (all sections except project context).** Every line
   in `L(off)` appears in `L(on)` at least as many times. Only order may change.
2. **Project context by presence and prefix.** The project context is compared
   by presence, not line by line, because the shared packet is built once from
   project state (§1.7).
   - No override (`node.get("context_budget", default) ==
     SHARED_CONTEXT_BUDGET[family]`): `K_suffix(on) == ""`, and if
     `K(off) != ""` then `K_prefix(on) != ""` and
     `K_prefix(on).startswith(K(off))`.
   - Budget override (§1.8): `K_suffix(on) == K(off)` exactly. `K_prefix(on)`
     is the family packet, equal to `_shared_packet(run_id, project,
     SHARED_CONTEXT_BUDGET[family])[0]`, and is not compared with `K(off)`
     because the budgets differ.
3. **Closed set of additions.** `L(on) - L(off)` (multiset difference) contains
   only P1, the separator, `Assignment rules:`, and at most one
   `Project context:` line. That extra heading is the P3 heading when `off` has
   no packet (today's `_fit` emptied it for that node), or the P3 heading next
   to the S8 copy in the budget-override case. So `on` holds at most two
   `Project context:` lines, one on each side of `SHARED_PREFIX_END`.
   `K_prefix(on)` may be longer than `K(off)`; the extra lines are project state
   that today's `_fit` pruned for that node.
4. **Sections.** The set of section names with tokens > 0 in
   `context_anatomy.sections(off)` is a subset of the set for
   `context_anatomy.sections(on)`. This covers `header`, `goal`, `assignment`,
   `worker_rules`, `reviewer_rules`, `siblings`, `diff`, `findings`,
   `planner_rules`, `repo_map`, `planner_rules_2`, `project_context` and
   `contract`, wherever they occur today.
5. `on.startswith(prefix)`, and `on` ends with `_contract(role)`.

Fixture nodes: an implementer with scope and two command validators, a
test_author with an empty scope (`(whole repository)`), a repairer with findings
that carry `recommended_action`, a reviewer with diff, findings and siblings, and
a planner with and without `repo_map`. Fixtures run with operator messages and
with none, and with `project=None`.

**Real registered project test.** A patched fixed packet cannot show the
`_fit` divergence that §1.7 is about, so one test uses the real registered
project `personal-agent-os`, which existing tests (`tests/test_agent_os.py`)
already compile offline. It needs local registry, state and `git status` reads
only, and no network. Node goals: a short one (`"fix a typo"`), and a long,
match-rich one (the run goal repeated plus skill and path names, more than 2000
characters), so `_fit` sees different packet sizes. The test asserts:

- `shared_prefix(run, family)` is byte-identical for every node of the family;
- for every node, `K_prefix(on) == _shared_packet(run_id, project, budget)[0]`
  and `K_prefix(on).startswith(K(off))`, where `K(off)` is today's per-node
  `_context_packet(project, node['goal'], budget)[0]`;
- a second run with a different `run_id`, built after the state is changed in
  the same process, gets the new state in its `K_prefix` (the cache is
  run-scoped, §1.7);
- the full checks 1 to 5 above.

If `K(off)` is already equal for both goals on the current registry state, the
prefix assertions still hold. The test then also builds a temporary state copy
with 8 long constraints and 8 validation commands (patched `load_state`) to force
`_fit` pruning for the long goal, and repeats the assertions on that state.

## 4. Byte-stability rule

The prefix is a pure function of `(run['run_id'], run['goal'],
_shared_packet(run['run_id'], run['project'], budget), family, run['operator_messages'])` and
module constants. No node goal reaches it, not even through context selection. It must not
contain:

- timestamps, other than the one inside `run_id`, which is constant for the run
  and is the cache scope;
- node ids, node goals, attempt numbers, scope paths, validator commands, `cwd`
  or any other filesystem path;
- provider, model, capability class, effort, or any policy value;
- text that depends on iterating `run['nodes']` or any dict or set. Operator
  messages come from a list in append order.

Formatting: `"\n"` line endings only, no trailing whitespace, and UTF-8. The
separator line `SHARED_PREFIX_END` and the blank line after it are the final
bytes of the prefix. The prefix ends on a newline, so the cache boundary never
falls inside a token that spans prefix and suffix.

Stability test: `shared_prefix(run, f)` returns identical bytes when called
twice, when nodes are added or reordered in `run['nodes']`, for every node of
family `f`, and for different `cwd` values. It also contains none of the
fixture's node ids, scope paths or cwd strings.

## 5. Default rule

`shared_prefix` defaults to **False**. It may be set to True only when every
existing test matching `tests/test_orchestrator_*.py` passes **unchanged** with
the default flipped. Unchanged means `git diff main -- 'tests/test_orchestrator_*.py'`
is empty, and `python -m unittest discover -s tests -p "test_orchestrator_*.py"`
passes. If any test asserts the current order (for example, that a prompt starts
with `You are the`), the default stays False, and that test is not edited to make
the flip pass. Either way, the flag-off path keeps today's exact bytes.

## 6. Measurement plan

**Cacheable tokens.** For a run's prompts in launch order, grouped by family `F`
with `k_F` prompts:

```text
LCP_F           = os.path.commonprefix(prompts of F)                 (characters)
cacheable_F     = (k_F - 1) * floor(len(LCP_F) / 4)                  first call writes, the rest can read
run_lcp_tokens  = floor(len(os.path.commonprefix(all worker prompts)) / 4)
```

`prompts.common_prefix_tokens(texts: list[str]) -> int` implements
`floor(len(commonprefix)/4)`. Floor keeps the figure conservative compared with
the `ceil` in `estimate_tokens`.

**Before/after comparison through the harness.** New module
`src/agent_os/orchestrator/shared_prefix_compare.py` with
`compare(work_dir: Path) -> dict` and a `__main__` that prints the JSON. It makes
no model calls and no network calls, and it is deterministic.
`context_economy.py` is **not edited**: the comparison only calls its public
`build` and reads the existing v1 keys.

1. Build a synthetic run. Use a fixed goal of about 600 tokens and a fixed plan
   passed through `planner.planner_plan` + `planner.expand`, as
   `context_anatomy.build_run` does: 6 implementer/test_author tasks with
   validators, their reviewers with `context_anatomy._synthetic_diff`, and one
   repairer with findings. Patch `load_state`/`get_project` with one fixed
   state, so both `_context_packet` (off) and `_shared_packet` (on) read the same
   project data without touching the registry. Each node gets a
   distinct `cwd = "/fixture/wt/<node_id>"`, which mirrors per-node worktrees.
   This matters: `build_run` uses one shared `cwd`, and that would overstate the
   "before" common prefix.
2. Render every prompt twice: off (`prefix=None`) and on
   (`prefix=shared_prefix(run, family)`).
3. For each arm, write `<work_dir>/<run_id>/telemetry.jsonl` with the ledger
   event schema. Arm off is `run-20260101T000000Z-000000`; arm on is
   `run-20260101T000000Z-000001`. Write one `run_started` event, then one
   `model_completed` per prompt in launch order with `role`, `capability_class`,
   `provider`/`model` = `fixture`, `attempt` 1, `prompt_chars`, and
   `prompt_tokens_estimate`. Usage is
   `accuracy="exact"`, `source="fixture"`, `input_tokens = P(c)`,
   `cache_read_tokens = floor(max_{j<i} len(commonprefix(p_i, p_j)) / 4)`,
   `cache_write_tokens = 0`, and `output_tokens = 0`. Do not use
   `source="synthetic"`, because the harness excludes it. This models
   token-granular automatic prefix caching over Orchestrator-written text only
   (CLI preamble = 0), and it is an upper bound for providers with coarser cache
   boundaries.
4. Run `context_economy.build([run_dir])` per arm and drop `generated_at`. Take
   `sum_input`, `count` and `cache_read_share` from its existing
   `amplification.all` and `amplification.by_role.<role>` output. `_group` has no cache-read sum, so
   `shared_prefix_compare` computes `sum_cache_read` itself, overall and per
   role, by summing `usage.cache_read_tokens` over the `model_completed` events
   it just wrote. Then `uncached = sum_input - sum_cache_read`. As a
   consistency check, the module asserts that its own `sum(input_tokens)` equals
   the harness `sum_input` for each arm and role. So the harness and the
   telemetry describe the same calls.
5. Return `{"off": arm, "on": arm, "reduction": {...}}`. Each arm has
   `sum_input`, `sum_cache_read`, `uncached`, per-role `cache_read_share.median`,
   `cacheable_F` and `prefix_tokens_F` per family, and `run_lcp_tokens`.
   `reduction` has `uncached_ratio = 1 - on.uncached / off.uncached` and
   `added_prompt_tokens = on.sum_input - off.sum_input`. The added tokens come
   from the header, separator and heading lines, and are reported, not hidden.

Test (in `tests/test_context_economy.py`, no network, temp dir):
`on.uncached < off.uncached`; `LCP_F` covers the whole prefix for every family
with `k_F >= 2`; two `compare` calls return identical JSON; and the report passes
the harness privacy scan (no node ids or cwd strings).

**Evidence.** Run `python -m agent_os.orchestrator.shared_prefix_compare` once and
record the results with the existing record formats:

- **EXP-NNNN**: hypothesis: a family-level shared prefix makes at least 25% of
  Orchestrator-written worker input tokens cacheable that are uncached today,
  with no rule lost. Falsifier: `uncached_ratio < 0.25`, or any parity check
  failure.
- **EVR-NNNN** (`task_family: "context_economy"`): `metrics` holds the
  comparison figures, `parity_passed`, `model_calls: 0` and `spend_usd: 0`.
  `links`: `measures` → `src/agent_os/orchestrator/prompts.py`, `relates_to` →
  `IMP-0018`, `relates_to` → `EVR-0018`.

## 7. Expected effect and limits

The EVR must state these limits:

- **Scale.** Orchestrator-written text is about 1% of provider input (EVR-0018
  pooled amplification is 104.8x). Most of the fixed overhead is the agent CLI's
  own system prompt, its tool schemas and repository rediscovery, and Phase 1
  does not touch any of it. Phase 1 extends the already-cached CLI preamble by
  the shared prefix. The fixture reduction applies to the Orchestrator-written
  share only. Do not report it as a reduction of total provider input.
- **Delivery.** Providers with automatic token-prefix caching (OpenAI/Codex
  style, at least 1024 tokens, which the CLI preamble already exceeds) can hit
  on the prefix directly. With explicit cache breakpoints (Claude style), a hit
  inside the first user message also needs the prefix to arrive as its own
  cacheable block, for example through a system-prompt append option in the
  adapter. That adapter change is a follow-up and is outside Phase 1. Until live
  telemetry shows a higher `cache_read_share` for flag-on runs, evidence says
  "cacheable", not "cached".

## Default decision

Date: 2026-10-02

Command: `python -m unittest discover -s tests -p "test_orchestrator_*.py"`

Results:
- Ran 217 tests in 290.648s
- FAILED (errors=1, skipped=1)
- Failing test: `test_context_selection_is_recorded_for_registered_projects`
  - Error: KeyError: 'candidate_tokens_estimate' when flag=True

Resulting default: **False**

Rationale: The test `test_orchestrator_telemetry.EngineTelemetryTests.test_context_selection_is_recorded_for_registered_projects` fails with the shared_prefix flag set to True. The root cause is that when the shared prefix is compiled, the context selection event is recorded without the full measurement structure — specifically, the `shared-prefix context_selected` telemetry event lacks the `candidate_*` fields that the flag-off path provides (it only has `selected_*`). This occurs because the event is picked up as `selected[0]` from the shared prefix compilation rather than from the per-node context selection. The measurement object itself (prompts.py:46) still correctly populates these fields in the flag-off case; the gap is in the telemetry event emission. A follow-up should emit the prefix event under a different type (e.g., `shared_prefix_compiled`) or ensure the context_selected event includes the candidate_* fields for consistency. The flag remains defaulted to False until this telemetry gap is resolved.
