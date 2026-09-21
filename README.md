# Personal Agent OS

Personal Agent OS is a small, Git-backed context layer for coding agents. Durable
knowledge stays in this repository; the local SQLite search index is derived and
can always be rebuilt.

The first integrated project is **HR GUI**. Its project-local policy, memory,
handoffs, and skills remain in that repository. This repository stores routing
metadata and retrieves only the files relevant to a task. It does not ingest HR
documents, OCR output, employee data, or other private runtime artifacts.

The registry also routes AutoClick, Job Applicant Dashboard, OvertimeParser,
TES Tagger, and the reserved ScanRenamer directory. Each integration has an
explicit privacy boundary; runtime business data is excluded from indexing.

## Start development

```powershell
python agent.py init
python agent.py context hr-gui "fix the two-digit scanner date regression"
```

This local launcher has no third-party dependencies. For a conventional virtual
environment and globally available command, create a venv and run
`python -m pip install -e .`; then use `agent-os` instead of `python agent.py`.

## Core commands

- `agent-os projects` lists known projects.
- `agent-os scan-projects` detects new or moved folders without reading data files.
- `agent-os install-routing` safely installs missing global and project adapters.
- `agent-os routing-status` verifies installed adapters against canonical sources.
- `agent-os init` synchronizes adapters, rebuilds the index, and validates setup.
- `agent-os status [project]` shows compact state and Git status.
- `agent-os search QUERY` searches the rebuildable lexical index.
- `agent-os context PROJECT TASK` compiles a focused task packet.
- `agent-os handoff PROJECT --completed ... --remaining ...` writes a durable handoff.
- `agent-os review --changed-file PATH ...` selects a risk-aware review level.
- `agent-os validate` checks canonical data, references, skills, adapters, and secrets.
- `agent-os mcp` exposes the same read-oriented operations over JSON-RPC on stdio.
- `agent-os capture-candidates` stages durable findings for review; it never promotes them.
- `agent-os curate-candidates` applies deterministic checks and makes explicit review, rejection, or eligible promotion decisions.
- `agent-os maintenance` rebuilds derived context and reports candidate curation for an event trigger.
- `agent-os change-*` captures, updates, verifies, safely projects, and reviews compact engineering change records.
- `agent-os improvement-*` deduplicates project improvement candidates and prepares explicit GitHub issue payloads.
- `agent-os form-route` matches sanitized form fingerprints; `--persist` writes only to the gitignored local queue.

## Canonical versus derived data

Canonical, reviewed files live under `profile/`, `projects/`, `memory/`,
`skills/`, `policy/`, and `schemas/`. `.agent-os/index.sqlite` is a local cache.
Raw conversation history is deliberately outside the default context path.

Relevant active changes and improvements are scored per task and capped at three
compact summaries of each kind. Full records and full skill bodies are fetched only
on demand. Form intake stores template structure only: never source documents,
completed values, raw OCR, or personal data. Google is not a form-intake fallback;
change records can only produce an explicitly requested, allowlisted safe projection.
These repository capabilities do not force every ChatGPT surface to invoke them;
clients must use the installed skill/MCP bridge or an explicit GitHub issue payload.

## Fresh-machine recovery

1. Clone this repository and the project repositories referenced by
   `projects/registry.json`.
2. Install Python 3.11 or newer.
3. Install this project with `python -m pip install -e .`.
4. Update local project paths in `projects/registry.json` if necessary.
5. Run `agent-os install-routing`, then restart Codex so global instructions and skills reload.
6. Run `agent-os validate`, then `agent-os index`.

No database backup is required. Re-running `agent-os index` restores derived
search state from Git-backed files.

Private canonical remote: `https://github.com/unwit1/personal-agent-os`.

## Client integration

Client surfaces are registered in `surfaces/registry.json`. A *surface* is a
client a person reaches Agent OS through; each entry describes, in
provider-neutral terms, how that client invokes Agent OS, how it is
automatically preflighted, and how it returns handoffs and durable candidates.
Locations are machine-independent (`~`, `${VAR}`, `repo/`) and are resolved by
`src/agent_os/machine.py`.

```powershell
agent-os integration-health
agent-os integration-health --surface claude-code
agent-os integration-health --strict
```

The report places every surface in one of three tiers:

- **fully routed** — the client reaches the canonical checkout and is
  automatically preflighted (Claude Code, through the MCP registration and the
  user-scoped instruction file);
- **partially bridged** — one half is in place, or the registration resolves to
  a stale checkout, or capture needs a manual step (ChatGPT chat and Work
  projects, which cannot start a local stdio server);
- **not yet integrated** — no registration and no preflight instruction.

Each surface also reports whether it is registered, reachable, able to emit
handoffs and candidates, and what is missing, including a registration that
embeds a checkout path instead of the stable launcher. `--strict` exits non-zero
when a surface falls below its expected tier.


