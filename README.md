# Orchestrator OS

Provider-neutral orchestration of coding agents on any Git repository. You
give it a repository and a goal. It plans, picks a permitted provider, runs
workers in isolated worktrees, validates, reviews, asks for approval where
policy requires it, and integrates on a run branch.

It runs on its own. [Agent OS](https://github.com/unwit1/personal-agent-os)
can drive it and supply richer project context, but that is optional.

## Install

```bash
git clone https://github.com/unwit1/orchestrator-os && cd orchestrator-os
python -m venv .venv && .venv/bin/pip install -e .
```

Python 3.11+. Runtime dependencies are `keyring` and `jsonschema`.

## Run

```bash
orchestrator providers --suggest          # find installed coding CLIs (Claude Code, Codex, ...)
orchestrator providers --suggest --write  # save them to the machine registry
orchestrator start-recommended --repo ~/src/my-app --goal "add a /health endpoint with a test"
orchestrator list
orchestrator status <run_id>
orchestrator approve <run_id> <gate_id>
orchestrator gui                          # local control GUI + API
```

Every action of the old `agent-os orchestrate …` works as
`orchestrator …`. A leading `orchestrate` is accepted too.
`docs/orchestrator-os/COMMANDS.md` lists them all. `python -m orchestrator_os`
is the same command.

To try it without any model, point it at a synthetic provider:

```bash
cat > /tmp/providers.json <<'EOF'
{"providers":[{"id":"synth","adapter":"synthetic","models":{"fast":"s","balanced":"s","reasoning":"s","frontier":"s"},"effort_map":{"none":"n","low":"l","medium":"m","high":"h"}}]}
EOF
AGENT_OS_PROVIDERS=/tmp/providers.json orchestrator start-recommended --repo <git repo> --goal "demo" --validator "git status"
```

## Where things live

| What | Where | In Git |
|---|---|---|
| Control-plane policy | `policy/orchestrator-os.policy.json` | yes |
| Evidence records, eval suites, provider policy, prior-art registry | `state/` | yes |
| Run state, worktrees, transcripts, telemetry | `.agent-local/` under the state root, or `AGENT_OS_ORCHESTRATOR_HOME` | no |
| Provider registry, budgets | `~/.agent-os/` (`ORCHESTRATOR_CONFIG_DIR` to change) | no |

The state root is `ORCHESTRATOR_STATE_ROOT`. Without it, the root is this
checkout for editable installs, and `~/.orchestrator-os` otherwise.

## Projects (optional)

A run can always name `--repo`. To give repositories ids, summaries,
constraints and validation commands without Agent OS, write
`~/.agent-os/orchestrator-projects.json`, or point `ORCHESTRATOR_PROJECTS` at
a file:

```json
{"projects": [{"id": "web", "path": "~/src/web", "summary": "Next.js storefront",
               "constraints": ["no new runtime deps"], "validation_commands": ["npm test"]}]}
```

With Agent OS, set `ORCHESTRATOR_HOST=agent_os.orchestrator_host:HOST`, or
let Agent OS set it (`AGENT_OS_ORCHESTRATOR_BACKEND=external`).

## Protecting a repository

The Orchestrator never lets a worker edit its own control plane: policy,
validators, evaluators, holdouts or append-only evidence. Any repository can
opt into the same guard by committing `policy/orchestrator-os.policy.json`
with `control_plane.protected_paths` (and optionally `records_dir`).

## Development

```bash
python -m unittest discover -s tests
```

About 1,300 tests. Some skip unless the Agent OS host is present. Each skip
states why, and those tests run from personal-agent-os CI. The repository's
history before the extraction lives in personal-agent-os; `PROVENANCE.json`
maps every file to its origin. See `docs/MIGRATION.md`.

Third-party notice: no third-party code is vendored. Harness² integration
(planned, optional) stays an external, pinned, Apache-2.0 dependency.
