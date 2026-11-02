# Open-source AI sweep, 2026-10-17: synthesis

Scope: 28 projects in six batches (tool-output, memory-and-context,
code-context, orchestrators-a, orchestrators-b, output-and-instructions). All
28 are now in `registry.json` (`as_of` 2026-10-17). Two entries were changed to
fit the schema: `revisit_when` became a list for the four
output-and-instructions entries, and the PA-repomapper link got a `rel`. Reddit
was unreachable, so no project is claimed as posted on r/OpenSourceAI. No batch
found such a thread.

How to read the ranking: our measured cost is dominated by **frontier retries
after validator failures (43% of hr-cc-run4)** and by implementer calls (63%).
Tool results are only about **20% of input-side cost**, and 94% of their bytes
were already narrowed. An idea that cuts retries or failed integrations can
save several times more than any tool-output trick, so those ideas rank first.
Most of the token-saving projects in this sweep act inside a loop Agent OS does
not own, and our measured facts argue against them.

## Shortlist (ranked)

### 1. Validator-miss fixture suite (from Bernstein, PA-bernstein)
- Where: fixtures under `tests/` driving `src/agent_os/orchestrator/validators.py`
  and the review path (`review.py`). This complements `mutation.py`, which
  mutates control-plane code, not worker diffs.
- Cheapest test (offline): from run records and handoffs, collect 8–10 worker
  diffs that passed validators or review and later turned out defective. Replay
  the validators on them and record the catch rate. For each miss, also note
  whether the defect was in the diff's callers or tests; that feeds #4 at no
  extra cost.
- Justifies implementing: a catch rate below 80%. The fixtures then become a
  permanent regression suite and the specific gaps get validator fixes. At 80%
  or above, keep the fixtures and stop there.

### 2. Downgrade at the cost cap instead of stopping (from Omnigent, PA-omnigent)
- Where: `budget.py` already has project and per-job hard caps, but they stop
  work. The rule (soft threshold, then force a cheaper tier, fail closed on
  unpriced models) belongs there and in the escalation path in
  `engine.py`/`router.py`.
- Cheapest test (offline): replay hr-cc-run4's cost ledger with a simulated cap
  at 70% of actual spend, comparing the downgrade rule with a hard stop. A
  saving without a pass-rate estimate means nothing, because escalation happens
  *because* the cheaper tier failed. So attach recorded per-tier pass rates
  (eval or route-calibration history) to every downgraded call.
- Justifies implementing: at least 20% of frontier-retry cost saved, with an
  estimated zero extra failed tasks. Then confirm live on at most 5 tasks.

### 3. Diff lint the worker can run before handing off (from agentless-mcp, PA-agentless-mcp)
- Where: as an extra check named in the worker prompt (`prompts.py`) so the
  worker runs it in-session. Run only after the worker exits (`validators.py`),
  it mostly duplicates the validators and cannot reduce retries.
- Cheapest test (offline): run `lint --diff` (or a stdlib `ast` approximation:
  syntax, signature or contract drift) on 30 historical diffs that failed
  validators and 30 that passed. Count only the failures that the worker's own
  validator command would *not* already have shown.
- Justifies implementing: it flags at least 20% of failing diffs, with under
  10% false positives on passing diffs. Installing the upstream CLI is a host
  action, so start with the stdlib approximation.

### 4. Blast-radius context for reviewers (from code-review-graph, PA-code-review-graph)
- Where: reviewer prompt assembly in the engine's review step. Reuse the
  definition-to-test-file mapping that `repomap.py` already computes, plus
  `ast` and grep for callers. Take no graph store.
- Cheapest test (offline): on 20 past reviewed diffs, build the caller and test
  set with a stdlib script. Measure the share of valid findings that cite files
  inside that set but outside the diff, and the tokens the set would add. Add
  the #1 misses that sit in the set.
- Justifies implementing: at least 25% of valid findings (or #1 misses) fall
  inside the set but outside the diff, and it adds less than about 10% to
  reviewer input.

### 5. Conflict-only retry (from Composio Agent Orchestrator, PA-composio-agent-orchestrator)
- Where: the integration step. `worktrees.merge()` already returns the
  conflicted files. A fresh worker would get only those files and both diffs,
  instead of a full task retry or escalation.
- Cheapest test (offline): count merge-conflict outcomes against validator
  failures across recorded run records.
- Justifies implementing: conflicts are at least 5% of failed tasks. Then build
  a deliberate-conflict fixture, and implement if the conflict-only retry costs
  under half a full retry.

### 6. Symbol-scoped reads (from repo-map / token-savior, PA-repo-map, PA-token-savior)
- Where: a worker instruction (`prompts.py`) or an opt-in MCP tool per worker.
  No orchestrator change.
- Cheapest test (offline): in recorded transcripts, find whole-file reads (the
  Read tool and `cat`) followed by an edit to one symbol. Compare the file's
  bytes with the enclosing symbol's bytes, using stdlib `ast`.
- Justifies implementing: the excess is at least 25% of tool-result bytes. Even
  that is only about 5% of input-side cost, since tool results are about 20%.
  Only then run token-savior's 10-task cost A/B (cache reads included, equal
  validator pass rate). If the replay fails, close both entries.

