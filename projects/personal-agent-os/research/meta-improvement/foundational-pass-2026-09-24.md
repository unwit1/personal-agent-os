# Meta-Improvement Engine — Foundational Research Pass 1

Research ID: `MIR-2026-09-24-FOUNDATION-01`  
As of: 2026-09-24  
Status: foundational synthesis; architecture research, not implementation authorization

## Executive conclusion

The strongest architecture is **not a recursively self-modifying agent**. It is a **controlled improvement control plane** wrapped around Agent OS.

Models should be allowed to observe, question, research, propose hypotheses, generate candidate changes, produce tests, and analyze results. They should **not** be the authority that decides their own changes are safe or successful. Promotion should instead be governed by independent evidence, deterministic policy, versioned evaluations, isolated execution, explicit rollback, provenance, and post-deployment monitoring.

The core engineering objective is therefore:

> Turn Agent OS improvement from a sequence of persuasive model opinions into an auditable experimental science.

A second conclusion is equally important: much of the required foundation already exists inside Personal Agent OS. Git-backed canonical state, local/private derived state, resumable ingestion ledgers, staged workflows, capability-class routing, validation-driven escalation, isolated worktrees, reviewer/repair loops, selective context retrieval, telemetry, and candidate/promotion patterns should be extended. Creating a second orchestration framework, second candidate system, second memory stack, or second telemetry store would violate the simplification objective.

The missing capability is a **unified causal evidence chain**:

```text
runtime event / source / user correction / ecosystem change
    -> observation
    -> diagnosed problem or successful pattern
    -> claim/finding
    -> improvement candidate
    -> hypothesis
    -> baseline
    -> experiment
    -> evaluation run
    -> decision
    -> implementation
    -> shadow/canary rollout
    -> verified outcome
    -> canonical knowledge / skill / policy / code
    -> monitoring
    -> later supersession, rollback, or retirement
```

Every arrow should be recoverable by a future model.

---

# 1. State of the Art

## 1.1 Agent architecture

Current production guidance converges on a useful principle: **start with the smallest architecture that works, add agency only where it produces measurable value**. Framework ecosystems expose similar primitives—agents, tools, handoffs/manager patterns, workflows, sessions/memory, guardrails, tracing—but the frameworks themselves change quickly.

Important ecosystem observations as of 2026-09-24:

- OpenAI's Agents SDK is now feature-complete/maintenance-oriented and OpenAI recommends its newer managed Agents API for new applications. Agent Builder and the hosted Evals platform are already on deprecation paths.
- Microsoft AutoGen is in maintenance mode and Microsoft Agent Framework 1.0 is its production successor.
- Google ADK, Microsoft Agent Framework, OpenAI agent runtimes, LangGraph-style workflows, and other frameworks increasingly separate flexible agent reasoning from explicit workflow/state machinery.
- MCP 2026-07-28 has moved its core toward stateless, cacheable, ordinary HTTP semantics and moved long-running tasks into an extension.
- A2A 1.0.0 provides a separate interoperability layer for agent-to-agent task exchange.

**Implication for Agent OS:** do not select one current agent framework as the architecture. Define provider/framework-neutral contracts and use frameworks as replaceable adapters.

## 1.2 Multi-agent systems

Multi-agent architectures can materially improve breadth-first research and workloads with genuinely independent subtasks. Anthropic's production research system reports strong internal gains for breadth-heavy research, but also reports major token multipliers and explicitly warns that tightly dependent tasks are less suitable.

Therefore:

- Multi-agent is an execution strategy, not a default.
- The router should require evidence of parallelizable work before fan-out.
- The orchestrator should impose fan-out budgets and deduplicate delegated objectives.
- Research breadth, independent review, adversarial review, and genuinely separable implementation work are good candidates.
- Sequential code changes sharing one fragile state are often better handled by one owner plus bounded reviewers.

## 1.3 Durable execution

Long-running agent systems inherit distributed-systems problems: retries, process death, partial side effects, rate limits, stale state, external changes, and expensive replay.

Temporal's recent agent work is useful not because Agent OS should immediately adopt Temporal, but because it clearly separates two concepts:

1. deterministic workflow/orchestration state;
2. nondeterministic model/tool activities whose outputs become recorded history.

That separation enables exact recovery and replay. Agent OS already has a lighter version through ingestion ledgers and staged workflows. The near-term task is to define the same guarantees explicitly—checkpoint semantics, idempotency, side-effect recording, replayability, and version migration—before deciding whether an external durable-workflow engine is justified.

## 1.4 Evaluation

Modern agent evaluation is moving from single-answer grading toward **trace-, state-, and task-level evaluation**.

Useful patterns include:

- inspect traces first to identify failure mechanisms;
- convert important failures into repeatable cases;
- separate component metrics from end-to-end outcome metrics;
- keep historical real-task replay;
- test stateful tool use rather than isolated textual answers;
- run adversarial and interruption/resumption scenarios;
- use model graders only as one evidence source.

A major current warning is provider churn: OpenAI's Evals platform is scheduled to shut down on 2026-11-30. Agent OS therefore needs a local/provider-neutral eval format even if it exports runs into provider tools.

## 1.5 Retrieval and memory

RAG research shows that end-to-end answer scores hide very different failure mechanisms. Retrieval quality, context precision, context recall, answer faithfulness, synthesis quality, temporal correctness, abstention, and update behavior should be diagnosable separately.

