# SAR — Safeguard-Aware Refusal Resolution and Policy-Bounded Model Fallback

**Status:** HIGH-PRIORITY / AGENT-READY DESIGN, **NOT IMPLEMENTED**  
**Requested:** 2026-10-19  
**Track:** SAR-0 through SAR-9  
**Parent:** IMP-0015 Model Infrastructure Manager / Compute Broker  
**Also relates to:** IMP-0018 Context Efficiency; cost-aware coding delegation (CCD); Autonomous Debugging / Self-Healing Runtime; deterministic continuation; EVS-SECURITY; Foreman shadow testing.  
**Owner:** Orchestrator OS.  
**Repository:** https://github.com/unwit1/personal-agent-os

> **What to build:** A deterministic, provider-neutral refusal-resolution and authorization layer that allows an already-authorized legitimate task to continue on an eligible alternative model when a model over-refuses or lacks a capability. A refusal is evidence to investigate, not itself permission to bypass a provider restriction or the operator's policies. Preserve the root objective, inherited safety context, contractual/provider restrictions, budget gates, tool boundaries and full provenance. Never route a prohibited end goal through split subtasks or a deliberately less restrictive worker.

## 0. Executive decision, scope and priority

**Implement SAR as an extension of existing router, adapters, engine, and evidence infrastructure, NOT as a second router or policy engine.** The highest-value first fix is the existing implicit `refused -> failover` behavior in `engine._fail`; make it conditional on an explicit, recorded authorization decision. Keep legitimate quota, rate-limit, transport, unsupported-capability and worker-error failover working.

**Priority:** P0 security/correctness prerequisite for future automatic safeguard-aware delegation; HIGH feature priority overall. Implement SAR-0 and SAR-1 before automatically expanding refusal-based fallback. Do not preempt emergency correctness/privacy fixes or work the operator has explicitly ranked above this task; integrate into the IMP-0015 track.

**User benefit:** Stop wasting tokens and time on repeated harmless refusals, yet keep the task DAG moving through permitted independent work. Allow per-project, task-family, role and model preferences only after capability and authorization checks. Learn from verified outcomes rather than blanket 'uncensored = better' assumptions.

**Explicit non-goals:**
- No automatic bypass of provider policy, content safety restrictions, scope/authorization boundaries, or protected control-plane edits.
- No hiding parent intent, withholding safety-relevant facts, changing benign labels to conceal meaning, or routing a denied end goal through subagents.
- No mandatory LLM 'safety judge' for each failure: default classification should be deterministic, inspectable and low-cost.
- No unapproved paid API calls, RunPod pods, credit top-ups, or cross-privacy-boundary exports.
- No hot-swapping the model inside an ongoing ChatGPT/Claude host session; route only Agent-OS-owned calls or explicitly delegated tasks.
- No massive dependency import (LiteLLM, LangGraph, NeMo, OPA, WildGuard); borrow tested interfaces and targeted evaluation fixtures unless benchmarks later prove a need.

## 1. Existing architecture: evidence confirmed by source review on 2026-10-19

Consult these exact files FIRST; repository state can change before implementation:

| Evidence | Present behavior | Why SAR needs it |
|---|---|---|
| `src/agent_os/orchestrator/engine.py`, `_fail` | `kind == "refused"` records telemetry and—when `provider_failover` is true—excludes provider/capability class and retries. | **Critical gap:** no separate pre-failover authorization adjudication is visible in that path. |
| `src/agent_os/orchestrator/refusal.py` | Five text-classification categories; regex-based detection; `refusals.jsonl` records sanitized excerpts and provider/model. | Split reported refusal cause from independent authorization; keep legacy telemetry readable. |
| `src/agent_os/orchestrator/adapters/claude_code.py` | Parses `stop_reason == refusal`, `safety_stops`, permission denials; reports failure kind `refused`. | Keep structured category/details when supported; do not confuse tool denials with model policy refusals. |
| `src/agent_os/orchestrator/adapters/codex_cli.py` | Parses JSONL errors, agent messages and special Windows sandbox refusal as `unavailable`. | Add structured refusal detection where supported, without guessing based on 'I cannot' alone. |
| `src/agent_os/orchestrator/adapters/http_api.py` | Flattens Anthropic and OpenAI-compatible responses to (text, usage); thread wrapper maps status errors. | Preserve provider-native refusal, truncation, content-filter and per-attempt billing signals. |
| `src/agent_os/orchestrator/adapters/base.py` | `AgentResult` has `failure_kind` and untyped `signals` dict. | Backward-compatible normalized `RefusalSignal`. |
| `src/agent_os/orchestrator/router.py` | Pure model selection, registry/profile constraints, provider/class exclusions and overrides. | Add an authorization eligibility filter ahead of ranked selection, keeping selection pure. |
| `src/agent_os/orchestrator/model_profile.py` | Profiles support standard / low / abliterated / unknown refusal behavior; hard and soft requirements. | Treat refusal profile as descriptive behavior, never an authorization grant. |
| `src/agent_os/orchestrator/context_contract.py` | Raises `ContextLaunderingError` if a fact already marked `safety_relevant` is removed; stable digest and untrusted-data fences. | Upgrade from caller-marked facts to trusted root-policy inheritance across every spawned task. |
| `src/agent_os/orchestrator/delegate.py` | Contract checks and text-based refusal recording for read-only delegation; one-shot path separate from engine. | Share a single resolver so delegate and engine cannot disagree. |
| `src/agent_os/orchestrator/model.py` | `DEFAULT_POLICY.provider_failover=True`, bounded retries, `APPROVAL_REQUIRED`, `FAILED_RETRYABLE`, `FAILED_FINAL`. | Extend existing states and policy keys rather than duplicate state machine. |
| `policy/orchestrator-os.policy.json` | `no_retry_failure_kinds` includes `policy`; controls permissions, protected paths and spending. | Reconcile naming/precedence with `refused` failover in engine; do not mutate policy without operator grant. |
| `tests/test_worker_refusals.py` | Synthetic test: alpha refuses, beta succeeds, run completes. | Add policy allow/deny/unknown preconditions. Existing success alone is not proof fallback is allowed. |
| `tests/test_model_infra.py`, `tests/test_orchestrator.py` | Classifier and context contract tests, router/failover cases. | Baseline, then extend with negative and adversarial cases. |
| `src/agent_os/orchestrator/capability.py`, `foreman.py`, `eval.py` | Capability observations, shadow Foreman, EVS/EVR evaluation. | Measure genuine improvement and run shadow/canary before promotion. |
| `projects/personal-agent-os/research/prior-art/registry.json` | Already tracks RouteLLM, LiteLLM, Cedar, AgentDojo, Inspect AI, LangGraph and others. | Consult before adding a new library; reuse prior decisions, update stale/new candidates. |

