# Model services integration: handoff (2026-10-12)

Worktree: `C:\Users\HR.RTEC\GitHub\pao-orchestrator`, branch `orchestrator-os/session-foreman`, base `76d806027`. All changes are **uncommitted** working-tree edits: nothing has been committed, pushed or merged. They were assembled from these Orchestrator run branches:
- `agent-os/ms-foundation-20261012/integration`
- `agent-os/ms-services-20261012/integration`
- `agent-os/ms-catalog-claude-20261012/integration`
- the `catalog-data` and `docs-roadmap` node branches of the last run, applied by hand. Both ended `blocked_on_host` (sandbox temp dirs) and were never merged, although their nodes say integrated; see IMP-0057.

## Implemented and verified
- `endpoints.py` path styles (auto/root/append_v1). Legacy bases are unchanged.
- `model_profile` billing and privacy blocks. `is_paid` is conservative: unknown overage counts as paid.
- Claude Code coding-plan bridge: `options.env` and `options.secret_env`. The operator's `ANTHROPIC_*` credentials are stripped whenever a bridge is configured.
- `model_services.py` with the `orchestrate services list|show|validate|discover|add|bridge` CLI.
- GUI Model services panel.
- `foreman use registered`.
- `catalog.json`: 28 services, 20 models, 9 media; 0 validation errors.
- Docs: `docs/model-services.md`, `docs/model-infrastructure.md`, the roadmap section, and `COMMANDS.md`.
- Tests: the 188 model-services tests pass. The full suite has 15 failures and errors that are identical on base `76d806027`: portability, registry, RTEC applicant, surfaces and validation tests, all environment-specific. `agent.py validate` has one error, which is identical on base (the `job-applicant-dashboard` context file is missing).

## Unverified
- No live vendor call with a key was made. Discovery and presets are verified with mocked transports only.
- The catalog `unknown` fields and `contradicted` findings. Chutes's dollar-value caps rest on secondary sources only.
- Batch G (media) is thin: 1-3 sources per record.
- No published abliterated-vs-base comparison exists for the Huihui variants, so `vs_base` is null everywhere.

## Deferred
- Paid provisioning and auto-recharge (never done without operator approval).
- Multimedia adapters (image, ASR, TTS, embeddings, rerank).
- Usage metering against allowances.
- Abliterated-vs-base eval runs (`eval-queue`).
- The improvement candidates found during this work: IMP-0056 (goal truncation), IMP-0057 (false PASSED/COMPLETE), IMP-0058 (same-provider review fallback), IMP-0059 (worker input dirs).

## 2026-10-14 session: NanoGPT live, headroom routing, research
Still uncommitted. Added to the same worktree:
- **Live NanoGPT key** at `secrets://nanogpt/subscription` (keyring). Registered `nanogpt-subscription` (planner role only, cost 1.0) as the session foreman, with backups Claude, then Codex. Eval-only candidates are registered as `nanogpt-ev-*` at cost 50, so they never win routing; disable or remove them once the foreman is chosen.
- **`headroom.py`**: proactive allowance state from Codex session logs, the Claude `rate_limit_event` (Haiku probe, at most every 20 minutes), and the NanoGPT `/usage` endpoint. The router skips exhausted plans and scales cost for tight (x3) and expiring (x0.6) plans. Wired into the engine, the foreman gate and `delegate`. CLI: `orchestrate headroom [--refresh]`.
- **`sensitive_data` run policy** (true, false or auto): no node, foreman included, may use a third-party host or a per-token API. "auto" covers the HR GUI, RTEC-HR, applicant, overtime, scan, capture and message-archive repositories.
- **`http_api` fix**: a 429 that reports model overload is now `unavailable`, not `quota`, so it no longer benches the plan for an hour.
- **`model_research.py`**: `orchestrate services research nanogpt [--family F] [--measure-multiplier MODEL]` writes `nanogpt-fit.json`. Priors are in `nanogpt-priors.json`, and the guide is in `NANOGPT-ROUTING.md`.
- Tests: `test_headroom.py`, `test_model_research.py`, and an overload case in `test_orchestrator_api_retry.py`. The full suite has only the pre-existing environment failures.

## Resume
1. Review the diff (`git status`, `git diff`) and decide whether to commit; this needs operator authorization.
2. Pick the foreman from the eval table in `NANOGPT-ROUTING.md` (operator choice: abliterated or strongest), then disable the `nanogpt-ev-*` entries.
3. Before NanoGPT takes `inline` delegations, add a sensitive-data guard to `work_delegate`.
