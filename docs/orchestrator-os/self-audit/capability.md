# Capability records audit

Snapshot date: 2026-09-30. Source: the 26 `CAP-*.json` files under `projects/personal-agent-os/orchestrator-os/records/capability/`. The capability CLI parser sets the aggregation floor to 0.9 (`src/agent_os/orchestrator/cli.py`, `capability --floor`). Pass/success rate below is `metrics.final_success / metrics.sample_count`, with the recorded `validator_pass_rate` in parentheses. No-sample rates are not applicable. `floor` is the record's `metrics.qualified_at_floor` field; `status` is the record's top-level field.

| ID | Model/provider and task class or capability | Observations | Pass/success rate | Floor / status |
|---|---|---:|---:|---|
| CAP-0439615756 | runtime_feature_audit — codex/gpt-6-luna | 0 | n/a (no samples) | floor=None; status=active |
| CAP-10b44018ba | injection_extraction:instruction_defense — codex/gpt-6-luna | 3 | 3/3 (100.0%) | floor=None; status=active |
| CAP-13cecf9a9a | injection_extraction:incumbent — codex/gpt-6-luna | 3 | 3/3 (100.0%) | floor=None; status=active |
| CAP-1512ae6ebf | research_implementation_classification — codex/gpt-6-luna | 4 | 0/4 (0.0%) | floor=None; status=active |
| CAP-2440b0b8c3 | foreman_planning — foreman-openrouter/openai/gpt-oss-120b | 13 | 7/13 (53.8%) | floor=None; status=active |
| CAP-2a70780d4a | affected_test_selection — codex/gpt-6-luna | 3 | 0/3 (0.0%) | floor=None; status=active |
| CAP-34fc71bce4 | affected_test_selection — deterministic/all-tests@1 | 4 | 0/4 (0.0%) | floor=None; status=active |
| CAP-4c543e5f84 | foreman_planning — codex/model unspecified | 14 | 5/14 (35.7%) | floor=None; status=active |
| CAP-50fd0f0bdd | research_implementation_classification — claude-code/claude-sonnet-5-5 | 3 | 0/3 (0.0%) | floor=None; status=active |
| CAP-5ef3b51406 | injection_extraction:spotlighting — codex/gpt-6-luna | 3 | 3/3 (100.0%) | floor=None; status=active |
| CAP-65014f78e8 | injection_extraction — codex/gpt-6-luna | 6 | 6/6 (100.0%) | floor=None; status=active |
| CAP-671d517810 | research_implementation_classification — claude-code/claude-haiku-4-5-20251001 | 3 | 0/3 (0.0%) | floor=None; status=active |
| CAP-793f8cdfde | research_implementation_classification — claude-code/claude-sonnet-5-5 | 4 | 0/4 (0.0%) | floor=None; status=active |
| CAP-8de825c293 | foreman_planning — foreman-qwen2-5-14b-instruct/Qwen/Qwen2.5-14B-Instruct | 13 | 9/13 (69.2%) | floor=None; status=active |
| CAP-9cff39607a | research_implementation_classification — codex/gpt-6-luna | 3 | 0/3 (0.0%) | floor=None; status=active |
| CAP-a17f98bb20 | foreman_planning — foreman-openrouter/deepseek/deepseek-v4-flash | 37 | 32/37 (86.5%) | floor=None; status=active |
| CAP-a3060acfdd | affected_test_selection — claude-code/claude-sonnet-5-5 | 3 | 0/3 (0.0%) | floor=None; status=active |
| CAP-b1842c430d | cold_start_orientation — claude-code/claude-haiku-4-5-20251001 | 1 | 1/1 (100.0%) | floor=None; status=active |
| CAP-b73ea35b39 | affected_test_selection — claude-code/claude-haiku-4-5-20251001 | 2 | 0/2 (0.0%) | floor=None; status=active |
| CAP-be9d7454fc | research_implementation_classification — claude-code/claude-haiku-4-5-20251001 | 4 | 0/4 (0.0%) | floor=None; status=active |
| CAP-cbe590764c | foreman_planning — codex/gpt-6-astra | 12 | 11/12 (91.7%) | floor=None; status=active |
| CAP-df5d4d6f24 | foreman_planning — foreman-openrouter/qwen/qwen3-32b | 25 | 12/25 (48.0%) | floor=None; status=active |
| CAP-e31c23e956 | foreman_planning — claude-code/claude-opus-5-5 | 18 | 16/18 (88.9%) | floor=None; status=active |
| CAP-e75a3a8167 | foreman_planning — foreman-openrouter/qwen/qwen3-235b-a22b-2507 | 11 | 3/11 (27.3%) | floor=None; status=active |
| CAP-ed2b8df74c | runtime_feature_audit — claude-code/claude-haiku-4-5-20251001 | 1 | 1/1 (100.0%) | floor=None; status=active |
| CAP-fd4207e4a6 | affected_test_selection — deterministic/import-graph@1 | 4 | 0/4 (0.0%) | floor=None; status=active |

## Aggregate counts

Counts use the recorded pass rate compared directly with the CLI's 0.9 floor. For freshness, the newest observation is `provenance.observed_to`; date-only compact timestamps are interpreted as UTC. The 30-day cutoff is 2026-08-31.

- Below 0.9: **19 of 26** records. Records with no observations count below the floor because there is no success evidence.
- Fewer than 5 observations: **17 of 26** records.
- Newest observation older than 30 days before 2026-09-30: **0 of 26** records.

## Findings

- **19/26 records** are below the 0.9 success floor; this includes zero-success records such as CAP-1512ae6ebf (0/4), CAP-2a70780d4a (0/3), CAP-34fc71bce4 (0/4), and CAP-fd4207e4a6 (0/4).
- **17/26 records** have fewer than 5 observations, so their observed rates are based on limited samples; for example, CAP-b1842c430d and CAP-ed2b8df74c each have 1/1 success, while CAP-b73ea35b39 has 0/2.
- **0/26 records** have a newest observation older than the 2026-08-31 cutoff; all records have recent observations on or after 2026-09-28 (or 2026-09-29/30).
- Only **1/26 records**, CAP-cbe590764c (11/12, 91.7%), meets the 0.9 observed-rate floor; CAP-e31c23e956 is close at 16/18 (88.9%), while CAP-a17f98bb20 is 32/37 (86.5%).
- **All 26/26 records** have `qualified_at_floor: null` despite some observed rates at or above 0.9. The table therefore preserves the parser-generated qualification field separately from the computed observed-rate comparison; the sole observed-rate pass is CAP-cbe590764c.
