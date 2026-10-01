# Run event audit

Read-only audit of the run history present on 2026-09-30. The history directory contained 7 run folders; the explicitly excluded active run was `run-20260930T215623Z-77a6c6`, leaving 6 eligible real runs. Therefore this report covers all 6 available runs, fewer than the requested maximum of 15. No run files were modified.

## Event types and category mapping

Distinct `type` values observed (42):

`completion.failed`, `completion.passed`, `completion.repair`, `driver.spawned`, `foreman.applied`, `gate.approved`, `gate.opened`, `gate.rejected`, `integration.merged`, `node.cancelled`, `node.deferred`, `node.escalated`, `node.failed`, `node.invalid_model`, `node.malformed`, `node.process_error`, `node.quota`, `node.reassigned`, `node.retry`, `operator.message`, `plan.expanded`, `provider.cooldown`, `provider.failover`, `repair.requested`, `review.completed`, `review.requested`, `run.complete`, `run.created`, `run.paused`, `run.resumed`, `run.started`, `run.state`, `run.stopped`, `tick.error`, `validation.baseline`, `validation.baseline_excused`, `validation.failed`, `validation.passed`, `worker.finished`, `worker.launched`, `worker.reattached`, `worktree.created`.

| Category | Event types and interpretation |
|---|---|
| Run lifecycle | `run.created`, `run.started`, `run.state`, `run.paused`, `run.resumed`, `run.stopped`, `run.complete` |
| Planning and tasks | `plan.expanded`; task count uses distinct non-planner task node names, excluding node names ending in `.reviewN` or `.repairN`. `plan` itself is excluded. |
| Worker attempts | `worker.launched` counts attempts; `worker.finished` reports their outcomes; `worker.reattached` is a continuation event, not a new launch. |
| Retries and escalation | `node.retry` counts explicit retries; `node.escalated` counts ladder/class escalations; `node.reassigned` is recorded separately and not added to escalation counts. |
| Validation | `validation.failed`, `validation.passed`, `validation.baseline`, `validation.baseline_excused`; accepted/validated task count is distinct base task nodes with `validation.passed`, excluding `.repairN` nodes. |
| Review | `review.requested`, `review.completed`; `changes_requested` is a rejected review round, and the `N material finding(s)` detail supplies finding count. |
| Provider and quota | `provider.failover`, `provider.cooldown`, `node.quota`, `node.invalid_model`, `node.process_error`; quota and invalid model are distinct from failover. |
| Gates and integration | `gate.opened`, `gate.approved`, `gate.rejected`, `integration.merged`, `completion.failed`, `completion.passed`, `completion.repair` |
| Other control plane | `driver.spawned`, `foreman.applied`, `node.cancelled`, `node.deferred`, `node.failed`, `node.malformed`, `operator.message`, `repair.requested`, `tick.error`, `worktree.created` |

## Per-run counts

Wall duration is the elapsed timestamp span from the first to last event in the run, so paused time is included. Median task duration is the median worker attempt duration, paired by node and launch/finish order; it includes planner/reviewer/repair worker attempts because events do not provide a task-only duration field. Review findings are material findings stated in `review.completed` details.

| Run | Tasks | Accepted / validated tasks | Worker attempts | Retries | Escalations | Validator failures | Review rounds (rejections; findings) | Provider failovers | Wall duration | Median attempt duration |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `run-20260922T200659Z-5b8a73` | 1 | 0 | 7 | 0 | 1 | 2 | 0 (0; 0) | 2 | 1d 17m | 101.5 s |
| `run-20260923T200037Z-a1e3c0` | 0 | 0 | 3 | 0 | 0 | 0 | 0 (0; 0) | 1 | 23.5 min | 76.4 s |
| `run-20260923T202405Z-5e4d75` | 3 | 2 | 22 | 3 | 2 | 5 | 4 (3; 8) | 4 | 6d 21h 47m | 66.5 s |
| `run-20260924T133405Z-dc8cf4` | 3 | 3 | 16 | 4 | 5 | 9 | 3 (0; 0) | 0 | 53.2 min | 55.4 s |
| `run-20260924T143653Z-746b90` | 4 | 4 | 13 | 0 | 1 | 1 | 5 (2; 2) | 2 | 30.3 min | 89.2 s |
| `run-20260930T181109Z-d9a9d8` | 7 | 1 | 25 | 1 | 10 | 10 | 4 (3; 5) | 0 | 3h 33m | 68.5 s |
| **Total / aggregate** | **18** | **10** | **86** | **8** | **19** | **27** | **16 (8; 15)** | **9** | — | — |

Totals/rates use all six eligible runs: **0.44 retries per task** (8/18); **1.06 escalations per task** (19/18); **1.50 validator failures per task** (27/18); **1.60 review rounds per accepted task** (16/10); **0.80 review rejections per accepted task** (8/10); **0.50 provider failovers per task** (9/18). Across 16 completed reviews, 8 (50%) requested changes, with 15 material findings. There were 86 worker launches and 86 finishes; the three `worker.reattached` events are not additional attempts.

## Recurring failure reasons

Counts are event counts, not unique tasks. For validation failures, the reason is taken from the quoted literal field/fragment in `detail`; repeated failures are counted each time the event occurred.

| Rank | Reason and quoted event detail | Count |
|---:|---|---:|
| 1 | `detail` contains `project-validation-1=FAIL` | 24 |
| 2 | `detail` contains `project-validation-2=FAIL` | 20 |
| 3 | `node.quota` reason begins `You’ve hit your usage limit. Upgrade to Pro...` | 6 |
| 4 | `detail` says `planner result has no tasks` (`node.malformed`) | 3 |
| 5 | `worker.finished` / `node.process_error` detail says `You're out of usage credits...` | 2 |

The two validation buckets are pipeline labels, and may include repeated reports of the same underlying failure. They are intentionally not presented as distinct root causes.

## Findings

- **27 validator failures** occurred across **18 tasks** (1.50 per task); 24 events named `project-validation-1=FAIL`, making validator failures the most frequent recorded failure category.
- **8 retries** occurred (0.44 per task), and **19 escalations** occurred (1.06 per task); run `run-20260930T181109Z-d9a9d8` alone recorded **10 escalations** for 7 tasks.
- **16 review rounds** served **10 accepted tasks** (1.60 rounds per accepted task); **8 rounds (50%)** requested changes and cited **15 material findings**.
- **9 provider failovers** occurred (0.56 per task); quota events separately occurred **6 times**, and planner output was malformed for missing tasks **3 times**.
- Recorded wall spans ranged from **23.5 minutes to 6 days 21 hours 47 minutes**; the longest span is dominated by paused/resumed history and is not an estimate of active work time. Median worker attempt durations ranged from **55.4 to 101.5 seconds**.
- The audit sample is **6 runs**, not 15, because only 7 run directories were present and the current run was excluded; all numeric totals describe this limited local history.