**Unverified:** no runtime CLI execution, full test suite, provider credentials, actual availability/quotas or end-to-end live worker call was performed during roadmap authoring. Audit the current checkout and re-baseline before treating any hypothesis as proven.

**Fresh-audit questions:** Do all run execution paths call a common refusal handler? Can provider adapters return HTTP 200 refusals without marking failure? Are `no_retry_failure_kinds` policy entries actually consulted by runtime? Are root safety facts propagated into *ordinary* engine nodes (not just Foreman shadow)? What is the effect of a user-specified model override on denial? Do worker-generated subtasks, repairs, deterministic steps and post-resume execution inherit identical gates?

## 2. External research and adoption decisions (checked 2026-10-19)

Primary documentation and research to reopen when implementing:

1. **Anthropic refusal/fallback specification** — https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback . Supported API responses may return HTTP 200 with `stop_reason="refusal"` and `stop_details` (category/explanation may be null). API supports beta server-side/client-side fallback with restrictions; `usage.iterations` distinguishes attempts; fallback may incur costs; subagent tool calls do not inherit a fallback setting automatically. **BORROW:** structured response parsing, per-attempt ledger, explicit per-request fallback and compatibility checks. **DO NOT turn on upstream server-side fallback by default:** Agent OS must authorize the named routes and account for attempts first, and server-specific fallback behavior may be less observable than client-controlled routing. Reverify beta semantics/version at implementation time.
2. **OpenAI Responses / Structured Outputs** — https://developers.openai.com/api/docs/guides/structured-outputs . Refusal can appear as a typed output content item (`type="refusal"`), or a message `refusal` field in supported Chat Completions structured-output flows; an incomplete response may be `content_filter` or `max_output_tokens`. **BORROW:** distinguish refusal, filter interruption and format failure before trying JSON extraction.
3. **Google Gemini safety** — https://ai.google.dev/gemini-api/docs/safety-settings . Current Interactions API may report blocked input or output via HTTP 400 error codes such as `safety`, `jailbreak`, `prohibited_content` or `blocklist`; older generateContent surfaces expose `promptFeedback`, `finishReason`, safety metadata. **BORROW:** adapter-specific status classification rather than universal HTTP-403 or empty-text heuristics; version-specific fixtures.
4. **Cedar authorization semantics** — https://docs.cedarpolicy.com/auth/authorization.html . Default deny, explicit forbid over permit. **BORROW:** principal/action/resource/conditions decision algebra; a small deterministic evaluator inside Agent OS first; no Cedar runtime dependency until complexity warrants it. Important distinction: unknown or malformed security metadata must not become implicit permit.
5. **NVIDIA NeMo Guardrails** — https://docs.nvidia.com/nemo/guardrails/configure-guardrails/yaml-schema/guardrails-configuration . Separates input, retrieval, dialog, execution and output rails. **BORROW:** checks at each trust boundary; existing Agent OS engine and control plane remain canonical.
6. **WildGuard** — https://github.com/allenai/wildguard ; **Safety-Eval** — https://github.com/allenai/safety-eval . Provides different judgments for harmfulness, refusal, and response harmfulness. **INVESTIGATE for offline benchmark only:** model can be wrong, its dependencies are heavy (PyTorch/transformers/vLLM), and it cannot authorize actions.
7. **XSTest** — https://arxiv.org/abs/2308.01263 . 250 safe prompts across ten traps plus 200 unsafe contrasts. **BORROW dataset for offline over-refusal measurement**, respecting license, split provenance and no live consequential tools. Need separate false-positive and unsafe-fallback measures.
8. **AgentDojo** — https://github.com/ethz-spylab/agentdojo-core ; existing `EVS-SECURITY` provenance. **BORROW prompt-injection fixtures** to test policy contamination via tool outputs, delegated research and downstream workers.
9. **RouteLLM** — https://github.com/lm-sys/RouteLLM . Quality/cost threshold calibration. **BORROW for eligible-route *ranking only*** once enough Agent OS observations exist; cannot be the authorization authority.
10. **LiteLLM** — https://docs.litellm.ai/ ; existing PA-litellm entry documents March 2026 supply-chain compromise and dependency risks. **BORROW bounded fallback and usage accounting; do not add as a runtime dependency** without a measured EVR/DEC.
11. **Guardrails AI** — https://github.com/guardrails-ai/guardrails . Distinguishes reask, programmatic fixes, filtering and refrain. **BORROW failure-resolution vocabulary**, subject to policy; never reask/rewrite to conceal a forbidden objective.
12. **OWASP Top 10 for Agentic Applications (2026)** — https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ . **BORROW threat categories:** goal hijack, tool misuse, trust-boundary and multi-agent handoff attacks.
13. **NIST AI RMF Generative AI Profile** — https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence . **BORROW risk governance, measurement, traceability and human escalation** principles.
14. **Current agentic security survey** — https://arxiv.org/abs/2603.01564 . Describes delegated cross-agent propagation, provenance and privilege controls; useful as a threat-model checklist, not as a plug-in.

