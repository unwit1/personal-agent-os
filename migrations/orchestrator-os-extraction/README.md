# Orchestrator OS extraction

| File | Purpose |
|---|---|
| `extract.py` | builds the initial `orchestrator-os` tree from this checkout. It only reads the source, and is reproduces the import commits `642ed34` and `fa4c349` and the `state/` tree of `5ee2358` in the new repository |
| `overlay/` | new files in that tree: `host.py`, `__main__.py`, `pyproject.toml`, CI, `AGENTS.md`, `tests/test_standalone.py` |
| `inventory.py` | regenerates `docs/audits/orchestrator-component-inventory.json` metrics |

Decision and evidence: `docs/adr/0001-orchestrator-os-extraction.md`,
`docs/audits/2026-10-orchestrator-baseline.md`,
`docs/audits/2026-11-orchestrator-simplification-backlog.md`.

## Publish the new repository

The session that did the extraction could not create GitHub repositories, so
the full `orchestrator-os` history was pushed to this repository as the
branch **`claude/orchestrator-os-main`**. It has an unrelated root and shares
no history with `main`.

1. Create `unwit1/orchestrator-os` on GitHub as **private**. `state/` holds eval holdouts and evidence records. Do not add a README or license, so the push is not rejected.
2. Mirror the branch:

   ```bash
   git clone --branch claude/orchestrator-os-main --single-branch https://github.com/unwit1/personal-agent-os orchestrator-os
   ```

   ```bash
   cd orchestrator-os && git remote set-url origin https://github.com/unwit1/orchestrator-os && git push -u origin claude/orchestrator-os-main:main
   ```

3. Delete the transport branch from personal-agent-os once the push is verified:

   ```bash
   git push https://github.com/unwit1/personal-agent-os --delete claude/orchestrator-os-main
   ```

To rebuild the initial import independently and compare:

```bash
python migrations/orchestrator-os-extraction/extract.py --dest /tmp/orchestrator-os-check
```

## Use it from Agent OS (opt-in until cutover)

```bash
pip install -e <path-to-orchestrator-os>
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
