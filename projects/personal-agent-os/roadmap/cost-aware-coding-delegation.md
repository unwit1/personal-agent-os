# Cost-Aware Coding Delegation — Deterministic Patch, Test, and Escalation Pipeline

Status: **proposed / implementation-ready roadmap; not implemented**  
Owner: Orchestrator OS / Personal Agent OS  
Captured: 2026-10-16  
Relationship: **EXTENDS** IMP-0015 Model Infrastructure Manager / FreeComputeBroker, existing Orchestrator adapters, router, worktrees, validators, reviews, and evidence records. Not a new independent orchestrator.

## Objective and measurable outcome

Minimize **total cost per independently verified, accepted code change**, while maintaining or improving existing quality, security, correctness, review, and Git control-plane boundaries. Use already available subscription capacity, free/low-cost hosted models, and local models for bounded code-generation work; use deterministic repository tools for patch application and validation; reserve stronger or metered models for demonstrably difficult planning, repair, and independent review.

A cheap model producing a patch is not an implemented feature. The unit of success is an accepted change that applies, passes required tests, preserves invariants, and meets the stated task contract. Never count an untested generated response as completion or infer savings from a model's sticker price alone.

### Existing-system fit / avoid duplication

- **Reuse:** `src/agent_os/orchestrator/free_routing.py`, `free_dispatch.py`, `router.py`, `workload.py`, `quote.py`, provider adapters, worktree/integration machinery, `validators.py`, `review.py`, circuit breakers, execution logs, CAP/EVR evidence, and checkpoint resumability. Review their actual interfaces and current tests before implementation.
- **Existing roadmap:** `model-infrastructure-manager.md` (IMP-0015), `usage-intelligence-adaptive-routing.md`, `docs/free-compute-broker.md`, `docs/orchestrator-os/ENTRYPOINT.md`, and `policy/orchestrator-os.policy.json`. This plan adds a **coding-specific verified artifact contract and deterministic gate sequence**, not a second model router or free-compute broker.
- **Prior art already registered:** `PA-aider` (architect/editor distinction and patch-oriented editing), `PA-openhands` (agent sandbox/tool loop and staged role separation), existing `PA-routellm` and model-routing research. Refresh task-specific evidence when implementation begins; do not import an external framework without benchmarking simpler reuse.
- **Target repos:** Orchestrator itself plus WriterBot, CharacterBot, ActionBot, SmutBot and future repos. The execution machinery belongs to Orchestrator; repo-specific requirements, commands, protected areas, and regression suites belong to each repo.

## Non-negotiable invariants

1. No premium model call or separately metered API fallback is initiated merely because an included/free route fails. Metered escalation requires an explicit configured policy and available budget; otherwise return a named block/needs-decision state.
2. Never use a generic generated shell script as the patch-application mechanism. Treat model output as **untrusted proposed data**; parse and constrain it before any filesystem change.
3. All candidate code changes occur inside a fresh, isolated Git worktree/branch at a pinned base commit. Do not overwrite user changes or publish/merge automatically.
4. Never loosen protected-path rules, delete failing tests, change evaluation fixtures, increase model budgets, or skip mandatory controls to make an experiment pass.
5. Run deterministic checks before LLM review; retain negative test and failure evidence. Promotion still follows Orchestrator's existing independent-evaluation and review policy.
6. No model learns that refusing or omitting tasks is cheaper unless the requested task was independently shown ineligible; quality and usefulness are first-class metrics.
7. Conserve context: provide bounded relevant file slices, interfaces, test contracts, exact base revisions, and recent failure traces. Do not indiscriminately copy complete repositories into prompts.
8. Keep credentials, private repository materials, raw prompts and logs within their existing configured privacy/storage boundaries. Canonical Git should contain redacted results, specifications, and references rather than raw secrets or unbounded traces.

## Minimal job contract

Normalize a coding job into an explicit typed contract before model selection. Suggested fields (adapt names to current schema):