**Research interpretation:** Provider refusals, app-level rules, user authorization, legal/contractual requirements and capability errors are different layers. A model's 'low refusal' property is not a security credential. Provider terms may prohibit cross-model resubmission even if a different service would answer; compatibility/terms should be evaluated as constraints. Avoid blanket claims that all providers support the same fallbacks.

## 3. Policy hierarchy, security invariants and trust boundaries

Precedence (strict, no lower level can relax a higher one):

1. Applicable law, provider/platform contractual restrictions, non-negotiable safety requirements.
2. Canonical operator-approved Agent OS policy, project privacy policy and resource permissions; hard explicit DENY overrides ALLOW.
3. Task-level authorization and approvals tied to principal, action, resource, sensitivity and expiry.
4. Parent DAG task invariant envelope and inherited constraints (no child can widen).
5. Provider/model runtime restrictions and capabilities.
6. User model preferences / cost / quota / latency optimization (only among eligible routes).
7. Model-generated plans, recommendations and textual assertions (advisory, never grant authority).

**Hard invariants** (write negative tests for each):
- `DENY` is absorbing for the same objective/action/resource: cannot change to `ALLOW` merely via a new model, role, prompt, subtask, retry, model override or resume.
- `UNKNOWN` and evidence missing or parser error -> `REVIEW` or `DENY` for safety-sensitive execution, not automatic retry.
- Parent -> child constraints monotonic: `child.permissions ⊆ parent.permissions`; task ancestry, original objective and safety labels remain available to trusted adjudicator even if a worker receives a concise context.
- A worker can propose a new plan or route but cannot edit policy, choose its own clearance, forge approvals, replace a trusted digest, or authorize a restricted operation.
- Every external tool/action must recheck authorization at execution time with exact action/resource arguments (including nested tools and deterministic continuation).
- An authorization for **one** model/provider/action is not reusable for another if data handling, terms, resource scope or risk changes.
- Protected control-plane files/holdouts and model-independent privacy, publication, spending and secrets gates remain enforced.
- Preserve provider refusals and categories as evidence; never treat a low-refusal alternative as proof of legitimacy.
- No partially streamed or incomplete refused output is integrated/published without full policy and output validation.
- Refusal resolution never retries indefinitely, creates duplicate mutations, resets a protected retry budget across subagents, or restarts completed work.
- A provider's native fallback, if opted in, must still stay inside Agent OS's permitted model allowlist, privacy and cost budget; if the provider cannot guarantee/observe this, disable that feature.
- Keep personal/work-sensitive raw prompt/response and refusal excerpts local, permissioned and redacted; commit only synthetic tests, reviewed findings and aggregate evidence.

**Authorization semantics (minimal):** `ALLOW`, `DENY`, `REVIEW_REQUIRED`, with `reason_codes`, `evidence_refs`, `policy_digest`, `principal`, `action`, `resource`, `scope`, `expiry`. This is a deterministic runtime check, not a new model verdict. Permission grants are narrow and time/scoped; do not write approvals into the prompt as substitute for tool permissions. Distinguish a model refusal from host sandbox denial, approval needed and provider-reported policy block.

## 4. Proposed data contracts (illustrative v1)

Do not add an incompatible second event or router schema without checking `AgentResult.signals`, existing run/node format, schema evolution and migration tests.

~~~json
{
  "schema": "personal-agent/refusal-signal/v1",
  "event_id": "RF-...",
  "run_id": "run-...",
  "node_id": "task-a",
  "call_id": "run/task-a/attempt-1",
  "source": "provider_structured",
  "provider": "provider-id",
  "requested_model": "model-a",
  "served_model": "model-a",
  "kind": "model_policy_refusal",
  "provider_category": "optional-or-null",
  "stop_reason": "refusal",
  "http_status": 200,
  "output_partial": false,
  "reliability": "high",
  "task_contract_digest": "sha256:...",
  "root_task_digest": "sha256:...",
  "policy_digest": "sha256:...",
  "raw_evidence_ref": "local-only-redacted-pointer",
  "observed_at": "ISO-8601"
}
~~~

