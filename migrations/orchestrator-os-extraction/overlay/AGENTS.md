# Orchestrator OS: agent instructions

- Run `python -m unittest discover -s tests` before and after a change.
- Protected paths are listed in `policy/orchestrator-os.policy.json`
  (`control_plane.protected_paths`). Do not edit them unless the operator grants it.
- Agent OS business logic never gets imported here. Project context comes
  through `src/orchestrator_os/host.py`.
- Runtime state lives under `.agent-local/` (gitignored) or `ORCHESTRATOR_HOME`.
  Never commit run state, transcripts or credentials.