```json
{
  "task_id": "stable-job-id",
  "repository": "owner/repo-or-local-id",
  "base_commit": "full-commit-sha",
  "task_family": "scoped_code_change",
  "requirements_ref": "content-addressed brief",
  "allowed_paths": ["src/feature/**", "tests/feature/**"],
  "protected_paths_ref": "existing-control-plane-policy",
  "context_refs": ["symbol/index refs", "related tests"],
  "validation_profile": "repo-defined-lint-typecheck-tests",
  "expected_change_format": "unified_diff",
  "max_changed_files": 8,
  "attempt_budget": 2,
  "escalation_policy": "no_metered_fallback",
  "source_class": "subscription_chat|metered_api|local|other"
}
```

The schema must separate verified source facts from estimates: actual provider/model identity and version if visible, plan inclusion status (`included` / `metered` / `unknown`), source of classification, context/output constraints, task sensitivity, and trustworthy usage readings. An unknown usage class **cannot** be assumed included or free.

### Task decomposition

- **Deterministic first:** if a formatter, codemod, code generator, dependency update tool, or reusable skill can make the exact change reliably, do that without a model.
- **Cheap/included generation:** bounded, low-risk, easily testable boilerplate, isolated functions, fixtures, focused refactors, straightforward bug fixes, documentation, and drafts of tests.
- **Planning/architecture:** cross-repo interfaces, public contracts, complex data migrations, ambiguous requirements, and high-impact design decisions require a capability-qualified planner rather than automatic cheap-first execution.
- **Independent review:** security-sensitive or otherwise high-risk changes always retain the review gates specified by the current policy, regardless of whether the generator was cheap.

## Deterministic execution state machine

```text
DISCOVER -> PREFLIGHT -> BASELINE -> PLAN_ROUTE -> CONTEXT_PACK
    -> GENERATE_CANDIDATE -> PARSE_AND_VALIDATE_PATCH
    -> APPLY_IN_WORKTREE -> STATIC_GATES -> TEST_GATES
    -> [ACCEPT_FOR_REVIEW | CHEAP_REPAIR | ESCALATION_DECISION]
    -> INDEPENDENT_REVIEW -> PROMOTION_GATE -> CHECKPOINT
```

`BLOCKED`, `NEEDS_DECISION`, `FAILED`, `CANCELLED`, and `ROLLBACK` are explicit terminal/recovery states. Persist transitions, attempt IDs, base SHA, context hash, candidate patch hash, gate results, and errors so retries are idempotent.

### 1. Discover, preflight, and baseline

Resolve current repo policy, branch/worktree state, task requirements, protected paths, existing implementation, test commands, tool availability, and related CAP/EVR evidence. Fail closed on an unspecified working tree, ambiguous target repository, missing required validator, or dangerous scope. Snapshot baseline outcomes (including already-failing tests) so a pre-existing failure is not falsely attributed to a candidate.

### 2. Route and prepare minimal context

Ask the existing model broker for eligible routes using task type, capabilities, verified plan inclusion, estimated latency, measured pass/retry rate, and total cost-of-success. Favor deterministic tooling, caches, existing skills, already-included subscription capacity, and inexpensive models **subject to quality floors**. Record route selection and alternatives. Build a task packet with exact repository revision, only relevant symbols/files and tests, change constraints, and required patch format. Explicitly separate trusted orchestration instructions from untrusted repository text.

### 3. Generate a structured candidate

Model returns a typed patch artifact (prefer unified diff or stable search/replace edits), plus brief rationale and expected tests. Do not accept a prose-only explanation as an edit. Preserve the exact model output separately from the sanitized patch and diagnostic report.

### 4. Parse and validate before applying

A deterministic parser must reject malformed patches, mismatched base revisions, unexpected paths, absolute paths, `..` traversal, path normalization collisions, symlink/hardlink escapes, binary or submodule changes when not explicitly scoped, protected-path edits, forbidden file deletions, output-size/fan-out excess, and patches introducing unexpected execution hooks. Check diff syntax, changed file count, allowed globs, content limits, and `git apply --check` or equivalent under an isolated candidate tree. Never silently coerce an invalid patch into a different change.