Long-term-memory work such as LongMemEval shows that memory quality requires more than “remember everything.” Key abilities include:

- accurate extraction;
- multi-session reasoning;
- temporal reasoning;
- updating previously true information;
- knowing when information is absent;
- avoiding stale or contradictory memory.

For Agent OS, memory should be considered a versioned evidence system, not a bag of summaries.

## 1.6 Context engineering

Context is a computational resource. Larger context windows do not remove the cost of:

- irrelevant retrieval;
- duplicated context;
- stale instructions;
- conflicting memories;
- tool-schema overhead;
- attention dilution;
- provider token cost;
- slower processing.

Agent OS already budgets context. The missing step is **context utility measurement**: identify what was retrieved, what survived packing, what was actually used, and whether removing it changes task success.

## 1.7 Model routing

RouteLLM and FrugalGPT establish the broad case for learned/cascade routing: tasks have heterogeneous difficulty, model cost differs substantially, and routing can improve cost-quality tradeoffs.

But a personal Agent OS has an advantage generic routers lack: it can benchmark models on the user's actual workload distribution.

The long-term router should use:

- eligibility constraints first;
- task-family evidence second;
- expected cost/latency optimization third;
- escalation on validator/evidence failure.

A single generic “intelligence index” should remain a fallback prior, not the final routing objective.

## 1.8 Self-improvement

“Self-improvement” covers mechanisms with very different evidence and risk:

### Low-risk, practical now
- failure mining;
- test generation;
- benchmark expansion;
- prompt/tool-description variants evaluated against fixtures;
- routing optimization;
- caching/indexing;
- deterministic replacement of repeated model work;
- context pruning;
- code profiling;
- dependency/security updates through normal software review;
- skill extraction from repeated successful workflows.

### Useful, but only with strong eval gates
- automatic prompt optimization;
- model-generated refactoring;
- automatic architecture candidates;
- synthetic eval/training data;
- learned routing;
- active-learning review queues;
- model-generated tool-schema changes.

### High-risk / later
- unsupervised continual fine-tuning on personal interaction traces;
- reinforcement loops whose reward is mostly model-generated;
- autonomous security-policy modification;
- autonomous privilege expansion;
- unconstrained self-modification.

Research on self-correction is especially cautionary: intrinsic self-reflection can improve some tasks, but critical surveys and negative results show it can also entrench or introduce errors. Reliable external feedback dramatically changes the picture.

**Rule:** reflection can propose; verification must come from elsewhere.

## 1.9 Security

The security frontier is shifting from “does the model follow the prompt?” to “can the architecture remain safe when the model does not?”

AgentDojo demonstrates that tool-using agents face realistic indirect prompt-injection attacks. CaMeL demonstrates a stronger design direction: preserve trusted control flow separately from untrusted data and constrain tool/data flow using capabilities.

Authorization systems such as Cedar/OPA add a critical non-LLM pattern: the application asks a deterministic policy engine whether principal P may perform action A on resource R in context C. The model supplies proposed intent; it does not supply the authorization decision.

## 1.10 Proactivity and HCI

Decades of interruption research and newer proactive-assistant studies converge on another control problem: the value of an intervention must exceed its interruption cost.

Proactivity should therefore be treated as **expected-utility decision making**, not “generate more suggestions.”

---

# 2. Failure Landscape

The following taxonomy should become canonical and machine-readable.

## 2.1 Reasoning and epistemic failures

- hallucinated fact;
- unsupported inference;
- false certainty;
- stale fact treated as current;
- contradiction ignored;
- source scope misapplied;
- source quality not considered;
- model self-critique reinforces original error;
- evaluator shares the same blind spot as generator;
- missing abstention;
- ambiguous requirement silently guessed.

## 2.2 Planning failures

- wrong objective inferred;
- correct objective but wrong decomposition;
- overplanning;
- premature implementation;
- missing prerequisite;
- circular dependency;
- plan too brittle for changing state;
- agent continues after sufficient evidence;
- uncontrolled fan-out;
- duplicate subagent work;
- inappropriate sequential/parallel choice.

## 2.3 Tool-use failures

- wrong tool;
- correct tool with wrong arguments;
- unnecessary tool calls;
- tool result ignored/misread;
- side effect repeated after retry;
- partial side effect not recorded;
- untrusted tool output treated as instruction;
- permission assumed rather than checked;
- tool schema too vague;
- tool schema too verbose and context-expensive.

## 2.4 Retrieval/context failures

- relevant evidence not retrieved;
- irrelevant context crowds out useful context;
- duplicate snippets;
- over-retrieval;
- stale result;
- wrong domain scope;
- retrieval from a lower-authority source when canonical exists;
- summary loses a critical constraint;
- summary accumulates an old error;
- context exceeds useful token budget;
- tool catalog/schema overhead dominates useful task context.

## 2.5 Memory failures

- memory pollution;
- one-off observation promoted as durable fact;
- user statement conflated with model inference;
- fact stored without provenance;
- later correction overwrites history destructively;
- conflicting identities/entities merged;
- same entity split unnecessarily;
- sensitive information crosses domain boundary;
- stale preference kept indefinitely;
- failed forgetting/deletion semantics.

## 2.6 Orchestration/distributed-systems failures