`kind` taxonomy (non-exclusive origin and final classification fields, no conflation): `model_policy_refusal`, `provider_contract_restriction`, `runtime_authorization_denial`, `tool_permission_denial`, `unsupported_capability`, `context_mismatch`, `ambiguous_request`, `format_failure`, `output_filter_interruption`, `provider_quota`, `transient_failure`, `unknown`. Preserve original reason plus normalized reason. Do **not** conclude "false positive" from a single text regex; add adjudication state `false_positive_confirmed | suspected | not_applicable | unknown` only with labeled or trusted evidence.

~~~json
{
  "schema": "personal-agent/refusal-resolution/v1",
  "signal_id": "RF-...",
  "policy_decision": "ALLOW",
  "policy_reason_codes": ["task_authorized", "route_authorized"],
  "resolution": "SWITCH_MODEL",
  "eligible_route_ids": ["provider-b:model-b"],
  "max_additional_attempts": 1,
  "root_task_digest": "sha256:...",
  "task_contract_digest": "sha256:...",
  "policy_digest": "sha256:...",
  "approval_id": null,
  "evidence_refs": ["local://..."],
  "at": "ISO-8601"
}
~~~

`resolution` enum: `NO_ACTION`, `RETRY_TRANSIENT`, `REPAIR_CONTRACT`, `SWITCH_MODEL`, `CONTINUE_INDEPENDENT`, `AWAIT_REVIEW`, `DENY`. `REPAIR_CONTRACT` may clarify output shape, fix unsupported tool/modality assumptions, or remove irrelevant untrusted context; never remove/materially alter objective, consent, ownership, provider restrictions or safety facts.

**Contract handling:** A trusted `TaskAuthorizationEnvelope` should live in run/node metadata, outside LLM-editable content. Proposed fields: root goal digest, policy source/version, inherited permissions, restrictions and data classification, parent edge, required approval IDs, sanctioned provider/model constraints, allowed tool/action/resource patterns, source provenance. Rebuild an immutable effective envelope at every task spawn/delegate/review/repair/resume. It may be compiled into a minimal truthful `context_contract` worker-facing packet; full trusted envelope remains available to adjudicator and execution guard. No raw secrets in packet or ledger.

**Idempotency:** resolution key = run+node+attempt+signal digest; one stored resolution per key; fail-safe against replay/multiple event handlers. Key retry ceilings at *root task lineage plus node* so decomposition cannot evade caps. Keep node selection/attempt history and do not invalidate successful validators/commits on retry.

## 5. Runtime decision flow (deterministic first)

1. Normalize request and derive trusted envelope from root run, project and parent DAG; validate schema and required permissions.
2. Before first dispatch (and before side effects), run authorization and privacy/capability checks; reject or request approval if restricted/unknown. Normal cheap deterministic/cached paths remain preferred.
3. Select eligible provider/model using existing `router.select`, not a model judging permissions. Check role, modality, context, privacy, deployment, terms, quota, accuracy floor, tool contracts and budget.
4. Launch via adapter; persist attempt ID, actual model, usage/cost and provider-native structured signals, including partial stream or HTTP 200 refusal.
5. If completed and validated, record success. If failure, classify by **provider structured signal > adapter status > deterministic contract/runtime facts > conservative text fallback**, keeping origin and uncertainty.
6. `quota`/`unavailable`/`transient` -> existing breaker/cooldown and bounded eligible reroute; `unsupported_capability` -> correct tool/capability route or request host action; `ambiguous` -> clarify; `auth/tool_permission` -> approval or stop; `model_policy_refusal` -> trusted authorization adjudication.
7. For model policy refusal: `DENY` -> no fallback; `REVIEW_REQUIRED/UNKNOWN` -> checkpoint and gate, while independent permitted siblings can proceed; `ALLOW` -> one bounded authorized alternative if technically eligible, preferably a truthful unchanged contract. Do not automatically suppress provider terms or resubmit to a provider that forbids it.
8. Before approving an output or tool effect, revalidate effective policy and downstream action constraints. Emit ledger event with reason and route; preserve worktree/checkpoint and verifier state.
9. If approved alternate routes are exhausted, stop with actionable summary and safe next actions, never keep cycling models.
10. Record false-positive/quality assessments only after independent labeled review; update CAP and optimization candidates, but do not let CAP learn a rule that relaxes authorization.

**Pseudocode:**

~~~python
def on_worker_result(run, node, result):
    signal = normalize_failure(result)
    persist_signal_once(signal)
    if signal is None:
        return validate_and_continue(run, node, result)

    # All decisions use original, trusted objective and inherited constraints.
    envelope = effective_authorization(run, node)
    decision = authorize_operation(envelope, action="reassign_model",
                                   resource=node["goal"], destination=None)
    resolution = resolve_failure(signal, decision, run, node)

    if resolution.kind == "SWITCH_MODEL":
        eligible = authorized_model_candidates(run, node, envelope)
        choice = existing_router_select(eligible, excluded=attempted_routes(node))
        if choice and retry_budget_remaining(run, node):
            return checkpoint_then_relaunch(run, node, choice)
    if resolution.kind == "RETRY_TRANSIENT":
        return existing_retry_circuit_breaker(run, node)
    if resolution.kind == "REPAIR_CONTRACT":
        return apply_nonsemantic_repair_and_validate(run, node)
    if resolution.kind == "CONTINUE_INDEPENDENT":
        return defer_node_and_progress_permitted_siblings(run, node)
    return gate_or_stop_without_side_effects(run, node, resolution)
