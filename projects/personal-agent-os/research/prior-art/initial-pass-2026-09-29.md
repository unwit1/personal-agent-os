# Prior-art initial pass (2026-09-29)

Generated from `registry.json`; the registry is canonical. 45 projects: 19 seeded by the operator plus 26 found by task-specific discovery for areas where Agent OS may be reinventing work.
Facts (license, activity) come from the GitHub REST API on 2026-09-29. Judgments compare each project with current Agent OS code, and each carries a confidence level.

| Decision | Project | Areas | Confidence | Why (short) |
|---|---|---|---|---|
| INVESTIGATE | [GEPA](https://github.com/gepa-ai/gepa) | prompt optimization, reflective optimization, Pareto candidate search | medium | Found by discovery: standalone reflective Pareto optimizer (ICLR 2026) that reads full execution traces to propose prompt edits; reported to beat MIPR |
| INVESTIGATE | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | property-based testing, stateful testing, state-machine testing | high | Best-in-class stateful testing (RuleBasedStateMachine with rules, invariants, preconditions, and automatic shrinking to a minimal failing sequence) |
| INVESTIGATE | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | agent evaluation, eval sets, sandboxing | medium | Strongest WRAP candidate for evaluation breadth: verified from the docs to have pluggable sandboxes (Docker, Kubernetes, others via extensions), eval  |
| INVESTIGATE | [mutmut](https://github.com/boxed/mutmut) | mutation testing | medium | Run as an external developer tool (not imported, so no runtime dependency) against control-plane modules (control_plane.py, validators.py) to measure  |
| BORROW | [AgentDojo](https://github.com/ethz-spylab/agentdojo) | prompt-injection benchmark, tool-use security | medium | Borrow its injection tasks and attack generators as EVS-SECURITY cases (with provenance, protected split). |
| BORROW | [AgentRx](https://github.com/microsoft/AgentRx) | failure localization, failure taxonomy, trajectory diagnosis | low | Synthesizes invariants, checks them step by step, and classifies failures into a grounded 10-category taxonomy |
| BORROW | [Aider](https://github.com/Aider-AI/aider) | repository map, context selection, symbol ranking | low | Aider ranks symbols with a reference graph (PageRank over tree-sitter tags) to fit a token budget |
| BORROW | [CaMeL](https://github.com/google-research/camel-prompt-injection) | prompt-injection defense, control/data-flow separation, capability tracking | medium | Design reference for MIE-0007: a privileged planner that sees only trusted input, a quarantined model that reads untrusted data but cannot call tools, |
| BORROW | [Cedar](https://github.com/cedar-policy/cedar) | policy/authorization, policy language, schema validation | medium | Borrow the principal-action-resource model with schema-validated policies and default deny for MIE-0006; a Rust binary/bindings dependency is unnecess |
| BORROW | [DBOS Transact](https://github.com/dbos-inc/dbos-transact-py) | durable execution, idempotent steps, workflow recovery | low | Library-level durable workflows (no separate server) with workflow IDs making steps idempotent |
| BORROW | [garak](https://github.com/NVIDIA/garak) | LLM vulnerability scanning, red teaming | low | Probe catalog (jailbreaks, leakage, encoding attacks) is a second source for security cases; the scanner itself targets model endpoints rather than ag |
| BORROW | [Graphiti](https://github.com/getzep/graphiti) | temporal knowledge graph, bi-temporal facts, entity resolution | medium | Borrow the bi-temporal fact model (valid_at / invalid_at plus ingestion time, facts invalidated rather than deleted) for durable facts that change ove |
| BORROW | [LangGraph](https://github.com/langchain-ai/langgraph) | durable execution, checkpoint/replay, human-in-the-loop interrupts | low | Agent OS already covers durable runs, gates and resume for its domain |
| BORROW | [Letta](https://github.com/letta-ai/letta) | agent memory, context paging, memory hierarchy | low | Must not replace Git-backed canonical memory |
| BORROW | [LiteLLM](https://github.com/BerriAI/litellm) | model gateway, provider failover, cost tracking | high | Highest-risk dependency found: malicious versions 1.82.7/1.82.8 were published to PyPI on 2026-03-24 (credential stealer via a .pth file running at ev |
| BORROW | [Mem0](https://github.com/mem0ai/mem0) | memory extraction, memory deduplication, memory update decisions | medium | Its memory update step (compare a new fact with similar existing memories and choose ADD / UPDATE / DELETE / NOOP) is a crisp pattern for Agent OS can |
| BORROW | [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | minimal coding-agent loop, bash-only tool use, API-model agents | medium | About a hundred lines of agent loop with bash as the only tool, reported competitive on SWE-bench |
| BORROW | [OpenHands](https://github.com/OpenHands/OpenHands) | coding-agent runtime, sandbox architecture, tool loop | low | Replacing the CLI workers with the OpenHands runtime would surrender orchestration and add a large TypeScript/Python/Docker stack |
| BORROW | [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) | distributed tracing, agent observability, trace schema | high | A specification, not a dependency: map Agent OS events to gen_ai.* span attributes (gen_ai.operation.name, provider, request/response model, usage tok |
| BORROW | [Promptfoo](https://github.com/promptfoo/promptfoo) | red teaming, prompt injection testing, LLM evaluation | medium | TypeScript/Node runtime, so not a dependency for a Python stdlib runtime |
| BORROW | [pybreaker](https://github.com/danielfm/pybreaker) | circuit breaking, provider failover | high | Circuit breaker state machine (closed -> open after fail_max failures -> half-open after reset_timeout -> closed on success) is small; subsumed into r |
| BORROW | [PydanticAI](https://github.com/pydantic/pydantic-ai) | typed agent outputs, structured output validation, tool schemas | medium | Its provider abstraction duplicates Agent OS adapters and it would bring pydantic into a stdlib runtime |
| BORROW | [Ragas](https://github.com/vibrantlabsai/ragas) | retrieval evaluation, RAG metrics | low | Borrow metric definitions (context precision/recall, faithfulness) when retrieval evaluation starts; model-graded metrics would need Agent OS routing  |
| BORROW | [RouteLLM](https://github.com/lm-sys/RouteLLM) | model routing, strong/weak routing, threshold calibration | medium | Last push 2024-08 (stale) |
| BORROW | [Tenacity](https://github.com/jd/tenacity) | retry orchestration, exponential backoff, jitter | high | The needed part is small and well understood: exponential backoff with full jitter, a stop-after-attempts/delay rule, retry only on retryable errors,  |
| DEFER | [ADAS / Meta Agent Search](https://github.com/ShengranHu/ADAS) | automated agent design, meta agent search | low | Research code, last push 2025-01 |
| DEFER | [AFlow (MetaGPT ext)](https://github.com/FoundationAgents/MetaGPT) | workflow optimization, MCTS over workflows | low | Monte Carlo tree search over agent workflow graphs needs many evaluated rollouts per task family, far beyond Agent OS's per-pass budget (<= 9 model ca |
| DEFER | [Arize Phoenix](https://github.com/Arize-ai/phoenix) | LLM observability, OTel tracing UI, evals | medium | OTel-native and runs locally, so it could view Agent OS traces once the OTel projection exists |
| DEFER | [Darwin Godel Machine](https://github.com/jennyzzt/dgm) | self-modifying coding agents, open-ended archive search | low | Open-ended self-modification of a coding agent validated on SWE-bench-style tasks; executes untrusted self-written code and needs large evaluation bud |
| DEFER | [DSPy](https://github.com/stanfordnlp/dspy) | prompt optimization, workflow optimization, evaluator-driven optimization | medium | DSPy is a full programming model (signatures, modules, compiled programs) aimed at API LLM calls; adopting it would pull Agent OS prompts into its abs |
| DEFER | [HyperAgents (DGM-H)](https://github.com/facebookresearch/HyperAgents) | self-referential self-improvement, meta-level improvement transfer | low | Meta's 2026 extension of DGM where the meta-agent also improves its own improvement process |
| DEFER | [LLMLingua](https://github.com/microsoft/LLMLingua) | context compression, prompt compression | low | Token-level compression needs a local small language model (torch); revisit if local models are added or context cost dominates. |
| DEFER | [LLMRouter](https://github.com/ulab-uiuc/LLMRouter) | model routing, router benchmarking, agentic routing | low | Found by task-specific discovery (2026-08 release, 16+ router families including agentic and multi-round routers) |
| DEFER | [OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) | evolutionary code optimization, AlphaEvolve-style search | low | Could evolve small deterministic algorithms (for example improving the import-graph selector's precision) against a deterministic fitness, which is sa |
| DEFER | [Optuna](https://github.com/optuna/optuna) | hyperparameter search, parameter tuning, TPE | medium | Useful once there is a cheap, objective, development-only objective to tune (for example selector thresholds or concurrency with deterministic benchma |
| REJECT | [AutoGen](https://github.com/microsoft/autogen) | multi-agent coordination, agent conversation patterns | high | In maintenance mode since October 2025 (no new features, community managed); Microsoft Agent Framework is the successor |
| REJECT | [CrewAI](https://github.com/crewAIInc/crewAI) | multi-agent roles, task delegation | medium | Role-play crew abstraction overlaps the orchestrator's planner/worker/reviewer model without adding verification, worktree isolation or evidence-drive |
| REJECT | [GPTCache](https://github.com/zilliztech/GPTCache) | semantic caching | medium | Semantic (similarity) caching of model answers is unsafe for coding correctness, where near-identical prompts need different answers; exact, version-k |
| REJECT | [Langfuse](https://github.com/langfuse/langfuse) | LLM observability, tracing UI, eval dashboards | medium | Self-hosting needs Postgres, ClickHouse, Redis and object storage; license is MIT with separately licensed enterprise directories |
| REJECT | [Open Policy Agent](https://github.com/open-policy-agent/opa) | policy/authorization | medium | Go binary plus Rego language: too heavy for a handful of JSON policies; Cedar's model is the better reference. |
| REJECT | [Outlines](https://github.com/dottxt-ai/outlines) | structured outputs, constrained decoding | medium | Constrained decoding needs logit access (local models); CLI and hosted API workers do not expose it |
| REJECT | [RouterBench](https://github.com/withmartian/routerbench) | router benchmarking | medium | Stale since 2024-06 and built on chat benchmarks; Agent OS's own objective cases (EVS-TEST-SELECTION) are more relevant. |
| REJECT | [smolagents](https://github.com/huggingface/smolagents) | code agents, minimal agent loop | medium | Code-as-action agents with a Python executor add an execution-sandbox concern without a capability Agent OS needs now. |
| REJECT | [Temporal](https://github.com/temporalio/sdk-python) | durable execution, workflow replay | high | Requires a Temporal server cluster; Agent OS's local, Git-backed durability is sufficient for its scale. |
| REJECT | [TextGrad](https://github.com/zou-group/textgrad) | prompt optimization, textual gradients | medium | Less active (last push 2025-07); GEPA covers the same need with stronger reported results. |

## Takeaways

- **ADOPT: none.** Research alone never promotes a dependency. Agent OS keeps its one-runtime-dependency posture, and the operator prefers subsuming code over depending on packages.
- **Subsumed now (DEC-0009):**
  - retry with full-jitter backoff and Retry-After handling (from Tenacity);
  - a circuit breaker (from pybreaker);
  - a minimal stdlib API adapter for Anthropic and OpenAI keys. LiteLLM is the obvious package for this, but it was compromised on PyPI in 2026-03 and is heavy.
- **Highest expected development savings, if the spikes confirm them:**
  - Hypothesis for orchestrator state-machine testing (shrinking is hard to rebuild);
  - Inspect AI for external benchmarks and sandboxes (WRAP as an optional extra);
  - GEPA for the MIE-0020 optimizer;
  - mutmut as an external tool for control-plane test strength.
- **Highest expected runtime savings:**
  - API adapter for one-shot delegate calls, which avoids the measured 14–19K-token CLI overhead per call (docs/simple-mode.md);
  - the backoff and breaker, which stop wasted calls against quota-blocked providers (FAIL-0001).
- **Highest-risk dependency:** LiteLLM (2026-03 supply-chain compromise, very heavy).
- **Do not adopt:**
  - AutoGen: maintenance mode since 2025-10.
  - RouteLLM as a package: stale since 2024-08, trained on chat data. The threshold-calibration idea is borrowed.
  - Temporal and Langfuse: server stacks.
  - GPTCache: semantic caching is unsafe for code.
  - Outlines: needs logit access.
- **Gaps that need deeper evaluation:**
  - OpenHands and Letta were not inspected at code level (low confidence);
  - LLMRouter (needs far more CAP data);
  - DBOS storage assumptions.