- process interruption loses progress;
- checkpoint too coarse;
- retry repeats external effect;
- worker races;
- stale worktree;
- conflicting writes;
- dead/stranded claim;
- dependency completes but blocked task does not wake;
- provider outage causes cascading failure;
- nondeterministic replay;
- schema/version incompatibility during resume.

## 2.7 Evaluation failures

- benchmark not representative;
- benchmark leakage/contamination;
- overfitting to golden set;
- grader bias;
- position bias;
- verbosity/style mistaken for correctness;
- correlated graders treated as independent votes;
- aggregate score hides critical regression;
- test misses harmful unnecessary actions;
- test fixture no longer reflects current workflow;
- optimizing the metric harms actual user utility.

## 2.8 Improvement-process failures

- candidate explosion;
- every observation becomes backlog;
- duplicate recommendations under different wording;
- research never converts into experiments;
- experiments never convert into decisions;
- “improvement” has no baseline;
- benefits measured but costs ignored;
- local metric improves while global UX declines;
- no post-deployment check;
- failed experiment is forgotten;
- successful experiment never generalized;
- system optimizes itself more than it helps the user.

## 2.9 Proactivity failures

- interruption at a bad moment;
- redundant reminders;
- obvious suggestion;
- irrelevant “helpfulness”;
- repeated dismissed suggestion;
- failure to surface urgent dependency;
- too many clarification questions;
- system acts when it should queue;
- system queues when it should act;
- notification confidence not calibrated.

## 2.10 Security failures

- prompt injection;
- indirect prompt injection;
- poisoned memory;
- poisoned research source;
- tool-chain exfiltration;
- privilege escalation;
- confused deputy;
- agent impersonates user authorization;
- cross-domain data leakage;
- secret enters trace/log;
- unsafe generated code escapes sandbox;
- dependency/supply-chain compromise;
- agent weakens tests/policy to improve score;
- audit evidence deleted or rewritten.

A failure should not disappear into a log. It should be classifiable into one or more durable lessons, tests, hypotheses, or monitoring rules.

---

# 3. Agent OS Gap Analysis

## 3.1 Existing strengths to preserve

Repository inspection shows Agent OS already has:

- Git as canonical reviewed state;
- local rebuildable indexes;
- local/private raw-data boundaries;
- structured candidates and explicit promotion;
- an improvement record system with deterministic deduplication;
- restart-safe ingestion ledgers;
- staged, validator-driven workflows;
- provider-neutral capability classes;
- routing telemetry and model evidence;
- isolated worktrees for multi-agent coding;
- independent review and repair loops;
- run visibility;
- selective profile/context retrieval;
- context-budget pruning;
- privacy gates;
- project and roadmap structure.

These are unusually aligned with the proposed meta-improvement architecture.

## 3.2 Material gaps

1. **Improvement provenance is too shallow.** Current improvement records cannot natively express the full observation→hypothesis→experiment→eval→decision→rollout chain.
2. **No unified eval registry.** Tests exist, but there is no universal dataset/suite/case/grader/run schema.
3. **No failure/success registry.** Telemetry exists; durable cross-run diagnosis and clustering do not.
4. **No formal experiment registry.**
5. **No research claim/evidence registry.**
6. **No explicit constructive-challenge scheduler/policy.**
7. **No system-wide proactivity intervention policy with measured outcomes.**
8. **No simplification/deletion lifecycle.**
9. **No component/capability/dependency graph sufficient to reason about redundancy.**
10. **No provider-neutral deterministic authorization plane covering every consequential action.**
11. **No explicit untrusted-data taint/control-flow model.**
12. **Model routing is not yet fully task-specific and uncertainty-aware.**
13. **Context telemetry does not yet measure contribution/utility.**
14. **No benchmark contamination/holdout governance.**
15. **No research radar with impact/noise measurement.**
16. **No compact future-model inheritance bundle that links all current evidence and active learning state.**
17. **Existing durability is strong but does not yet expose general event-history branching/replay semantics.**

## 3.3 What should not be rebuilt

Do **not** create:

- another canonical memory database;
- another project registry;
- another orchestration engine solely for meta-improvement;
- a separate security prompt;
- a second telemetry system;
- a separate “critic agent” that runs on every turn;
- a separate improvement backlog unrelated to current IMP records;
- a separate knowledge engine for research.

The Meta-Improvement Engine should be a control plane that composes current primitives.

---

# 4. Self-Improvement Architecture

## 4.1 Control-plane model

Use seven layers.

### Layer A — Immutable policy boundary

Owns:

- authorization;
- secrets;
- data-domain policy;
- approval classes;
- spending limits;
- sandbox constraints;
- audit retention;
- which parts of the system may modify which other parts.

Models can propose policy changes. They cannot activate them.

### Layer B — Observation plane

Inputs:

- structured run events;
- test/eval results;
- failures/retries;
- user corrections;
- user dismissals/acceptances;
- cost/latency;
- retrieval/context stats;
- security events;
- dependency/tool/provider changes;
- research-radar events;
- project/commitment state;
- manual observations.

Prefer OpenTelemetry-compatible semantics while preserving the compact internal ledger.

### Layer C — Evidence and diagnosis plane

Transforms events into:

- observations;
- failure records;
- success patterns;
- findings;
- claims;
- contradictions;
- uncertainty;
- candidate root causes.

No implementation happens here.

