# Meta-Improvement Research Source Index — Pass 1

As-of date: 2026-09-24

Evidence labels used below: **official** = vendor/standard/maintainer documentation; **research** = peer-reviewed paper or preprint; **engineering report** = implementation experience from a primary builder; **historical research** = older work retained because the principle remains relevant.

## Agent architecture and orchestration

1. **Anthropic — How we built our multi-agent research system** (engineering report, 2025). Multi-agent breadth can outperform single-agent research for heavily parallelizable tasks, but Anthropic reports very large token multipliers and warns that tightly coupled tasks are poorer fits.  
   https://www.anthropic.com/engineering/multi-agent-research-system

2. **OpenAI — Agents SDK** (official, current 2026). The SDK is feature-complete/maintenance-oriented and OpenAI recommends the managed Agents API for new agent applications. Important inheritance lesson: do not make Agent OS architecture depend on a provider SDK remaining strategic.  
   https://developers.openai.com/api/docs/guides/agents/sdk

3. **Microsoft — Agent Framework 1.0** (official, 2026). Production successor to AutoGen/Semantic Kernel agent orchestration, with multi-provider support and A2A/MCP interoperability.  
   https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/

4. **Microsoft — Agent Framework workflows** (official, current 2026). Explicit workflows/checkpoints are recommended when guaranteed execution order and recovery matter; simpler agent composition is recommended first.  
   https://learn.microsoft.com/en-us/agent-framework/journey/workflows

5. **Google — Agent Development Kit** (official, current 2026). Useful reference for agents, workflows, sessions, memory, evaluation, tool integration, and sandboxed code execution.  
   https://google.github.io/adk-docs/agents/

## Protocols and interoperability

6. **Model Context Protocol 2026-07-28** (official). Stateless core, self-describing requests, cacheable lists, header routing, extension framework, authorization hardening, deprecation policy, and Tasks extension.  
   https://blog.modelcontextprotocol.io/posts/2026-07-28/

7. **MCP Tasks extension** (official). Defines durable task handles and poll/update/cancel lifecycle for deferred work.  
   https://tasks.extensions.modelcontextprotocol.io/specification/draft/tasks

8. **A2A Protocol 1.0.0** (official). Cross-framework agent discovery, task management, modality negotiation, and information exchange without sharing internal memory/tools.  
   https://a2a-protocol.org/dev/specification/

## Durable execution, observability, reliability

9. **Temporal — complexity cliff / durable execution for agents** (engineering report, 2026). Long-running workflows need durable state, replay, and side-effect-safe recovery; history branching can make later-stage experiments much cheaper.  
   https://temporal.io/blog/building-ai-agents-that-overcome-the-complexity-cliff

10. **Temporal + OpenAI Agents SDK integration** (official/engineering report). Demonstrates durable execution around agent/model/tool activities.  
    https://temporal.io/blog/announcing-openai-agents-sdk-integration

11. **OpenTelemetry — GenAI observability** (official, 2026). Standardized model/tool/token/latency traces and metrics, with content capture treated as sensitive opt-in data.  
    https://opentelemetry.io/blog/2026/genai-observability/

12. **Google SRE — Error Budget Policy** (primary engineering guidance). Provides a concrete control-loop pattern: when reliability budget is exhausted, stop feature change and redirect effort to reliability.  
    https://sre.google/workbook/error-budget-policy/

13. **Google SRE — Eliminating Toil** (primary engineering guidance). Defines toil as manual, repetitive, automatable, tactical work lacking enduring value and scaling with system growth.  
    https://sre.google/sre-book/eliminating-toil/

## Provenance and software supply chain

14. **W3C PROV** (standard). Entities, activities, agents, usage, generation, derivation, and responsibility provide a durable conceptual model for research/change provenance.  
    https://www.w3.org/TR/prov-overview/

15. **OpenLineage object model** (open standard). RunEvent, JobEvent, DatasetEvent and facets are a useful model for separating design metadata from runtime lineage.  
    https://openlineage.io/docs/spec/object-model/

16. **SLSA v1.2 Provenance** (approved specification). Verifiable software-artifact provenance for build/source supply chains.  
    https://slsa.dev/spec/v1.2/provenance

## Evaluation and benchmark science

17. **OpenAI — Evaluate agent workflows** (official, 2026). Traces first for debugging; datasets/eval runs for repeatability. Useful pattern, but the provider-hosted Evals product is being retired.  
    https://developers.openai.com/api/docs/guides/agent-evals

18. **OpenAI — Deprecations** (official, current 2026). Evals becomes read-only 2026-10-31 and is scheduled to shut down 2026-11-30; Agent Builder also shuts down 2026-11-30. Strong evidence for a provider-neutral local eval core.  
    https://developers.openai.com/api/docs/deprecations

19. **RAGChecker** (research, 2024). Fine-grained retrieval and generation diagnostics; demonstrates why end-to-end answer accuracy alone is inadequate for retrieval systems.  
    https://arxiv.org/abs/2408.08067

20. **RAGAS** (research, 2023). Reference-free metrics for retrieval relevance/focus, faithfulness, and generation quality.  
    https://arxiv.org/abs/2309.15217

21. **LLM-as-a-Judge position-bias study** (research, 2025). 150k+ evaluations across judges/tasks show systematic position bias; graders require calibration, order randomization, deterministic checks, and disagreement analysis.  
    https://aclanthology.org/2025.ijcnlp-long.18/

22. **Benchmark contamination survey** (research, EMNLP 2025). Shows why dynamic/private task sets and contamination-aware benchmarking matter.  
    https://aclanthology.org/2025.emnlp-main.511/

