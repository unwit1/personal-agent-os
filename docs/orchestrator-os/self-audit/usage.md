# Usage report evidence

## Commands

Run with `AGENT_OS_ORCHESTRATOR_HOME=C:\Users\HR.RTEC\GitHub\personal-agent-os\.agent-local\orchestrator`:

1. `python -m agent_os orchestrate usage-report`
2. `python -m agent_os orchestrate usage-report --since 2026-09-16T00:00:00Z`

Both commands completed on 2026-09-30. Both returned `runs_counted=7`, `calls=95`, `exact_calls=85`, `input=24,118,670`, `cache_read=21,808,837`, `cache_write=1,055,595`, and `output=405,137`. Thus both report windows have identical aggregates in the available history. The first report had `since=null`; the second had `since=2026-09-16T00:00:00Z`. Each reported 10 calls without token reports and 0 malformed lines. The CLI output stated `file_error=PermissionError: report not saved`; figures below are transcribed from the completed command outputs.

Token columns reproduce the report fields: provider input, cache read, cache write, and output. Cached total is the estimate `cache_read + cache_write`; it is shown as a derived figure. Calls and exact calls are included to expose token-report coverage.

## Full-history report (`usage-report`)

### By provider/model

| Provider/model | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| claude-code/sonnet | 17 (17) | 9,220,175 | 8,609,265 | 610,478 | 9,219,743 | 145,848 |
| claude-code/opus | 6 (6) | 1,176,067 | 1,012,359 | 163,608 | 1,175,967 | 38,239 |
| claude-code/fable | 2 (2) | 0 | 0 | 0 | 0 | 0 |
| codex/gpt-6-astra | 1 (1) | 546,825 | 507,392 | 0 | 507,392 | 2,636 |
| codex/gpt-6-luna | 50 (41) | 6,427,477 | 5,358,848 | 0 | 5,358,848 | 114,097 |
| claude-code/haiku | 11 (11) | 5,897,939 | 5,615,053 | 281,509 | 5,896,562 | 88,772 |
| codex/gpt-6-sol | 7 (6) | 712,222 | 598,912 | 0 | 598,912 | 13,924 |
| codex/gpt-5.6-terra | 1 (1) | 137,965 | 107,008 | 0 | 107,008 | 1,621 |
| **Total** | **95 (85)** | **24,118,670** | **21,808,837** | **1,055,595** | **22,864,432** | **405,137** |

### By role as reported

| Role | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| planner | 8 (8) | 3,925,095 | 3,620,189 | 237,386 | 3,857,575 | 78,754 |
| implementer (worker) | 52 (47) | 8,216,851 | 7,045,438 | 101,702 | 7,147,140 | 144,675 |
| reviewer | 20 (17) | 5,396,630 | 4,901,283 | 463,730 | 5,365,013 | 104,127 |
| repairer (other) | 7 (5) | 3,810,006 | 3,662,254 | 115,683 | 3,777,937 | 40,679 |
| test_author (other) | 8 (8) | 2,770,088 | 2,579,673 | 137,094 | 2,716,767 | 36,902 |

### By capability tier

| Tier | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| balanced | 23 (23) | 9,945,977 | 9,213,169 | 610,478 | 9,823,647 | 160,293 |
| reasoning | 8 (7) | 1,300,452 | 1,114,375 | 163,608 | 1,277,983 | 39,339 |
| frontier | 3 (3) | 546,825 | 507,392 | 0 | 507,392 | 2,636 |
| fast | 61 (52) | 12,325,416 | 10,973,901 | 281,509 | 11,255,410 | 202,869 |

## Since 2026-09-16 report

### By provider/model