### Layer D — Opportunity plane

Generators include:

- failure miner;
- success miner;
- simplification auditor;
- context optimizer;
- routing optimizer;
- tool/prompt optimizer;
- constructive challenger;
- proactive opportunity detector;
- research radar;
- skill miner;
- automation miner.

Outputs become deduplicated improvement candidates.

### Layer E — Experiment/evaluation plane

For a candidate, require:

- hypothesis;
- target metric;
- guardrail metrics;
- baseline;
- treatment;
- representative cases;
- holdout;
- rollback;
- risk class;
- isolation method;
- budget.

Then run the smallest experiment capable of resolving the uncertainty.

### Layer F — Change and release plane

Reuse Orchestrator OS:

- branch/worktree;
- implementation;
- deterministic tests;
- evaluator/reviewer;
- artifact diff;
- shadow run;
- canary/feature flag;
- promotion or rejection.

### Layer G — Monitoring/learning plane

After promotion:

- monitor target and guardrail metrics;
- detect regression;
- compare actual to expected benefit;
- rollback if required;
- create learning record;
- update capability/router evidence;
- update documentation;
- schedule re-review.

## 4.2 State model

Do not overload one status enum with the entire scientific process. Keep related objects:

- `OBS` observation;
- `CLM` claim;
- `FND` finding;
- `FAIL` failure;
- `SUC` success pattern;
- `IMP` improvement candidate;
- `HYP` hypothesis;
- `EXP` experiment;
- `EVC` eval case;
- `EVS` eval suite;
- `EVR` eval run;
- `DEC`/ADR decision;
- `REL` rollout/release;
- `CAP` capability;
- `RAD` radar item;
- `Q` unresolved question.

Current `IMP-####` records should remain the actionable projection rather than becoming a giant universal record.

## 4.3 Promotion gates

A candidate may advance when:

- problem recurs or impact justifies one-off action;
- evidence meets minimum confidence for its risk;
- no existing candidate already covers it;
- a plausible simpler alternative has been considered;
- success is measurable;
- regression dimensions are named;
- rollback is possible.

A change may become canonical when:

- mandatory deterministic tests pass;
- target eval improves or meets threshold;
- guardrail metrics do not regress beyond tolerance;
- security/privacy policy passes;
- independent grader/human review is used where deterministic evaluation is insufficient;
- the result survives holdout/shadow/canary appropriate to risk;
- documentation/provenance are complete.

---

# 5. Constructive Challenge Architecture

The challenge engine should be **event-triggered and budgeted**, not constantly antagonistic.

## 5.1 Trigger conditions

Challenge when at least one is true:

- decision is expensive;
- decision is hard to reverse;
- a new subsystem/tool/provider is being introduced;
- workflow has recurring friction;
- same manual task repeats;
- architecture duplicates existing capability;
- user's stated solution appears more complex than the goal;
- assumption conflicts with evidence;
- constraint may be obsolete;
- there is substantial opportunity cost;
- security/privacy surface expands;
- long-term maintenance burden is created.

## 5.2 Challenge record

Each challenge should contain:

- inferred objective;
- proposed approach;
- assumption under review;
- whether the assumption is explicit/inferred;
- evidence for concern;
- simpler alternative;
- automated alternative;
- delete/do-nothing alternative;
- cost/risk/reversibility;
- what experiment would decide;
- confidence;
- urgency;
- whether to surface now, queue, digest, or suppress.

## 5.3 Anti-contrarian controls

- Do not challenge stylistic preferences without material consequence.
- Do not repeat a rejected challenge unless evidence changes.
- Do not manufacture an alternative merely to create debate.
- Treat “current approach is already appropriate” as a valid result.
- Count interruption cost.
- Prefer one high-value challenge over five weak ones.
- Track whether challenges actually changed outcomes.

The goal is not dissent. The goal is better decisions.

---

# 6. Evaluation Architecture

## 6.1 Evaluation pyramid

### Level 0 — deterministic invariants
Schemas, parsing, permissions, privacy boundaries, idempotency, hashes, file paths, state transitions.

### Level 1 — unit/component tests
Individual router, retriever, memory writer, tool, prompt builder, classifier, candidate deduper.

### Level 2 — diagnostic AI evals
Retrieval recall/precision, faithfulness, extraction, tool selection, argument correctness, contradiction detection, abstention, prompt adherence.

### Level 3 — historical/synthetic task replay
Representative real tasks with sanitized or local-private fixtures.

### Level 4 — stateful integration scenarios
Multi-tool tasks where state changes between actions.

### Level 5 — long-horizon/fault scenarios
Rate limits, tool failure, interruption, process death, stale state, partial completion, provider switching, context compaction.

### Level 6 — adversarial/security
Prompt injection, tool poisoning, malicious retrieved content, privilege escalation, exfiltration, malicious dependencies.

### Level 7 — production shadow/canary
Observe real workload before full promotion.

## 6.2 Dataset governance

Every eval case needs:

- stable ID;
- task family;
- source;
- creation date;
- sensitivity;
- fixture location;
- expected outcome or rubric;
- deterministic checks;
- grader(s);
- applicable model/tool versions;
- whether the case has been used for optimization;
- contamination risk;
- retirement/supersession status.

Split:

- development/training examples;
- validation examples;
- protected holdout;
- periodically refreshed dynamic cases.

