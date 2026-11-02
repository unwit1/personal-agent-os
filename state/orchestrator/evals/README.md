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

## Running

```powershell
# test suites: git refs, each in a detached worktree with the trusted runner copies
agent-os orchestrate eval --suite EVS-CONTROL-PLANE --incumbent main --candidate <branch-or-commit>
# case suites: routes provider[:model][@class], worktree pinned to the case file's base_commit
agent-os orchestrate eval --suite EVS-CAPABILITY-CLASSIFICATION --incumbent claude-code@balanced --route codex@fast --route claude-code@fast
```

Each run writes one append-only EVR (`records/evaluations/`) with per-dimension
deltas and verdicts; the candidate verdict uses only the quality dimension, so
cost never rescues a regression (DEC-0005). Case-suite runs also record
accuracy-scored capability observations; follow with `orchestrate capability --write`.
Case suites also take `--samples N` (each base route is called N times; a
`+verify` variant such as `codex@fast+verify` is scored from the same calls),
and `--max-calls` refuses runs over budget. Before paying for new samples,
replay stored outputs under `.agent-local/orchestrator/delegations/` (EXP-0001
predicted its own result that way). Exit code 8 means a candidate regressed. EVS-COST still runs through
`agent-os orchestrate benchmark` (its runner type is not supported by `eval`).

## Rules

- Optimizers read `development` and `validation` only. `holdout/` is
  operator-invoked and reports pass/fail aggregates, never case contents.
- Suite definitions, evaluators and holdouts are protected control-plane paths.
  A candidate that edits them fails validation (`control_plane.py`).
- Classification and eval tasks run against a pinned commit (FND-0002).
- External corpora: register first (license and permissions verified from the
  source), store machine-locally, record revision + checksum, never mix
  training data with evaluation data.