Codex-compatible clients can read `AGENTS.md`. Claude-compatible clients can
read `CLAUDE.md`. Both are intentionally thin and point to
`policy/CANONICAL_AGENT_POLICY.md`.

For clients with JSON-RPC/MCP-style stdio integration, start:

```powershell
agent-os mcp
```

The server retains `project.list`, `project.status`, `project.context`,
`memory.search`, `skill.search`, `agent.start_session`, and
`agent.finish_session`. Its regular-chat surface is deliberately smaller:

- `agent.context` recognizes substantial project work, resolves one likely
  project, and returns a token-budgeted packet with matched skill metadata,
  relevant handoff, validation hints, and freshness. It does not load raw chat
  history, every project, or full skill bodies by default.
- `agent.capture_candidates` stages evidence-backed findings with deterministic
  deduplication. A chat observation cannot rewrite canonical memory directly.
- `agent.search`, `agent.project_status`, `agent.skills_match`, and
  `agent.latest_handoff` are focused fallbacks when the context call is not
  enough.

Candidates remain Git-tracked review records. The curator runs deterministic
checks first; material decisions, skills, project-state changes, and rules are
held for independent review. Routine, evidenced candidates can be explicitly
promoted into `memory/promoted-candidates.json`, which remains canonical Git
data. The included GitHub workflow can rebuild the disposable index and report
pending curation after repository events. Google Docs mirroring is intentionally
skipped until a Docs connector is configured, so it can never block canonical
updates.

`agent-os mcp` is also a dependency-free MCP stdio server: it supports MCP
initialization, tool discovery, and tool calls alongside its lightweight
JSON-RPC compatibility operations.

Register clients against the stable launcher rather than this checkout, so a
repository move does not break the integration:

```powershell
agent-os launcher-install
agent-os launcher-verify
```

`launcher-install` writes `~/.agent-os/agent_os_mcp_launcher.py`; point the
client's MCP registration at that file. The launcher resolves the current
checkout and then serves **in its own process**. It must never hand the session
to a replacement process: `os.execv` does not replace the process image on
Windows, so the client sees the process it spawned exit during the handshake
while the inherited pipes stay open, and waits on a server it believes is dead
until its own timeout. `launcher-verify` holds the process open across a real
handshake and fails if it exits, which draining stdout to EOF would not catch.

### Staged workflows

Complex work decomposes into stages so one expensive session does not carry a
whole job. Stages name a provider-neutral capability class (deterministic ->
fast -> balanced -> reasoning -> frontier); concrete models resolve at run time
from configured providers. Deterministic stages execute locally for free; other
stages are prepared with their own budgeted context and an exact next prompt,
then handed to whatever agent is running.

```powershell
agent-os workflows
agent-os workflow-start repository-health-sweep --run-id sweep-1
agent-os workflow-run   repository-health-sweep --run-id sweep-1
agent-os workflow-next  repository-health-sweep --run-id sweep-1
```

Run state persists under `projects/<project>/workflows/` and carries no
transcript, so an interrupted job resumes from disk. Escalation happens only
after a declared validator actually fails, and a stage that already passed is
never silently redone by a stronger model. See `docs/staged-workflows.md`.

### Shared document intelligence

A reusable extraction layer so projects do not each repeat page hashing, blank
detection, embedded-text extraction and OCR routing. No OCR engine is bundled:
callers pass their own extraction and OCR callables.

```powershell
agent-os document-cache-status
agent-os document-cache-prune --max-age-days 90
agent-os document-cache-clear
```

The cache key covers only what determines the extracted bytes, so changing a
classifier or fingerprint reuses the OCR instead of paying for it again. The
cache is workstation-local: a location inside the tracked repository is refused
structurally, and `validate` asserts nothing under `.agent-local/` is tracked.
Template signatures are built from an allowlisted form vocabulary, so two
copies of one form filled in by different people match while personal values
never enter a signature. See `docs/document-intelligence.md`.

### Selective profile retrieval

Durable personal context in `profile/` is never injected whole. It is flattened
into addressable facts carrying domain, provenance, confidence, sensitivity and
recency, and only the slice a task touches is compiled in.

```powershell
agent-os profile-status
agent-os profile-retrieve "plan meals and groceries for next week"
```

Relevance needs a distinctive signal, so a task with no personal dimension
retrieves nothing. The privacy section is never retrievable, and any fact
tripping the privacy gate is dropped at retrieval regardless of what is on
disk. Over MCP: `profile.retrieve`, `profile.status`. See
`docs/selective-profile-retrieval.md`.

### Context budgeting

`agent.context` prunes by usefulness, not by source order. Verbose history goes
first and the task's own next action goes last. The previous handoff is graded
rather than dropped whole: its finished narrative (`completed`, `validation`) is
generic bulk, while its `decisions` and `remaining` are the next action and are
shed only after broad state, lexical matches, and skill metadata. Improvements
and changes selected for the current task survive to the tightest budgets.