Do not let an optimizer see protected holdouts.

## 6.3 Model graders

Use model graders only when deterministic evaluation is insufficient.

Controls:

- randomize A/B order;
- blind model/provider identity;
- use structured rubrics;
- calibrate against human-labeled subset;
- measure judge consistency;
- preserve disagreement;
- allow abstention;
- avoid treating several correlated LLM judges as independent evidence;
- use deterministic checks as anchors;
- audit judge-version drift.

## 6.4 Top-level outcomes

Avoid one composite magic score. Maintain a small number of primary outcomes:

1. **successful task rate**;
2. **user correction/effort burden**;
3. **cost per successful task**;
4. **reliability/resume safety**;
5. **security/privacy policy compliance**.

Diagnostic metrics can include latency, tokens, unnecessary actions/tool calls/retrieval, provenance completeness, context utility, proactive precision, and complexity.

## 6.5 Error budget

Borrow the SRE concept.

If a subsystem falls below reliability/safety SLO:

- freeze optimization that increases behavioral surface;
- allow critical/security fixes;
- prioritize root-cause and regression coverage;
- resume experimentation only after recovery.

This prevents the Meta-Improvement Engine from increasing change velocity while reliability deteriorates.

---

# 7. Context & Memory Architecture

## 7.1 Memory classes

### Working state
Ephemeral execution state needed to resume current work.

### Episodic evidence
What happened: traces, events, interactions, outcomes.

### Semantic knowledge
Facts, claims, concepts, relationships, project knowledge.

### Procedural knowledge
Validated skills, deterministic workflows, tools, playbooks.

### Decision knowledge
ADRs, accepted constraints, rejected alternatives, rationale.

### Personalization
User preferences, patterns, people/project context under domain/privacy policy.

Do not blur these stores semantically even if they share physical storage.

## 7.2 Canonical vs derived

Continue current principle:

- Git: reviewed durable schemas, rules, docs, decisions, sanitized knowledge, tests, manifests.
- Local derived stores: indexes, caches, telemetry, private traces, private OCR, private sensitive evidence.
- External services: adapters, never canonical unless explicitly chosen.

## 7.3 Retrieval pipeline

```text
resolve task + domain + authorization scope
  -> identify memory classes needed
  -> cheap exact/structured retrieval
  -> lexical + semantic candidates as needed
  -> temporal/entity filters
  -> provenance/authority filter
  -> contradiction/staleness check
  -> rerank
  -> token-budget pack
  -> lazy secondary retrieval if evidence is insufficient
  -> record retrieval-use telemetry
```

## 7.4 Contradiction and staleness

Never silently overwrite contradictory durable information.

Store:

- valid_from / valid_to where meaningful;
- recorded_at;
- source;
- confidence;
- status: active / contested / superseded / stale / retracted;
- relationship to prior claim;
- reason for update.

A later fact may supersede an earlier fact without making the earlier historical fact “false.”

## 7.5 Memory-write gate

Before durable promotion ask:

- Is it likely to matter again?
- Is it scoped to the right domain/person/project?
- Is authorship/speaker identity reliable?
- Is it fact, user interpretation, or model inference?
- Does a canonical fact already exist?
- Does it contradict current state?
- Is it sensitive?
- What retention applies?
- Can it be represented without unnecessary raw content?

---

# 8. Model & Tool Capability Registry

Each model/tool record should separate **claimed capability** from **measured capability**.

## 8.1 Static identity

- provider;
- model/tool ID;
- version/revision;
- first/last seen;
- deprecation status;
- modalities;
- context limits;
- tool/function support;
- structured output support;
- locality/cloud;
- privacy/data terms reference;
- pricing source/date.

## 8.2 Measured evidence

Per task family:

- eval suite/version;
- sample size;
- success rate;
- uncertainty interval;
- correction rate;
- latency distribution;
- input/output/cache tokens;
- cost/success;
- tool error rate;
- refusal/abstention behavior;
- long-context degradation;
- resume behavior if applicable;
- failure clusters;
- evidence timestamp.

## 8.3 Routing

Use constrained optimization:

1. eliminate candidates failing authorization/privacy/modality/context requirements;
2. eliminate candidates below quality/reliability threshold for risk class;
3. choose the lowest expected total cost/latency objective;
4. escalate when validators fail or uncertainty is too high.

Model routing itself becomes an experimentable policy with champion/challenger evaluation.

## 8.4 Tool lifecycle

Tools need the same discipline:

- capability;
- owner/source;
- permission class;
- schema version;
- latency;
- failure rate;
- usage frequency;
- redundancy links;
- security review;
- deprecated/sunset date;
- replacement.

A tool no one uses is a deletion candidate, not permanent architecture.

---

# 9. Redundancy / Simplification Engine

## 9.1 Component graph

Maintain a generated graph of:

- components;
- capabilities provided;
- interfaces;
- data stores;
- prompts;
- tools;
- agents;
- external dependencies;
- consumers;
- usage;
- failure rate;
- cost;
- owner/project.

## 9.2 Candidate detection

Look for:

- same capability implemented twice;
- same source indexed in multiple canonical stores;
- same prompt logic copied;
- agents differing only by minor instructions;
- multiple tool wrappers over one API;
- repeated summary layers;
- model calls whose outputs are deterministic;
- unused fallback;
- dead configuration;
- provider-specific workaround after provider behavior changed;
- duplicate telemetry/event stores.