| Provider/model | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| claude-code/sonnet | 17 (17) | 9,220,175 | 8,609,265 | 610,478 | 9,219,743 | 145,848 |
| claude-code/opus | 6 (6) | 1,176,067 | 1,012,359 | 163,608 | 1,175,967 | 38,239 |
| claude-code/fable | 2 (2) | 0 | 0 | 0 | 0 | 0 |
| codex/gpt-6-astra | 1 (1) | 546,825 | 507,392 | 0 | 507,392 | 2,636 |
| codex/gpt-6-luna | 50 (41) | 6,427,477 | 5,358,848 | 0 | 5,358,848 | 114,097 |
| claude-code/haiku | 11 (11) | 5,897,939 | 5,615,053 | 281,509 | 5,896,562 | 88,772 |
| codex/gpt-6-sol | 7 (6) | 712,222 | 598,912 | 0 | 598,912 | 13,924 |
| codex/gpt-5.6-terra | 1 (1) | 137,965 | 107,008 | 0 | 107,008 | 1,621 |
| **Total** | **95 (85)** | **24,118,670** | **21,808,837** | **1,055,595** | **22,864,432** | **405,137** |

### By role as reported

| Role | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| planner | 8 (8) | 3,925,095 | 3,620,189 | 237,386 | 3,857,575 | 78,754 |
| implementer (worker) | 52 (47) | 8,216,851 | 7,045,438 | 101,702 | 7,147,140 | 144,675 |
| reviewer | 20 (17) | 5,396,630 | 4,901,283 | 463,730 | 5,365,013 | 104,127 |
| repairer (other) | 7 (5) | 3,810,006 | 3,662,254 | 115,683 | 3,777,937 | 40,679 |
| test_author (other) | 8 (8) | 2,770,088 | 2,579,673 | 137,094 | 2,716,767 | 36,902 |

### By capability tier

| Tier | Calls (exact) | Input | Cache read | Cache write | Cached total (estimate) | Output |
|---|---:|---:|---:|---:|---:|---:|
| balanced | 23 (23) | 9,945,977 | 9,213,169 | 610,478 | 9,823,647 | 160,293 |
| reasoning | 8 (7) | 1,300,452 | 1,114,375 | 163,608 | 1,277,983 | 39,339 |
| frontier | 3 (3) | 546,825 | 507,392 | 0 | 507,392 | 2,636 |
| fast | 61 (52) | 12,325,416 | 10,973,901 | 281,509 | 11,255,410 | 202,869 |

## Shares and task counts

Shares use `input + output` as total tokens, since those are the report's input/output token measures. Cache read/write are components of input accounting and are not added again.

| Window | Reviewer share (estimate) | Worker share (estimate) | Tokens per validated/accepted task |
|---|---|---|---|
| Full history | `(5,396,630 + 104,127) / (24,118,670 + 405,137) = 5,500,757 / 24,523,807 = 22.43%` | `(8,216,851 + 144,675) / 24,523,807 = 8,361,526 / 24,523,807 = 34.09%` | not available from usage-report |
| Since 2026-09-16 | `(5,396,630 + 104,127) / (24,118,670 + 405,137) = 5,500,757 / 24,523,807 = 22.43%` | `(8,216,851 + 144,675) / 24,523,807 = 8,361,526 / 24,523,807 = 34.09%` | not available from usage-report |

The usage-report output provides call/run counts, but no validated or accepted task count. Therefore tokens per validated/accepted task are not available from usage-report for either window.

## Findings

- Both windows cover the same 7 runs and 95 calls, with 85 exact-token calls and 10 unreported calls; the since-filter does not change the returned totals.
- The reviewer used 5,500,757 input-plus-output tokens (22.43% estimate) versus the worker's 8,361,526 (34.09% estimate), a difference of 11.66 percentage points (34.09% - 22.43%).
- Cache-read plus cache-write volume was 22,864,432 tokens (estimate: 21,808,837 + 1,055,595), compared with 405,137 output tokens.
- Fast tier recorded 61 calls (52 exact) and 12,325,416 input tokens; balanced tier recorded 23 calls (23 exact) and 9,945,977 input tokens.
- `codex/gpt-6-luna` accounted for 50 calls (41 exact), 6,427,477 input tokens, and 114,097 output tokens; these figures are the same in both command windows.
