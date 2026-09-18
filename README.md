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

## Canonical versus derived data

Canonical, reviewed files live under `profile/`, `projects/`, `memory/`,
`skills/`, `policy/`, and `schemas/`. `.agent-os/index.sqlite` is a local cache.
Raw conversation history is deliberately outside the default context path.

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

This is a dependency-free JSON-RPC transport; a future MCP SDK adapter can wrap
the same Python service without changing canonical storage.