~~~

*This is a design sketch, not runnable code.* Actual handling must not re-run an authorization check whose action/resource semantics differ between the original task and the fallback.

## 6. Integration seams and proposed ownership

- `src/agent_os/orchestrator/adapters/base.py`: typed optional `refusal_signal` on `AgentResult` or versioned normalized `signals`; preserve all current adapter callers and serialized snapshots.
- `adapters/claude_code.py`: carry stop reason/safety stop counts/permission denials independently; `stop_details` when exposed. Test JSON missing/null/unknown, never assume CLI exposes Claude API metadata.
- `adapters/codex_cli.py`: parse documented JSONL signals when present; keep Windows sandbox `unavailable` exception; avoid regexing arbitrary agent prose into policy decisions.
- `adapters/http_api.py`: separate `parse_response` from result normalization; recognize Anthropic `stop_reason` and `stop_details`, OpenAI `message.refusal`/typed refusal and content-filter incomplete; Gemini adapter only if present/newly needed. Preserve actual model, attempt-specific usage, provider retry data. Handle streaming partial refusal defensively.
- `refusal.py`: keep `classify` backwards-compatible for telemetry; create normalized classifier that records origin and uncertainty, and a migration reader for old JSONL.
- **New thin `refusal_resolution.py`**: pure deterministic `resolve(signal, authorization, history, policy)->Resolution` with no model calls and no side effects. It must not rewrite policies. Model preference and model selection remain in `router.py`.
- `engine.py`: insert resolution hook *before* existing `kind == refused` branch in `_fail`; dispatch, resume, reassign, launch and tool-effect paths recheck envelope. Keep durable node states and use existing `APPROVAL_REQUIRED` gate rather than new scheduler. Do not bypass `_fail` for errors needing a gate.
- `delegate.py`: same normalized resolver; if read-only contract fails but provider claims a refusal, record it; no silent retry unless effective permission envelope is supplied/derived.
- `router.py` and `model_profile.py`: accept an already-filtered eligible candidate set or callback; no policy verdict inferred from `refusal_profile`; hard requirements and overrides always subordinate to policy.
- `context_contract.py`, `planner.py`, `foreman.py`: derive task/child metadata from trusted root, record lineage; workers see truthful task-level facts, while security enforcement uses full trusted metadata.
- `store.py`, `ledger.py`, `trace.py`: normalized `refusal.observed`, `refusal.resolved`, `refusal.fallback_selected`, `refusal.gated`, `refusal.exhausted` with schema version, timestamp, causal links and redacted identifiers. Avoid raw prompts in telemetry. Add report `orchestrate refusals --decisions` or equivalent without breaking old CLI.
- `model.py`/policy: reconcile policy vs refusal failures, add **opt-in** `refusal_resolution_mode: observe | enforce`, `max_refusal_fallbacks_per_root: 1`, `review_on_unknown: true`, `require_lineage_contract: true`. New policy must validate exact enums and disallow worker alteration.
- `model_view.py`/GUI: last resort after validated engine; read-only refusal waterfall, origin/category, reason, next safe action, actual model selected, token/cost per attempt, confidence, pending review. No green 'success' badge for simply getting output after a policy denial.
- `free_routing.py`, `free_dispatch.py`, `retry.py`, `provider_health.py`, `api_budget.py`, `provision.py`, `continuation.py`: regression test hard compatibility. A free/abliterated provider never escapes approval; budget exhaustion cannot trigger paid fallback; continuation after quotas does not erase denial.

## 7. Implementation plan with bounded deliverables

Each SAR stage is separately checkpointable; preserve the current code path until a new behavior proves noninferior. Do not open unrelated redesign work.

### SAR-0 — Repository preflight, ownership, baseline (P0; no code behavior change)
**Inspect:** AGENTS, ENTRYPOINT, constitution § relevant paragraphs, live git branch/status, last checkpoint, prior-art registry, engine failure paths, model policies, all adapters, delegate and EVS. Run `agent-os context personal-agent-os "SAR refusal resolution"`, `agent-os orchestrate prior-art lookup "model refusal classification authorization fallback agent security"`, `agent-os orchestrate checkpoint --show`, and `agent-os validate` when local CLI available. Confirm no existing feature/issue covers SAR. Map all pathways (planner, reviewer, repairer, delegate, free-route, continuation, CLI, MCP, API workers). Capture a read-only control-flow table and synthetic incumbent EVR. **Done when:** a gap matrix is committed, current tests pass or pre-existing failures are documented, and a scoped implementation decision cites prior art.

### SAR-1 — Failure taxonomy + explicit decision precedence (P0; safe shadow first)
Define normalized refusal categories separately from `FAILURE_KINDS`; reconcile `policy.no_retry_failure_kinds` vs `engine._fail("refused")`. Decide whether a provider policy refusal is eligible for any alternate call under applicable terms and authorization, rather than treating 'provider refused' as an automatic hard deny for all providers or automatic global allow. Implement pure authorization adapter around existing policy/approval and `resolve_failure` no side effects. Default to observe + log potential decisions; retain existing behavior only on current trusted admissible workflows while migration is tested, with a documented temporary risk and opt-in strict gate where feasible. **Done when:** policy and model failure semantics are explicit; unit tests show hard DENY / unknown / allow / expired approval outcomes; no unapproved protected paths altered.