### 7. Lossless handles for Agent OS's own large artefacts (Headroom CCR, deepagents offload, RTK tee; one idea from three batches)
- Where: artefacts Agent OS builds itself. `worktrees.diff()` already truncates
  at `MAX_DIFF_CHARS` = 60,000 with "inspect the branch directly", which is
  already a pointer. `validators.failure_excerpt` (borrowed from distill) already
  keeps the failing line. What is left is to make truncation explicit and
  retrievable (path plus byte range) instead of a bare cut.
- Cheapest test (offline): from recorded runs, count how often reviewer diffs
  hit `MAX_DIFF_CHARS` and how often validator logs exceed the excerpt limit.
  Then check whether review misses or repeated retries cluster on truncated
  cases.
- Justifies implementing: truncation in at least 5% of reviews or retries, with
  misses concentrated there. Do not use the batch's proposed test (compressing
  the 528 tool results); it measures a surface this BORROW does not touch.

### 8. Launch-failure memo plus adapter preflight (from Scion and Agent-Reach, PA-scion, PA-agent-reach)
- Where: `provider_health.py` already has a failure-window breaker for provider
  quota and outages. Extend the key to launch causes that cannot change between
  attempts (missing CLI login, bad skill or worktree path), with a fix hint in
  the style of a `doctor` command.
- Cheapest test (offline): count worker launches in run logs that failed with
  the same error signature as the previous launch within 10 minutes.
- Justifies implementing: at least 3% of launches, or any run that spent more
  than one retry on an unchanged cause.

## Not worth it (now)

- **RTK hook** (PA-rtk): our replay saved 0 bytes on already-narrowed traffic,
  independent A/Bs show 0 to +7.6% cost, and its tee-and-hint idea is already
  covered by distill's failure excerpt.
- **Headroom proxy or MCP** (PA-headroom): it targets repetitive JSON or search
  payloads we do not produce, and a history-rewriting proxy loses 2–6% to cache
  rewrites.
- **tml** (PA-tml): tool schemas belong to the CLIs and are cached at 0.1x.
- **Intel Adaptive Token Compressor**: it needs two model services and
  publishes no savings or quality figure.
- **Hindsight service**: it would be a second memory authority. Its stdlib rank
  fusion idea waits until a recall@k fixture exists; none exists today.
- **Cognee**: LLM graph extraction duplicates the Git-backed store; its
  evidence is 24 vendor HotPotQA questions.
- **ACON compression**: history lives inside the CLI. The contrastive
  guideline-tuning loop overlaps PA-gepa and PA-dspy and is not a new lead.
- **Focus**: five tasks, no code. Dropping history pays the cache-rewrite
  penalty we already measured.
- **Agent-Reach tool**: scraping glue that needs platform cookies (#8 keeps its
  only useful idea).
- **Graphify and claude-code-memory-setup**: they duplicate repomap and memory.
  Graphify writes `graphify-out/` into worktrees.
- **RepoMapper**: stale and non-stdlib. Its PageRank idea stays under PA-aider.
- **fractal**: recursion multiplies fan-out and retry cost, parallelism is
  already only 1.43x, and approvals are off by default.
- **Claude Squad and Superset**: human GUIs under AGPL and ELv2 licences.
  Superset's lesson (never install hooks in global `~/.claude`/`~/.codex`
  config) is a one-line rule for whenever we add hooks.
- **Orca worktree guards**: `worktrees.remove()` already removes only
  registered worktrees or empty directories, so little is left to borrow.
- **Bernstein hash chain**: the run ledger is local, gitignored telemetry that
  fails open; there is no tamper threat to defend.
- **deepagents harness**: adopting it means rewriting the CLI workers.
- **Pi adapter**: cheap tiers already exist (http_api, OpenRouter, vLLM). Pi
  adds only a tool loop for them, so revisit it when a cheap tier needs a
  coding loop.
