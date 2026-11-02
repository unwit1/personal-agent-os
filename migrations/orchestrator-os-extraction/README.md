# Orchestrator OS extraction

| File | Purpose |
|---|---|
| `extract.py` | builds the initial `orchestrator-os` tree from this checkout. It only reads the source, and is reproduces the import commits `642ed34` and `fa4c349` and the `state/` tree of `5ee2358` in the new repository |
| `overlay/` | new files in that tree: `host.py`, `__main__.py`, `pyproject.toml`, CI, `AGENTS.md`, `tests/test_standalone.py` |
| `inventory.py` | regenerates `docs/audits/orchestrator-component-inventory.json` metrics |

Decision and evidence: `docs/adr/0001-orchestrator-os-extraction.md`,
`docs/audits/2026-10-orchestrator-baseline.md`,
`docs/audits/2026-11-orchestrator-simplification-backlog.md`.

## Published repository

The extracted history lives at **https://github.com/unwit1/orchestrator**
(private), branch `main`, published 2026-11-02. The package and CLI names are
unchanged (`orchestrator-os`, `orchestrator_os`, `orchestrator`).

```bash
git clone https://github.com/unwit1/orchestrator
```

To rebuild the initial import independently and compare:

```bash
python migrations/orchestrator-os-extraction/extract.py --dest /tmp/orchestrator-check
```

## Use it from Agent OS (opt-in until cutover)

```bash
pip install -e <path-to-orchestrator-checkout>
```

PowerShell:

```powershell
$env:AGENT_OS_ORCHESTRATOR_BACKEND = "external"
agent-os orchestrate list
```

`agent-os orchestrate …`, the MCP `orchestrate.*` tools and the Executive
window then drive `orchestrator_os`, with Agent OS as host. The run store stays
at `.agent-local/orchestrator`. Unset the variable to roll back.

Contract test: `python -m unittest tests.test_orchestrator_bridge`. It skips
when `orchestrator_os` is not installed.

The cutover checklist is in the new repository's `docs/MIGRATION.md`.