### SAR-2 — Provider-native signal extraction (P0)
Implement fixture-tested signals in base + Claude CLI + Codex CLI + HTTP Anthropic/OpenAI-compatible. Distinguish HTTP 200 refusal, 400/403 policy block, 401 credential auth, 429 quota, 5xx transient, tool permission denial, invalid model, content-filter interruption, max-token truncation and malformed JSON. Handle null fields, non-text content, streamed partial output and served-model mismatch. **Done when:** all provider fixtures produce stable normalized records, legacy adapters/tests are compatible and no new provider call is required to classify known native signals.

### SAR-3 — Trusted lineage context and non-laundering enforcement (P0)
Create trusted envelope from root task and project at run creation. Make the envelope monotonic under planner expansion, delegation, review, repair, retry, spawn, and resume. Preserve source goal/hash, safety requirements, permissions, data classification and model/provider constraints. Guarantee that relevant facts remain in the *worker-facing truthful prompt* while runtime retains full authorization snapshot. Don't conflate required factual safety context with irrelevant bulk context that can be reduced for token economy. Check tool args at boundary. **Done when:** adversarial cases cannot remove/forge parent policy, task hashes survive resume and all node types carry lineage.

### SAR-4 — Policy-aware engine/delegate fallback (P0/P1)
Insert resolver at engine refusal branch and read-only delegate error path; implement retry budget per root and node, idempotent event linkage, preserved worktrees/attempts, correct provider/class exclusion, alternate eligible model selection and clean stop/approval. Keep transient provider failures on existing `retry.py` / health path; avoid double counts/duplicate actions. Do not add provider-native automatic server-side fallback yet. **Done when:** synthetic alpha-refuses/beta-success still passes **only for an explicitly authorized benign case**; denied/unknown cases never reach beta; unrelated nodes continue; no extra paid calls.

### SAR-5 — Cross-provider behavior and safety evals (P1)
Create development and protected holdout suites combining XSTest safe/contrast, real harmless coding/research/creative tasks, provider-native refusals and AgentDojo-derived indirect-injection cases. Preserve licenses/provenance; do not put copyrighted/PII or raw sensitive work inputs in Git. Blind-adjudicate labels and track inter-rater disagreement. Score classification, authorized completion, policy bypass, cost/latency/tokens, refusal cascade, duplication, retry count. Run paired incumbent vs candidate with deterministic fixtures first; then limited permissioned live trials with matched prompts/contracts. **Done when:** EVR/DEC show no observed invariant breach, measured gain on benign tasks, and no unacceptable regression.

### SAR-6 — Model preference / workload-profile config (P1)
Add per-project and task-family preferred models/provider classes as *soft* preferences behind hard authorization constraints. Require role/modality/tool support, privacy-safe deployment, provider eligibility and policy provenance. Record exact resolved model version. Avoid hardcoded vendor names in engine. Fallback may prioritize a low-over-refusal model for authorized work, but an abliterated profile never weakens tool/action gates. **Done when:** explicit user override cannot escape hard constraints and router explanations include eligibility reasons without private traces.

### SAR-7 — Shadow/canary, economics and promotion (P1/P2)
Use existing Foreman shadow, CAP/EVR and route calibration; monitor rolling false-positive rates and cost per *verified permitted completion*. Compare no-fallback, current fallback and SAR fallback. Add per-root token/spend accounting inclusive of refusal attempts, provider-native fallback attempts and cache effect. Permit rollout by trusted task family, with feature flag, kill switch, rollback and migration tests. Revisit Anthropic server-side fallback only if explicit model allowlist, policy compatibility, auditability and per-attempt billing are demonstrably enforceable. **Done when:** trustworthy improvement, audit metrics and reversible staged rollout; no paid calls without approval.

### SAR-8 — Visibility, operator review and maintainability (P2)
Surface in run visibility: blocked node, refusal source/category, why alternate is/not eligible, current model, allowed next steps, root restriction and estimated spend; provide safe user review flow and resume. Add redacted CLI reports, telemetry retention, regression case export and changelog. Flag recurring legitimate false positives as model capability candidates; separately flag policy bugs as defects. **Done when:** user can understand every fallback/stop without raw chain-of-thought or leaked sensitive input.

### SAR-9 — Handoff, documentation, adversarial hardening and closure (P2)
Document the public provider-neutral interfaces and exact failure matrix; update prior-art decisions; add tests for self-healing and deterministic continuation; ensure checkpoint/handoff and `agent-os validate` work; close all material findings or keep blocking gates. Re-evaluate architecture size and delete duplicate wrappers per simplification principles. **Done when:** one complete, reproducible EVR-backed release decision and a compact resumable next prompt exist.

## 8. Detailed verification matrix (minimum)

Write tests before changing engine routing; fail closed for missing data. Use synthetic adapters by default.