- **Caveman terse-reviewer line**: first compute reviewer and planner output
  share from the cost ledger (no model call needed). Below 10% of run cost,
  stop.
- **CostAffective**: no repository found.

## Claims that did not hold up

- **RTK "up to 90% smaller"** is a byte ratio on bash output from the vendor's
  own command mix. JetBrains measured +7.6% cost at low effort, Quesma did not
  recommend it, and our replay found 0 bytes to save. All three agree.
- **Headroom 21–57%** comes from seeded, repetitive MCP-style payloads; its own
  README says dense output barely compresses. Its accuracy suite is QA and math
  at N=100, not coding tasks. The 614M-token replay putting rtk, Headroom and
  Caveman together at about 3.7% is a search summary, but it agrees with our
  own replay.
- **Caveman "33.2% fewer input tokens"** is mostly its proxy shrinking tool
  output, the same mechanism our replay measured at 0. The voice alone is about
  3% better than "Answer concisely." Separately, the batch's premise that
  output is a small share of our cost is an assumption: BRIEF.md has no
  output-share figure.
- **tml "77% fewer tokens"** compares against verbose OpenAPI for three tools.
  Against minimal JSON the same table shows 251 vs 174 tokens.
- **Graphify "80%" or "71x"**: the repo's harness measures key-fact coverage on
  6 questions, not tokens. The 71x figure looks like the
  claude-code-memory-setup illustration (20,000 vs 280 tokens for one Graphify
  query), whose author now says it is not reproducible.
- **code-review-graph "65x"** is measured against feeding the whole corpus,
  which no agent does.
- **repo-map "-33%"** is one unpublished workflow.
- **token-savior "-43%"** is one prompt on one repo. Its "-80%" counts active
  tokens, which leaves out cached reads at 0.1x.
- **Hindsight "independently reproduced"**: the reproducers are co-authors of
  the paper, and the 94.6% figure has no reproduction details.
- **Cognee** compares itself with rivals on 24 HotPotQA questions with an LLM
  judge.
- **ACON 26–54%** counts peak tokens, not cost under cache pricing.
- **Focus "same accuracy"** is 3/5 vs 3/5.
- **agentless-mcp as evidence for WRAP**: the n=60 benchmark measures
  localization with native search *removed*. The shipped gate only *defers*
  search, and the lint and validate side the WRAP would use is not benchmarked.
  Read the WRAP as "pending test #3", at the low confidence the entry already
  records.
- **Bernstein "audit chain over every step"**: the chain is opt-in. Its
  SWE-bench harness is explicitly not live runs, and its own evasion suite
  catches 2 of 8.
- **"94% of bytes already narrowed" used to dismiss symbol reads** (code-context
  and token-savior batches): that group includes `cat`, which returns whole
  files. The figure shows distill's guard skipped those results, not that they
  were small. Whether Read-tool results are in the 528 is not stated, so #6 is
  still an open question.
- **Omnigent downgrade "targets the 43% retries"**: it saves money only if the
  cheaper tier passes, and escalation happened because it did not. Hence the
  pass-rate condition in #2.
- **Pi "cheaper escalation tier"**: Agent OS already reaches cheap models. What
  Pi adds is an agent loop, not a tier.
- **Orca BORROW**: overstated, because our cleanup already guards removal (see
  "Not worth it").
- **Headroom BORROW test**: proposed on tool results, while the BORROW targets
  Agent OS's own artefacts, part of which `MAX_DIFF_CHARS` truncation already
  covers (see #7).

## Offline checks run (2026-10-17, no model calls)

Over the 8 recorded runs on this machine (90 worker launches, 34 reviewer
prompts) and the four replayed hr-cc-run4 implementer transcripts:

| # | Check | Result | Bar | Decision |
|---|---|---|---|---|
| 5 | Merge conflicts among failed tasks | 0 conflicts; all 8 failures were validator failures | at least 5% | Close for now |
| 7 | Reviewer diffs hitting `MAX_DIFF_CHARS`; validator excerpts at their cap | 1 of 34 (2.9%); 0 of 8 | at least 5% | Close for now |
| 8 | Identical launch failure repeated | 0 | at least 3% | Close for now |
| 6 | Whole-file reads followed by an edit: bytes outside the edited symbol | 5 such reads; 15% excess (22.2 KB read, 18.8 KB in edited symbols). Workers mostly read ranges already | at least 25% | Close for now |

Still open, needing data the runs do not record yet: #1 (diffs later found
defective), #2 (per-tier pass rates), #3 and #4 (historical diffs with
review outcomes).
