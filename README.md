# Personal Agent OS

Personal Agent OS is a small, Git-backed context layer for coding agents. Durable
knowledge stays in this repository; the local SQLite search index is derived and
can always be rebuilt.

The first integrated project is **HR GUI**. Its project-local policy, memory,
handoffs, and skills remain in that repository. This repository stores routing
metadata and retrieves only the files relevant to a task. It does not ingest HR
documents, OCR output, employee data, or other private runtime artifacts.

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
- `agent-os init` synchronizes adapters, rebuilds the index, and validates setup.
- `agent-os status [project]` shows compact state and Git status.
- `agent-os search QUERY` searches the rebuildable lexical index.
- `agent-os context PROJECT TASK` compiles a focused task packet.
- `agent-os handoff PROJECT --completed ... --remaining ...` writes a durable handoff.
- `agent-os review --changed-file PATH ...` selects a risk-aware review level.
- `agent-os validate` checks canonical data, references, skills, adapters, and secrets.
- `agent-os mcp` exposes the same read-oriented operations over JSON-RPC on stdio.

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
5. Run `agent-os validate`, then `agent-os index`.
6. Configure a client with the compact adapter in `AGENTS.md` or `CLAUDE.md`.

No database backup is required. Re-running `agent-os index` restores derived
search state from Git-backed files.

## Client integration

Codex-compatible clients can read `AGENTS.md`. Claude-compatible clients can
read `CLAUDE.md`. Both are intentionally thin and point to
`policy/CANONICAL_AGENT_POLICY.md`.

For clients with JSON-RPC/MCP-style stdio integration, start:

```powershell
agent-os mcp
```

The server advertises `project.list`, `project.status`, `project.context`,
`memory.search`, `skill.search`, `agent.start_session`, and
`agent.finish_session`. This is a dependency-free JSON-RPC transport; a future
MCP SDK adapter can wrap the same Python service without changing canonical
storage.
