# Orchestrator OS evaluation harness

Provider-neutral evaluation compares **incumbent vs candidate on the same
applicable cases**, one dimension at a time (constitution §5).

```
evals/
  suites/        EVS-*.json  suite definitions (evidence-record-v1, type EVS)  [protected]
  evaluators/    scoring code/specs used by suites                              [protected]
  cases/
    development/ labeled cases optimizers may read and iterate on
    validation/  (create when needed) cases read only for promotion decisions
  holdout/       protected private cases; operator-invoked; aggregates only    [protected]
  external-corpora.json  third-party corpus registry (schema external-corpus-v1)
```

A suite record lists `metrics.runners` (test modules, benchmark entry points or
case files), `metrics.dimensions`, and `metrics.task_families`. `agent-os
validate` checks that every runner target exists.

## Running today

- Test-backed suites: `python -m unittest <runner modules>` on the incumbent
  and on the candidate branch.
- EVS-COST: `agent-os orchestrate benchmark` (offline, deterministic).
- EVS-CAPABILITY-CLASSIFICATION: `agent-os orchestrate delegate` per route
  with the development case prompt; score accuracy against
  `cases/development/*.json`; record the result as an EVR and run
  `agent-os orchestrate capability --write`.

The single command that runs suites for two refs and writes the EVR
automatically is **IMP-0003** (not built yet).

## Rules

- Optimizers read `development` and `validation` only. `holdout/` is
  operator-invoked and reports pass/fail aggregates, never case contents.
- Suite definitions, evaluators and holdouts are protected control-plane paths.
  A candidate that edits them fails validation (`control_plane.py`).
- Classification and eval tasks run against a pinned commit (FND-0002).
- External corpora: register first (license and permissions verified from the
  source), store machine-locally, record revision + checksum, never mix
  training data with evaluation data.
