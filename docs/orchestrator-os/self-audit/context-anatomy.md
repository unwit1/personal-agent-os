# Context anatomy audit

## Commands run

The environment variable was set for each command to `C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator`.

```powershell
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate list
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260930T181109Z-d9a9d8
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260923T202405Z-5e4d75
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260924T143653Z-746b90
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260924T133405Z-dc8cf4
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260923T200037Z-a1e3c0
$env:AGENT_OS_ORCHESTRATOR_HOME='C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator'; python -m agent_os orchestrate context-anatomy run-20260922T200659Z-5b8a73
```

The listing contained seven runs: the current `READY` run (excluded), these six non-current runs, and no benchmark run. The six comprise two `COMPLETE` runs and four `PAUSED` runs. `PAUSED` is treated here as a finished, inactive attempt; the CLI did not list six `COMPLETE` runs. Context-anatomy was run with its default `--harness-tokens 6000` setting. Percentages below are calculated as section token count divided by `prompt_tokens_total`; percentages are rounded to one decimal place.

## Measurements

| Run ID (listed state) | Model calls | Prompt tokens total | Top prompt sections by tokens (tokens; share of total) | Worker fan-out duplication | Context amplification |
|---|---:|---:|---|---:|---:|
| `run-20260930T181109Z-d9a9d8` (PAUSED) | 25 | 114,360 | diff 68,692 (60.1%); goal 16,325 (14.3%); worker_rules 8,500 (7.4%) | 85,167 tokens (76.5%) | 8.24 |
| `run-20260923T202405Z-5e4d75` (PAUSED) | 22 | 52,837 | goal 22,836 (43.2%); diff 8,802 (16.7%); worker_rules 5,877 (11.1%) | 39,512 tokens (79.4%) | 11.50 |
| `run-20260924T143653Z-746b90` (COMPLETE) | 13 | 24,536 | diff 11,091 (45.2%); assignment 3,315 (13.5%); worker_rules 2,807 (11.4%) | 11,773 tokens (48.0%) | 5.76 |
| `run-20260924T133405Z-dc8cf4` (COMPLETE) | 16 | 19,626 | worker_rules 4,500 (22.9%); assignment 3,928 (20.0%); contract 2,897 (14.8%) | 12,149 tokens (69.3%) | 9.29 |
| `run-20260923T200037Z-a1e3c0` (PAUSED) | 3 | 4,746 | repo_map 1,479 (31.2%); planner_rules_2 1,422 (30.0%); contract 940 (19.8%) | 0 tokens (share not reported) | 3.01 |
| `run-20260922T200659Z-5b8a73` (PAUSED) | 7 | 7,741 | assignment 2,496 (32.2%); contract 1,712 (22.1%); planner_rules 1,482 (19.1%) | 3,459 tokens (71.9%) | 6.13 |

## Findings

- The overall goal section totals 16,325 tokens in `run-20260930T181109Z-d9a9d8` and 22,836 in `run-20260923T202405Z-5e4d75`, equal to 14.3% and 43.2% of each run's prompt tokens, respectively. In the first run, the repeated-line report separately identifies the overall-goal line as 2,415 wasted tokens across 24 copies.
- Reviewer sibling-list context is measured at 1,368 tokens across four reviewer calls in `run-20260930T181109Z-d9a9d8` (342 tokens per reviewer call, estimate: 1,368 / 4), and 796 tokens across six reviewer calls in `run-20260923T202405Z-5e4d75` (about 133 per call, estimate: 796 / 6).
- Fan-out duplication accounts for 48.0% to 79.4% of prompt tokens in the five runs with worker fan-out: 11,773/24,536, 85,167/114,360, 39,512/52,837, 12,149/19,626, and 3,459/7,741 as reported. The planner-only run has zero duplicated fan-out tokens and no duplication-share value.
- The reported context amplification ranges from 3.01 in the three-call planner-only run to 11.50 in `run-20260923T202405Z-5e4d75`; these are report values, not independently recomputed estimates.

The CLI notes that token counts are estimates from characters divided by 3.5, and that harness tokens are per call and mostly cache-served.