23. **METR time-horizon methodology** (research/benchmark program, current 2026). Useful for measuring how task duration and messiness affect autonomous completion; public benchmarks should not be confused with the user's real workload distribution.  
    https://metr.org/time-horizons/

## Model routing and cost/quality optimization

24. **RouteLLM** (research/open source, 2024). Learns strong-vs-weak model routing from preference data and demonstrates substantial benchmark cost reductions.  
    https://arxiv.org/abs/2406.18665

25. **FrugalGPT** (research, 2023). Prompt adaptation, approximation, and cascades show that cost can be optimized while preserving or sometimes improving task performance.  
    https://arxiv.org/abs/2305.05176

## Memory, context, retrieval

26. **MemGPT** (research, 2023). Treats context management as virtual-memory-like paging between memory tiers; useful conceptual basis for externalized working state.  
    https://arxiv.org/abs/2310.08560

27. **LongMemEval** (research, 2024). Tests extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention; shows that long-term memory quality is not equivalent to simply retaining more history.  
    https://arxiv.org/abs/2410.10813

28. **MemBench** (research, 2025). Evaluates agent memory effectiveness, efficiency, and capacity across factual/reflective and participation/observation scenarios.  
    https://arxiv.org/abs/2506.21605

29. **Anthropic — Context engineering for AI agents** (engineering guidance, 2025). Treats context as a finite resource whose value depends on relevance and utility rather than raw quantity.  
    https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

## Self-improvement, reflection, correction

30. **Critical survey of LLM self-correction** (TACL 2024). Finds intrinsic prompted self-correction unreliable outside unusually favorable tasks; reliable external feedback is much more dependable.  
    https://aclanthology.org/2024.tacl-1.78/

31. **Large Language Models Cannot Self-Correct Reasoning Yet** (research, 2023). Shows self-correction can degrade reasoning without external feedback.  
    https://arxiv.org/abs/2310.01798

32. **DSPy** (research). Declarative LM programs plus metric-driven compilation/optimization motivate eval-gated prompt/pipeline search instead of hand-tuning alone.  
    https://arxiv.org/abs/2310.03714

33. **OPRO — Optimization by PROmpting** (research). LLM-generated candidate prompts can be evaluated iteratively against objective metrics; only appropriate when the metric/eval is trustworthy.  
    https://arxiv.org/abs/2309.03409

## Agent security and deterministic authorization

34. **OWASP Top 10 for Agentic Applications 2026** (industry security guidance). Current agent-specific threat framework.  
    https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

35. **OWASP GenAI LLM Top 10 2026 / Agent Control Standard announcement** (current 2026).  
    https://genai.owasp.org/2026/09/01/owasp-genai-security-project-unveils-2026-top-10-for-llm-applications-new-agent-control-standard-and-sponsors-as-community-tops-30000-members/

36. **AgentDojo** (research, 2024). Extensible benchmark for prompt injection in tool-using agents with realistic tasks and adversarial cases.  
    https://arxiv.org/abs/2406.13352

37. **CaMeL — Defeating Prompt Injections by Design** (research, updated 2025 / SaTML 2026). Separates trusted control flow from untrusted data flow and uses capability-based policies; particularly relevant to Agent OS tool authorization.  
    https://arxiv.org/abs/2503.18813

38. **Cedar authorization language** (official). Separates authorization policy from business logic; principal/action/resource/context requests, default deny, and explicit forbids are strong fits for agent tool gates.  
    https://docs.cedarpolicy.com/

39. **Cedar — agents acting on behalf of a principal** (official, current). Explicit patterns for modeling an agent and the user/on-behalf-of relationship in authorization context.  
    https://docs.cedarpolicy.com/bestpractices/bp-using-the-context.html

40. **Open Policy Agent** (official). Alternative general-purpose policy-as-code engine with default-deny patterns and local deployment.  
    https://www.openpolicyagent.org/docs/security

41. **NIST AI RMF and GenAI Profile** (official). Current AI RMF 1.0 is being revised in 2026; use as risk taxonomy/guidance rather than freezing Agent OS to a superseded version.  
    https://www.nist.gov/itl/ai-risk-management-framework  
    https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

42. **NIST SSDF** (official). v1.1 remains final; v1.2 is currently a draft. Relevant practices include secure environments, security requirements, provenance, risk/design-decision tracking, and root-cause prevention.  
    https://csrc.nist.gov/projects/ssdf/publications

## Proactivity and human factors

43. **Attention-Sensitive Alerting** (historical research). Formalizes the value of balancing alert criticality/delay cost against interruption cost.  
    https://www.microsoft.com/en-us/research/publication/attention-sensitive-alerting/

44. **Need Help? Designing Proactive AI Assistants for Programming** (CHI 2025). Experimental evidence that proactive assistance can help, but design details strongly affect usefulness and adoption.  
    https://www.microsoft.com/en-us/research/?p=1134954

45. **Human-AI Interaction Design Guidelines** (research/design guidance). Includes timing services based on context, contextual relevance, efficient dismissal/correction, and communicating capability/uncertainty.  
    https://www.microsoft.com/en-us/research/?p=564561

46. **Magentic-UI** (engineering research). Co-planning, anytime interruption, allowlists, sandboxing, and approvals for irreversible actions are strong human-control patterns.  
    https://www.microsoft.com/en-us/research/blog/magentic-ui-an-experimental-human-centered-web-agent/

## Source-policy note

These sources are inputs, not unquestionable truth. Vendor engineering posts can contain product incentives; preprints may not be peer reviewed; old HCI/SRE results must be revalidated in the current Agent OS context. The research registry should preserve claim-level provenance and disagreement rather than flattening all sources into one confidence score.
