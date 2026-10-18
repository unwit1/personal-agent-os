# Agent handoff — Start Orchestrator Audit Remediation (OAR-2026-10-18)

**Priority:** immediate high-value reliability program. **State:** roadmap captured, implementation not started.  
**Audit baseline:** `main` at `c2b23ea3e59273d503248061f1710799676abd05` (2026-10-17). The current checkout may be newer; do not rebase historical claims onto current code without reinspection.

## Paste into an authorized coding/orchestration agent

> Work autonomously in `unwit1/personal-agent-os` on the **OAR-2026-10-18 Orchestrator reliability/efficiency audit remediation program**.
>
> Start by reading `AGENTS.md`, `policy/CANONICAL_AGENT_POLICY.md`, `docs/orchestrator-os/ENTRYPOINT.md`, `projects/personal-agent-os/roadmap/orchestrator-audit-remediation-2026-10-18.md` and `projects/personal-agent-os/roadmap/orchestrator-audit-remediation-tracker.json`. Reconcile the actual current `main` SHA and existing IMP-0015/18/19/22, P1.2A, CCD and LH-01 work before changes; inspect only source paths needed for the first ticket. Do not assume every October 18 source observation remains true.
>
> **Immediate assignment: OAR-00.** Diagnose the failing Oct 17 GitHub Actions run `39010082397` where the private Ingester Engine checkout returned `Not Found` and prevented all core tests. Create an isolated worktree/feature branch. First reproduce and capture current CI behavior and a minimal fixture; then separate mandatory standalone core verification from private integration tests so core always executes and reports real failure even without private repository access. Do not log or reveal private deploy keys, weaken PR secret boundaries, silently skip the core suite or make secrets available to untrusted PRs. Avoid changing external repo permissions without explicit owner approval. Verify with a failure-injection test and supported CI/platform matrix. If the private key is missing and only an operator can supply it, finish the core split, mark private integration `blocked` with a precise actionable reason, and move on to the next safe package.
>
> After OAR-00, start OAR-01: run a new repeatable test baseline on the current SHA, classify all failed/slow/flaky/environment-sensitive modules without suppressing them, and record redacted command/exit/environment evidence. Then work through the DAG in the tracker: protect operator commands under concurrent drivers (OAR-02), nonblocking deterministic execution (03), safe cache reuse (04), truthful final verification (05), single-probe breakers (06), gap-free event cursors (07), scoped history/privacy (08), statistical integrity (09), shadow routing (10), pre-execution publication protection (11), self-repair evals (12), budgets (13), review cost/defect evals (14), careful engine modularization (15), shared fault/performance eval corpus (16) and staged canary/rollback (17).
>
> **For every ticket**, create a failing regression on the incumbent (or document why it was not reproduced), implement the smallest change preserving APIs and saved runs, test both the fix and adjacent invariants, document exact commands/results, compare costs and quality where relevant, and save a typed evidence record and compact checkpoint. No claim of "fixed" based on code review alone. Maintain current independent reviews, protected control plane, approval gates, worktree isolation, privacy, negative-evidence retention and spender controls. Never merge/push to `main` or change protected evaluators/policy without explicit operator approval. No real paid API calls or cloud/GPU provisioning without configured consent and budget. No real public posting, Git pushes, or network exfiltration even for security tests. Use offline fakes.
>
> Keep source, evidence, and task statuses synchronized, but **do not replace** the established Orchestrator active objective/checkpoint with this roadmap until actually starting a run and generating a validated new checkpoint. Avoid unrelated project drift. Work in small testable commits; preserve independent changes; on a blocked item, record why and continue any independent safe work. Check the current `agent-os validate` schema before editing tracked status JSON. Require a trusted review before protected or consequential changes.
>
> **Report after each slice:** OAR ID, branch/commit, files, old failure reproduction, new tests, targeted/full suite results, measured quality/latency/cost with source and uncertainty, security/privacy gates, blockers, rollback, and the next unblocked item. Stop at the existing approval gate rather than bypassing it.

## Fast first-session checklist

1. Inspect status (`git status --short --branch`, `git rev-parse HEAD`), canonical context, current OAR tracker, the 2026-10-17 CI run and `.github/workflows/agent-os-maintenance.yml`.
2. Build a **no-secret, no-network** standalone reproducible environment. Determine whether installed Agent OS imports optional Ingester at test collection time. Separate core-only tests without lying about coverage.
3. Confirm the mandatory core CI job would be red on a deliberate failing core test and still run if the private checkout cannot authenticate. Preserve private integration as explicit independent result.
4. Run `python -m unittest discover -s tests -v` and `python agent.py validate` where dependencies/environments permit; explain every skip/failure and do not report green based on unrun tests.
5. Commit a small OAR-00 branch diff with tests and report; leave `main` unchanged. Continue to OAR-01 if not blocked.

## Related source documents

- [Full high-value remediation specification](orchestrator-audit-remediation-2026-10-18.md)
- [Machine-readable package tracker](orchestrator-audit-remediation-tracker.json)
- [Master priority roadmap](master-priority-roadmap.md)
- [September 30 self-audit — historical](../../../docs/orchestrator-os/self-audit.md)
- [October 17 GitHub Actions run](https://github.com/unwit1/personal-agent-os/actions/runs/39010082397)
- [Canonical Orchestrator entrypoint](../../../docs/orchestrator-os/ENTRYPOINT.md)

**Definition of success:** real red-to-green evidence on the current SHA, no regressions in safety/quality gates, new evaluations that expose the failure modes, measurable total task-efficiency improvement where optimization is claimed, and a resumable documented next action.