## 9.3 Delete test

Before deletion:

1. identify consumers;
2. simulate or shadow-disable;
3. run regression suite;
4. verify fallback/rare-path coverage;
5. archive migration path;
6. remove;
7. monitor.

## 9.4 Complexity budget

Every new persistent subsystem should answer:

- What existing component cannot satisfy the requirement?
- What does this replace?
- What new state does it own?
- What new failure modes does it add?
- Who/what maintains it?
- How is it deleted later?

“Nothing” can be the best new feature.

---

# 10. Proactivity Architecture

## 10.1 Opportunity object

A proactive opportunity should record:

- event/trigger;
- user goal/commitment/project;
- possible action;
- expected benefit;
- confidence;
- urgency;
- deadline;
- reversibility;
- consequence/risk;
- interruption cost;
- novelty;
- prior similar interventions;
- authorization requirement.

## 10.2 Intervention classes

1. **quiet observation** — gather more evidence;
2. **automatic local preparation** — reversible, low-risk work;
3. **candidate capture** — preserve opportunity without interrupting;
4. **review queue** — useful but non-urgent;
5. **digest** — batch low-urgency items;
6. **immediate surface** — urgent/high-value;
7. **clarifying question** — action blocked by material ambiguity;
8. **future re-check** — value depends on changing condition;
9. **do nothing**.

## 10.3 Utility framing

A conceptual score:

```text
expected utility
= probability useful
  * impact
  * timeliness
  * confidence
  * actionability
  - interruption cost
  - false-positive cost
  - privacy/risk cost
  - execution/model cost
```

Do not pretend the numbers are objectively measurable at first. Begin with explicit ordinal components and calibrate from observed outcomes.

## 10.4 Feedback

Capture:

- acted on;
- accepted but deferred;
- dismissed;
- rejected as irrelevant;
- duplicate/already known;
- too late;
- too early;
- useful but wrong channel;
- missed opportunity discovered retrospectively.

Optimization target differs by channel:

- interruptions: favor precision;
- quiet review queue: tolerate more recall;
- safety/deadline critical alerts: raise recall where evidence justifies it.

---

# 11. Research Radar

## 11.1 Source groups

### Critical/high-frequency
- provider model/API deprecations;
- MCP/A2A specifications;
- security advisories;
- key tool dependency releases;
- Agent OS dependency CVEs.

### Regular
- OpenAI, Anthropic, Google, Microsoft agent/runtime changes;
- local/open models;
- coding agents;
- embeddings/rerankers;
- retrieval systems;
- evaluation frameworks;
- workflow/durable-execution engines;
- browser/computer-use systems;
- voice/audio systems;
- mobile/OS integration;
- observability/provenance standards.

### Research watch
- prompt injection;
- memory poisoning;
- continual learning;
- routing;
- context optimization;
- automated program repair;
- self-correction;
- active learning;
- human-agent interaction;
- proactive computing;
- personal information management;
- HCI interruption/task-resumption research.

## 11.2 Radar gate

For every item:

1. What existing Agent OS limitation does this affect?
2. Does it replace complexity?
3. Does it materially improve a measured metric?
4. Does it enable a previously impossible valuable capability?
5. Is the evidence independent or just vendor claims?
6. What would adoption cost?
7. Is current behavior already good enough?

Only then create an improvement candidate.

## 11.3 Radar telemetry

Measure:

- items scanned;
- items promoted to findings;
- findings promoted to experiments;
- experiments accepted;
- deprecations caught before breakage;
- false alarms/noise;
- research cost per accepted improvement.

If research produces no action repeatedly, reduce cadence or scope.

---

# 12. Future-Model Handoff Architecture

A future model should not need chat archaeology.

Generate a compact **inheritance manifest** containing:

- Agent OS purpose and non-negotiable principles;
- current architecture map;
- canonical repository paths;
- domain/privacy boundaries;
- tool/interface contracts;
- active models/tools and capability evidence;
- current SLOs;
- latest eval baselines;
- active improvements;
- active hypotheses/experiments;
- unresolved failures;
- top open questions;
- roadmap priority;
- current weakest links;
- latest ADRs;
- deprecations/migrations in progress;
- recent research-radar changes;
- next recommended research/actions;
- pointers to local/private state without copying it.

## 12.1 Machine-readable relationship model

Use stable typed edges such as:

- `derived_from`;
- `supports`;
- `contradicts`;
- `supersedes`;
- `tests`;
- `evaluates`;
- `implements`;
- `caused_by`;
- `observed_in`;
- `depends_on`;
- `replaces`;
- `rolled_back_by`.

This is sufficient to inherit the valuable ideas from W3C PROV/OpenLineage without forcing Agent OS to adopt their entire schemas.

---

# 13. Security & Authorization Model

## 13.1 Fundamental trust rule

Treat the LLM as an **untrusted planner with bounded capabilities**.

The model may decide what it wants to attempt. A deterministic layer decides what may actually happen.

## 13.2 Authorization request

At every consequential boundary evaluate:

- principal/agent identity;
- user on whose behalf it acts;
- action;
- resource;
- domain;
- data sensitivity;
- tool;
- requested side effect;
- spending/budget;
- current approval token;
- risk class;
- provenance/taint of arguments;
- environmental constraints.