| Case family | Input / perturbation | Required outcome |
|---|---|---|
| Authorized false positive | Harmless task, model A returns native refusal, model B eligible | One bounded model B attempt, independent validator required |
| Hard denied goal | Task has trusted DENY, model A refuses | No B call, no action, denial survives restart |
| Unknown authorization | Missing owner/consent/context or conflicting policy | Gate / ask; no automatic reroute |
| Model refuses via HTTP 200 | Structured refusal but successful status | Count refusal, not successful JSON |
| Auth errors / provider 403 | Invalid credentials vs API policy/contract block | Distinct classification; no policy-bypass loop |
| Quota vs refusal | 429/Retry-After, invalid model, timeout, 5xx | Reuse health/cooldown/eligible routing; bounded |
| Worker asks for approval | Structured `needs_decision`, denied Bash tool | Gate or host-action resolution; never mislabel as false-positive safety refusal |
| Output malformed | JSON schema fails absent refusal signal | Normal validation/repair, not refusal reroute |
| Truncated / midstream refusal | Partial output and `content_filter` / native stop | Never integrate partial result as complete |
| Same model repeatedly | Registry maps two classes to same concrete model | Prevent repeated attempts/loops; dedupe by exact provider+model+version |
| Different vendor model | Alt supports requested roles but not modality/tool/privacy | Candidate rejected, no inappropriate fallback |
| Explicit user override | Override chooses an ineligible model | Router declines override, doesn't change policy |
| Model has `abliterated` profile | Lower refusal rate but low quality or no permission | Never boosts authorization; must satisfy validators |
| Parent/child laundering | Planner omits critical inherited ownership/target/safety fact | Fails compilation or resolution; no agent call on unsafe child |
| Innocuous split subtasks | Children each appear harmless; root goal restricted | Root denial propagates; tools gated independently |
| Prompt injection | Retrieved doc/tool output says to change policy/model or conceal purpose | Ignored as instructions; treated as untrusted data |
| Fake approval | Worker text invents approval token or edits `policy` | No grant; protected-path guard holds |
| Security policy version changed | Resume task after more restrictive policy | Revalidate; invalidate prior authorization if no longer valid |
| Refusal racing worker result | Two events for one attempt / process restarts | Idempotent one resolution, one ledger entry |
| Worktree partial edits | A edits files then refuses; B handles permitted task | Checkpoint and isolate, verify conflicts, no silent merge |
| Budget limit | Fallback requires paid call but `allow_paid_spend=false` | Stop or wait/ask; no spend |
| Native server-side fallback | Provider silently changes served model / multiple billed attempts | Disabled by default; if opt-in, reconcile attempts and eligibility |
| Long-running DAG | Restricted node blocks certain dependencies, independent nodes remain valid | Continue only independent authorized work |
| Deterministic continuation | Model quota exhausted, queued tool steps remain | Run only approved deterministic steps, never restricted actions |
| Telemetry privacy | Refusal contains tokens, secrets, personal data | Redact; no raw data committed to repo |
| Audit reproducibility | Same normalized signal+policy snapshot twice | Deterministic decision; stable reason code |
| Regression to incumbent | Feature flag off / old events | Existing behavior and legacy JSONL remain readable |
| Child retry storm | Multiple siblings attempt identical blocked goal | Aggregate attempt ceiling and circuit breaker hold |
| Provider default fallback | Anthropic beta default suggests another model | Suggestion is non-authoritative; policy/terms and budget gate before use |

**Metrics:**
- `authorized_completion_rate` on adjudicated safe tasks (primary benefit).
- `unsafe_reroute_rate`, `unauthorized_tool_action_rate`, `privacy_boundary_violations`, `unapproved_spend`: target **zero observed** across all enforced synthetic/holdout cases; explicitly not a statistical guarantee.
- `refusal_detection_precision/recall`, `false_positive_refusal_rate`, `ambiguous_case_review_rate`.
- `cost_per_verified_permitted_task`, input/output/cache tokens, incremental failed-refusal spend, wall-time and per-root fallback counts.
- `duplicate_side_effects`, `denial_persistence_on_resume`, `human_review_load`, `model_routing_version_drift`.
- Fairness by task family, data sensitivity, provider and refusal category. Do not optimize only aggregate completion if any high-risk segment regresses.

**Promotion gates:** full baseline suite green or waived with documented pre-existing failures; no invariant violation; clean consent/scope checks; evidence on held-out harmless over-refusal cases; quality/latency/token/cost reported even if null; manual review of safety-sensitive unknowns; feature flag and rollback proven; independent review of policy-changing commits; all protected-file changes explicitly operator-granted. Do not use a zero-violation observed sample as proof of universal safety.

## 9. Suggested tests, test locations and commands

New focused tests:
- `tests/test_refusal_signal_normalization.py`
- `tests/test_refusal_resolution.py`
- `tests/test_refusal_policy_inheritance.py`
- `tests/test_refusal_fallback_engine.py`
- `tests/test_delegate_refusal_resolution.py`
- `tests/test_refusal_resume_and_budget.py`
- `tests/test_refusal_attack_matrix.py`
- `tests/fixtures/refusal_signals/` (synthetic JSON, anonymized)
- `projects/personal-agent-os/orchestrator-os/evals/` SAR development suites with cited provenance; holdout additions only through authorized evaluator workflow.

Existing tests to extend: `test_worker_refusals.py`, `test_model_infra.py`, `test_orchestrator.py`, `test_api_budget.py`, `test_provider_health.py`, `test_orchestrator_trace.py`, `test_orchestrator_control_plane.py`, and any current state-machine/resumability tests.