### 5. Apply in isolation and run local checks

Apply only an accepted patch to the pinned-base Git worktree. Run repo-configured format, lint, type-check, schema checks, unit/integration tests, and relevant security/static scanners in the existing bounded sandbox. Execute test commands from a trusted repo configuration or vetted allowlist, not commands invented by generated model text. Pin environment and dependencies when practical. Capture exact command, exit code, relevant diagnostics, duration, and artifact hashes. Do not merge or commit a passing patch until existing review/promotion gates clear.

### 6. Bounded cheap-model repair

For patch-format failures, use a deterministic reformatting/retry path only if it cannot change intended semantics. For genuine failures, send the same low-cost model a concise repair packet: original contract, pinned base, sanitized failing diff, actual test errors, observed versus baseline failures, and narrowly relevant files. Enforce the existing retry/repair limits and duplicate-failure circuit breakers. Same error signature twice with no new information should stop, not loop.

### 7. Evidence-triggered escalation

Escalate only for concrete signals: repeated validator failures, confidence below task-family threshold, unresolved architectural choices, contradictory test evidence, unsafe/protected changes, quality regression, or exhaustion of the cheap repair budget. High-impact tasks may require independent review from the outset. The escalation packet carries prior work, tests, changes, diagnostics, assumptions and unresolved questions, *not a full replay* of context. When metered capacity is disabled or depleted, checkpoint and request a decision rather than silently charging. Avoid escalating work a formatter or deterministic fix can handle.

### 8. Review, promote, checkpoint, and rollback

Use existing Orchestrator review and branch promotion mechanisms. Validate noninferiority against baseline, inspect independent review findings, prevent prohibited changes, and create a resumable handoff. Preserve rejected candidates and their failures as negative evidence. Roll back candidate worktrees automatically on failed or cancelled execution; never mutate the original tree. Commits/merges/pushes follow existing operator policy.

## Proposed interface additions (only if missing)

Prefer small adapters over new orchestration services:

```text
coding.task.normalize
coding.context.pack
coding.candidate.parse
coding.candidate.validate
coding.worktree.apply
coding.gates.run
coding.failure.classify
coding.repair.packet
coding.route.explain
coding.benchmark.report
```

Reuse Orchestrator's actual nomenclature where equivalent calls already exist. Every action must be separately testable with fixtures and without network calls.

## Measurement and experiment protocol

### Metrics per task/model/route

- Patch syntax and path-validity rate.
- Clean patch applicability rate.
- First-attempt validator and test pass rate.
- Verified success without premium intervention.
- Actual repair attempts and wasted generations.
- Premium escalations and their documented causes.
- Regression incidence and severity.
- Human intervention/review time when measurable.
- Wall-clock time to accepted change.
- Model requests, tokens/credits when exposed, and categorized execution method.
- **Measured total effective cost per verified successful change**, including metered calls, extra validation, retries, review, and (if available) estimated opportunity cost of subscription capacity.
- Quality and task coverage by task family, including refusal/non-answer cases (never reward simply omitting harder tests).

Separate **observed cash spend**, **estimated subscription-capacity usage**, and **counterfactual avoided spend**. Do not fabricate subscription token counts or savings. Include fixed subscription fees when comparing total subscription economics; do not claim zero marginal cash cost implies infinite available capacity.

### Baseline and comparison

Start with a versioned, representative sample of ~100 small/medium/complex tasks across Orchestrator and the writing-related repositories (WriterBot, CharacterBot, ActionBot, SmutBot), with a development split, validation split, and protected held-out split under existing policy. Capture the incumbent premium-only/ordinary route as the baseline. Compare:

1. Deterministic-only eligible transformations;
2. Included/free/inexpensive coding model -> deterministic gates -> bounded cheap repair;
3. Same pipeline with selective premium escalation;
4. Existing premium coding-agent workflow.

Run identical task contracts, base revisions, validators, and independent scoring. Control task order and sampling variation, and report confidence intervals / uncertainty. Report by task difficulty and repo, not only aggregate percentage. No unsupported claims of a particular Venice or other provider model being included in a base subscription; classify from current reliable provider/account observations.