Default deny.

## 13.3 Capability separation

Separate:

- read;
- propose;
- write local reversible;
- write canonical;
- send externally;
- delete;
- purchase/spend;
- modify authorization;
- modify audit;
- access secrets.

No general “agent has tool access” permission.

## 13.4 Control/data separation

External web pages, email bodies, documents, MCP tool results, and retrieved knowledge are data. They cannot:

- change system policy;
- grant a capability;
- change approval state;
- add a new trusted tool;
- modify authorization rules;
- direct secret exfiltration.

Track source/taint through the action path.

## 13.5 Non-modifiable invariants

No agent may:

- grant itself permissions;
- approve its own privilege escalation;
- delete required audit evidence;
- disable safety tests to get a better score;
- silently broaden spending;
- silently widen data scope;
- overwrite canonical security policy from untrusted input.

## 13.6 Sandboxes and side effects

- generated code runs sandboxed;
- network/file mounts are allowlisted;
- high-risk actions use dry-run/preview;
- irreversible actions require explicit approval according to policy;
- retries use idempotency keys;
- commits/artifacts record provenance;
- dependencies are pinned/verified where practical.

---

# 14. Improvement Backlog

The structured backlog is stored in `improvement-backlog.json`.

Highest-priority candidates from this pass:

- **MIE-0001** unified improvement evidence chain;
- **MIE-0002** provider-neutral eval registry/task corpus;
- **MIE-0004** failure/success registries and clustering;
- **MIE-0005** experiment/rollout/rollback registry;
- **MIE-0006** deterministic authorization plane;
- **MIE-0007** untrusted-data taint/control-flow separation;
- **MIE-0008** task-specific model/tool capability registry;
- **MIE-0010** memory/retrieval eval suite;
- **MIE-0011** simplification/deletion engine;
- **MIE-0013** unified proactivity decision engine;
- **MIE-0015** future-model handoff bundle.

Do not implement all of them in parallel. The correct sequencing begins with evidence/evals and authorization, because every later adaptive feature depends on them.

---

# 15. Open Questions

The machine-readable registry is stored in `open-questions.json`.

The most consequential unresolved questions are:

1. What minimum authorization invariants must cover every tool?
2. Which current side effects are not exactly-once/idempotent on resume?
3. How can the task corpus be representative without leaking sensitive data?
4. How should user effort/cognitive load be measured?
5. What evidence thresholds promote candidates to durable rules?
6. How should temporal contradiction/supersession work?
7. When is graph retrieval worth its complexity?
8. What very small set of SLOs best captures real usefulness?
9. How can missed proactive opportunities be measured?
10. When should challenge surface now versus queue/digest?
11. When does external durable-execution infrastructure become worth adopting?
12. How should model capability uncertainty decay as models/providers change?

---

# 16. Unknown Unknowns

Areas that appear important enough for dedicated investigation but are not yet mature in this pass:

## 16.1 Causal inference

If prompt, model, retrieval, and tool versions all change at once, attribution becomes impossible. The engine needs experiment discipline and perhaps causal-inference methods for observational production data.

## 16.2 Formal verification/model checking

Authorization state machines, workflow invariants, and “cannot happen” security claims may benefit from property testing, model checking, or formally analyzable policy languages.

## 16.3 Economics of information

Research itself has a cost. Agent OS needs a “value of more information” model: when should it stop searching and act?

## 16.4 Contextual bandits / safe online learning

Routing and proactivity could eventually learn online, but exploration must be constrained by user risk and annoyance. This should be researched after deterministic baselines exist.

## 16.5 CRDT/local-first state synchronization

As Agent OS spans desktop, phone, recorder, browser, and future devices, synchronization conflicts may become a first-class architecture problem.

## 16.6 Retention/value decay

Not all historical evidence remains equally useful. The system needs principled retention, compaction, and expiry by data class.

## 16.7 Machine-readable behavioral contracts

Future models may benefit from contracts that specify not just APIs but expected behavioral properties, failure semantics, and examples.

---

# 17. Contrarian Review

## 17.1 This entire Meta-Improvement Engine could become bureaucracy

The largest risk is building a beautiful meta-system that consumes more engineering, tokens, storage, and attention than the improvements it produces.

Countermeasure: measure the engine itself.

Track:

- research cost;
- candidate count;
- candidate-to-experiment conversion;
- experiment-to-accepted-change conversion;
- measured value of accepted changes;
- stale backlog;
- duplicate findings;
- repeated audits with no new result;
- context overhead added by meta-state.

If the engine repeatedly produces paperwork rather than measurable improvement, delete layers.

## 17.2 “Recursive” may be the wrong metaphor

The useful mechanism is closer to:

- SRE;
- scientific experimentation;
- continuous delivery;
- active learning;
- observability;
- product analytics;
- decision support.

Calling it recursive self-improvement can encourage over-agentic design. Most improvement should come from ordinary engineering loops with models helping at specific steps.

## 17.3 More agents are not necessarily better

Multi-agent architectures are expensive and coordination-heavy. A single strong model with good tools, persistent state, validators, and selective parallel subwork may be better for most Agent OS tasks.

## 17.4 A universal knowledge graph may be unnecessary

Typed relationships are valuable. A heavyweight graph database may not be. Start with stable IDs + typed edges in files/SQLite and benchmark graph-specific queries before adding infrastructure.