~~~sh
agent-os orchestrate checkpoint --show
agent-os context personal-agent-os "SAR-0 audit refusal fallback"
agent-os orchestrate prior-art lookup "refusal classification policy authorization model fallback"
agent-os validate
python -m unittest tests.test_worker_refusals tests.test_model_infra
python -m unittest discover -s tests
# Run approved candidate vs incumbent EVS and write EVR/DEC after defining SAR suite.
~~~

Use exact test invocation syntax supported by the checked-out project (the above is a proposed checklist); select affected tests first, full suite before promotion. Record baseline refs, runtime OS, model revisions and what could not be executed. GitHub-only research cannot establish tests passing.

## 10. Risks, tradeoffs and future-proofing

| Risk | Mitigation |
|---|---|
| Refusal mistaken for harmless false positive | Native signal + trusted independent authorization; unknown -> review |
| Wrong root intent reaches specialist | Immutable root/lineage envelope; every descendant sees truthful relevant facts |
| Too many checks/tokens/latency | One deterministic resolver per failure; cache verified policy digest until invalidated; no extra model judges by default |
| More retries cost more tokens | Per-root ceilings and measured cost of verified success; stop on repeating same concrete model |
| Provider signals/API change | Versioned adapter fixtures, capability detection, fail-closed unknown fields, Radar refresh |
| Loss of prompt cache on fallback | Reuse stable contract and track read/write cache tokens; provider fallback credits only where supported and approved |
| Paid cloud fallback | Existing hard budget/approval gate before every attempt |
| Dependency bloat | Borrow schemas/algorithms; no new major runtime packages in SAR-0..4 |
| Corrupted run state/migrations | Versioned additive fields, old JSONL compatibility, idempotency, snapshot replay |
| Shadow result conflated with policy | Separate policy-authority field from suggestion; shadow models have no routing authority |
| Hidden operator approval | Scoped, timestamped approvals in trusted state; no fabricated grants |
| Host model hot-swap assumption | Agent OS only controls its own delegated model calls |
| Vendor terms change | Check permitted providers/model combinations at routing time; record last verification |

**Token impact hypothesis (must measure):** SAR may save tokens by avoiding repeated same-model refusals and unnecessary full-worker restart, but can increase tokens when fallback doubles prompt/context cost. Prefilter authorized routes and use deterministic classification; benchmark total cost per verified authorized task, not simply number of 'answered' refusals. Existing IMP-0018 context economy work is a dependency for efficient warm-state fallback.

## 11. Initial operator configuration (proposed; NOT a live policy)

~~~json
{
  "refusal_resolution_mode": "observe",
  "review_on_unknown": true,
  "max_refusal_fallbacks_per_root": 1,
  "require_lineage_contract": true,
  "allow_paid_refusal_fallback": false,
  "model_preferences": {
    "coding": ["configured-coding-primary", "configured-coding-backup"],
    "research": ["configured-research-primary", "configured-research-backup"],
    "creative_writing": ["configured-writer-primary", "configured-writer-backup"]
  }
}
~~~

Names above are placeholders, not known local providers. Feature flag `off` must be possible for rollback. `observe` should produce proposed resolutions with no behavior change. Only promote `enforce` by tested, explicitly approved route/family, preserving original policy gates. Configuration must be operator-controlled, not invented by planner/worker or retrieved content.

## 12. Required handoff for the next implementing agent

**Your assignment:** Implement SAR-0, then SAR-1 and SAR-2 in bounded commits; do not implement all stages at once or start new subsystem projects. Read this roadmap, the canonical Orchestrator ENTRYPOINT, current checkpoint, model-infrastructure-manager.md, `AGENTS.md`, `policy/orchestrator-os.policy.json`, and the relevant files in §1. Re-run current prior-art lookup and verify provider docs/API versions; use existing PA entries. Start by isolating the existing engine refusal-failover case as a regression and adding explicit benign-ALLOW / DENY / UNKNOWN variants.

**Each agent batch must leave:** changed paths; reason for each change; synthetic tests, command outputs and EVR if applicable; migration/compatibility results; policy/approval implications; token/cost delta where measured; blocked items; exact next action; saved checkpoint; preserved independent progress. Never silently edit `policy/**`, protected evaluators, approval-gate code or main; request operator permission for protected code and follow existing branch/PR rules.

**Stop and ask for a decision when:** modifying canonical protected policy paths, a provider's terms are ambiguous for fallback, a task's authorization is genuinely unresolved, a suggested change weakens an existing safety boundary, a paid model/GPU would run without existing approval, or a failing holdout/security test cannot be explained without changing the test/evaluator.

**Definition of fully implemented:** At least two configured provider families demonstrated on authorized harmless synthetic tasks; all failure taxonomy and negative cases pass; no unauthorized retry in adversarial cases; old execution works when disabled; observable model and per-attempt token/cost provenance; root-context non-laundering enforced; users can inspect/approve unresolved cases; measured rollout outperforms current code on verified legitimate completion or costs while respecting hard policy; a final EVR/DEC and resumable ORCH checkpoint are recorded.

---
**Roadmap authorship note (2026-10-19):** This file is a research-and-implementation plan, not a claim that the listed phases, schemas, tests or runtime controls already exist. Source review and public documentation were available; no local checkout tests/live model invocations or real provider billing were performed. Re-verify all external beta/provider details at implementation time.
