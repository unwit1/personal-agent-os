# Open-source AI sweep, 2026-10-17: evaluation brief

Goal: find ideas, features or efficiency tricks in recent open-source AI
projects that are worth testing in Agent OS, and say plainly which are not.

## Source of candidates
The operator asked for projects discussed on r/OpenSourceAI. Reddit is not
reachable from this environment (the network proxy and the search crawler
both refuse reddit.com), so candidates come from web search over roundups,
GitHub topic lists and awesome lists that cover the same projects. When a
search shows a project was posted on r/OpenSourceAI, say so; otherwise do not
claim it.

## What Agent OS is (so "worth it" means something)
- A Python, stdlib-first orchestrator (`src/agent_os/orchestrator/`). A
  planner splits a goal into tasks, each worker runs in its own git worktree
  through a coding CLI (Claude Code or Codex via `adapters/`), deterministic
  validators decide pass/fail, independent reviewers check diffs, and failed
  work retries or escalates to a stronger model tier.
- Agent OS does not run the agent loop itself: tool calls, tool results and
  history live inside the CLI. A trick that rewrites tool output only helps
  if it can run as a CLI hook, proxy, skill or instruction file, or if Agent
  OS gains its own loop (`adapters/http_api.py`).
- Prior-art decisions already recorded are in
  `projects/personal-agent-os/research/prior-art/registry.json`. Check it so
  you do not repeat or contradict an entry without saying why.

## Measured facts about our own costs (use them; do not re-derive)
- 2026-10-16 offline replay of 528 real Claude Code tool results: 94% of
  bytes came from commands already narrowed with grep/head/tail/cat/sed;
  distill's tool-output compression saved 0 bytes on them.
- With the 1-hour prompt cache, history re-reads are 0.1x price; tool results
  were about 20% of input-side cost; a result stays in context for a median
  of 64 calls.
- Trimming history mid-session cost 2-6% more than it saved (cache rewrite).
- Lossy crushers removed text the model later used in 28-47% of reduced
  results.
- Run hr-cc-run4: 43% of cost was frontier retries after validator failures;
  8 implementer calls were 63% of cost; parallelism was 1.43x. Retry prompts
  now quote the failing test output.

## How to evaluate each project
1. Find the canonical repository (web search). Clone it shallow:
   `git clone --depth 1 <url> .oss-cache/<owner>__<repo>` (inside your
   worktree; `.oss-cache/` is git-ignored). Read the README and the code that
   implements the claimed trick. Never run its install scripts, hooks or
   binaries.
2. Separate claims from evidence. Who measured the headline number, on what
   workload, against what baseline? Is there a benchmark harness in the repo?
3. Map it to Agent OS: what exactly would we borrow, where would it go (file
   or module), and does our architecture even expose the surface it acts on?
4. Propose the cheapest test that would prove or kill it here, preferably
   offline (replay of recorded transcripts or validator logs, unit fixture)
   and say what result would justify implementing it.
5. Decide: BORROW (take the idea), WRAP (call it as a tool), ADOPT (depend on
   it; needs a linked EVR/EXP/DEC, so do not use ADOPT here), DEFER,
   REJECT, or INVESTIGATE. Be critical: stars and headline percentages are
   not evidence.

## Output (per batch; the validator checks this)
- `<batch>.md`: one `## <Project name>` section per project, each with these
  lines, exactly as labelled:
  - `Repository:` URL and evaluated commit/date
  - `License:`
  - `What it does:`
  - `Claims vs evidence:`
  - `Fit for Agent OS:`
  - `Test to run:`
  - `Verdict:` one of BORROW, WRAP, DEFER, REJECT, INVESTIGATE, then one
    sentence why.
- `<batch>.json`: `{"entries": [...]}` with one prior-art entry per project
  in the registry's entry format (see existing entries and
  `src/agent_os/orchestrator/prior_art.py` REQUIRED and EVIDENCE_DIMENSIONS).
  `id` is `PA-<slug>`; `evaluated_at` is `2026-10-17`.
- Check your files with
  `python projects/personal-agent-os/research/prior-art/sweeps/check_sweep.py <batch>`.