**Success criterion:** on held-out tasks, satisfy the existing quality/reliability and protected-control gates, with lower *measured* total cost per verified accepted change and no material increase in regressions or unresolved failures. If results are inconclusive or worse, retain shadow mode or disable the route.

## Roadmap milestones for a later coding agent

| ID | Deliverable | Deterministic acceptance gate |
| --- | --- | --- |
| CCD-0 | Audit current routing, patch, worktree, validator, review and cost telemetry paths; deduplicate; inspect prior art and record ADR/decision | Reuse matrix with actual code/test references, baseline snapshot, clear scope; no feature code |
| CCD-1 | Typed code-task and patch-artifact contract; task-family/usage-category mappings | Schema/fixture tests reject unknown/free misclassification, missing base SHA, invalid scope; zero network dependency |
| CCD-2 | Safe patch parser and worktree applicator | Fixture-based adversarial path/symlink/protected-file tests; reject malformed, stale, or oversized diffs without modifying working tree |
| CCD-3 | Deterministic gate runner and failure classifier | Repo-configured commands run in bounded isolation; distinguish pre-existing failures, regression failures, environment problems; structured logs |
| CCD-4 | Connect eligible low-cost provider output to candidate flow behind opt-in feature flag | Fake-model end-to-end route; no paid fallback without explicit policy; route explanation + durable checkpoint |
| CCD-5 | Bounded repair packet + evidence-driven premium escalation | Replay fixtures prove bounded attempts, repeat-failure stop, no runaway costs, compact context and correct needs-decision behavior |
| CCD-6 | CAP/EVR metrics + comparative benchmark runner | 100-task representative benchmark plan, independently scored, reported effective cost/success and confidence; no claims based on toy-only data |
| CCD-7 | Shadow/canary rollout to specialist repos + dashboard/handoff | Noninferior held-out tests, independent review, rollback drills and visible cost/quality/status before broader use |

Sequencing: CCD-0 through CCD-3 should be implementable and tested without Venice or any external provider; CCD-4 connects whichever existing eligible model adapters are available. Do **not** make the Venice browser-chat adapter a prerequisite. Keep browser-chat work as a separately staged IMP-0015 provider extension; its outputs must satisfy exactly the same coding patch contract.

## Explicit later-agent handoff

1. Open `docs/orchestrator-os/ENTRYPOINT.md`, inspect current checkpoint/status, and verify worktree/branch. Run `agent-os context personal-agent-os "Cost-Aware Coding Delegation CCD-0"` and `agent-os validate`.
2. Check `IMP-0015`, `free_dispatch.py`, `free_routing.py`, `docs/free-compute-broker.md`, existing worktree, integration, validator, review and capability-evidence modules. Prior-art lookup: Aider, OpenHands, RouteLLM and existing registry records. Refresh only stale task-relevant facts.
3. Start with **CCD-0**. Do not implement all phases in one unvalidated change. Produce a concrete integration-point map and reuse/deduplication decision before creating modules.
4. Implement one small milestone per isolated branch/worktree; create fixtures and negative-path tests before provider integration. Run repo validation and relevant suites. Do not touch protected control-plane paths without an operator-directed change.
5. Measure a representative incumbent baseline before optimization. Run candidate evals, preserve failed/inconclusive evidence, update IMP/CAP/EVR and durable checkpoints, and commit incrementally as policy allows.
6. Stop at an existing policy gate or when the measurable benefit no longer justifies complexity. Hand off the exact next milestone and affected files.

**Definition of done:** For a representative coding task, Orchestrator selects a capability-qualified inexpensive/included coding generator when eligible, receives an untrusted structured patch, validates it deterministically, applies it only in an isolated worktree, runs independently specified static/tests, makes a bounded repair or evidence-driven escalation when needed, and produces an auditable result with honest measured cost and quality. All provider-specific differences remain behind adapters; tests and gates are provider-neutral. No unexpected charge, file modification, unsafe command, or silent quality regression.