## 17.5 A full Temporal deployment may be premature

Current homegrown staged workflows and ingestion ledgers already solve meaningful resumability problems. The right next step is to characterize their gaps, not automatically replace them with a workflow platform.

## 17.6 Automatic fine-tuning is probably far down the priority list

Agent OS can capture much of the benefit through:

- better context;
- better retrieval;
- skills;
- deterministic automation;
- routing;
- prompt/tool optimization;
- cached artifacts;
- model upgrades.

Fine-tuning adds data governance, evaluation, rollback, and behavioral-opacity costs. It should require clear evidence that simpler mechanisms plateau.

## 17.7 Personal optimization can become invasive

“Challenge everything in my life” can easily become nagging or surveillance if every observation creates an intervention. The architecture must make *doing nothing* an explicit successful decision.

## 17.8 The best future system may contain less Meta-Improvement machinery

As future models become more reliable, context windows expand, and providers expose better native durability/evaluation/routing, some custom layers should disappear. The engine must be designed to retire itself piece by piece.

---

# 18. Next Research Pass

Priority order for the next pass:

## P1 — Evaluation science and schema

Deepen:

- provider-neutral eval schema;
- train/dev/holdout governance;
- stateful agent eval;
- long-horizon eval;
- grader calibration/disagreement;
- dynamic benchmark generation;
- contamination control;
- user-effort metrics;
- macro vs micro evals.

Deliverable: `eval-architecture-v1.md` + schema drafts, no runtime implementation yet.

## P2 — Authorization, prompt injection, and data-flow security

Deepen:

- Cedar vs OPA vs minimal embedded policy engine;
- capability systems;
- confused-deputy defense;
- CaMeL design;
- AgentDojo/current attacks;
- taint tracking;
- action approval;
- secret isolation;
- MCP/A2A authorization.

Deliverable: threat model + authorization contract + invariants.

## P3 — Real-workload capability/routing evidence

Deepen:

- task taxonomy;
- benchmark design;
- uncertainty/confidence;
- routing objective;
- escalation;
- champion/challenger;
- cost/success;
- generic benchmark vs real workload weighting.

Deliverable: model/tool capability registry schema and routing-eval plan.

## P4 — Proactivity and constructive challenge HCI

Deepen:

- interruption timing;
- mixed initiative;
- task boundaries;
- reminders and forgetting;
- cognitive load;
- dismissal/rejection learning;
- notification precision/recall;
- challenge fatigue.

Deliverable: intervention policy and measurement plan.

## P5 — Simplification and architecture entropy

Deepen:

- component manifests;
- dependency/capability graph;
- runtime usage evidence;
- shadow-disable/delete experiments;
- complexity metrics;
- stale/dead feature detection;
- source-of-truth duplication.

Deliverable: simplification audit design.

## P6 — Durable execution threshold study

Deepen current Agent OS workflow semantics first. Compare those guarantees against Temporal/Dapr/LangGraph/Microsoft Agent Framework durability only after measuring actual failure/replay needs.

Deliverable: build-vs-adopt decision record.

---

# Proposed durable schema family

The eventual schema family should have a common envelope:

```yaml
schema_version: 1
id: <stable typed ID>
kind: <source|claim|finding|failure|success|hypothesis|experiment|eval_case|eval_suite|eval_run|improvement|decision|capability|radar_item|question>
created_at: ...
updated_at: ...
status: ...
scope:
  domain: ...
  project: ...
epistemic:
  class: <official_doc|empirical|benchmark|community|user_report|inference|hypothesis>
  confidence: ...
  freshness: ...
provenance:
  sources: [...]
  derived_from: [...]
relationships:
  supports: [...]
  contradicts: [...]
  supersedes: [...]
  depends_on: [...]
security:
  sensitivity: ...
  canonical_allowed: ...
review:
  last_reviewed: ...
  review_due: ...
```

Type-specific schemas add only what is necessary.

---

# Recommended implementation sequence after research

Do not start with an autonomous critic agent.

Start with infrastructure that makes later learning trustworthy:

```text
1. eval registry + task corpus
2. evidence/provenance object model
3. failure/success normalization
4. experiment + rollback records
5. deterministic authorization contract
6. tool/model capability evidence
7. context/retrieval utility evals
8. simplification auditor
9. bounded constructive challenge
10. bounded proactive decision engine
11. research radar
12. advanced automated optimizers
13. only then consider continual training/fine-tuning
```

This sequencing intentionally delays the most “intelligent-looking” features until the system can prove whether they help.

---

# Definition of success for the Meta-Improvement Engine

The engine is successful if, over time:

- the same failure is less likely to recur;
- repeated successful patterns become cheaper reusable capabilities;
- user corrections decrease;
- user effort decreases;
- cost per successful task declines;
- context becomes smaller without quality loss;
- interrupted workflows resume safely;
- security/privacy violations remain blocked by deterministic policy;
- obsolete components are removed;
- model/provider migration gets easier;
- proactive interventions become more useful and less noisy;
- future models can understand why the system is shaped the way it is;
- research produces measurable changes rather than accumulating prose;
- the improvement engine itself consumes a justified and preferably declining share of total system effort.

The most important meta-metric is not “how many improvements did we generate?”

It is:

> **How much verified user value did the system gain per unit of added complexity, cost, risk, and attention?**
