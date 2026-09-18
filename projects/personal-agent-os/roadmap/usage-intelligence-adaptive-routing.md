# Usage Intelligence, Adaptive Routing, and Skill/Automation Mining

Status: roadmap / deferred implementation
Recorded: 2026-09-18

## Objective

Add a vendor-neutral optimization layer to Personal Agent OS that learns where model/reasoning usage is being spent and progressively replaces repeated expensive work with deterministic code, cached results, reusable skills, or cheaper model calls.

This feature is intended to conserve usage without reducing correctness. It must optimize Agent-OS-controlled work, not pretend it can change a model already running inside a host client.

## Critical client/model constraint

A third-party MCP server must NOT be designed around hot-swapping the model that is already running a ChatGPT Work or Claude task.

Working assumption as of 2026-09-18:

- An MCP tool can provide data, actions, or delegated execution to the currently running host model.
- It cannot reliably change the visible/active host model halfway through that task.
- Do not build a mechanism that expects a Work/Claude reasoning session to resume seamlessly on a different model.
- Verify current client capabilities before implementation because vendor behavior can change.

Therefore the optimization architecture must use:

1. pre-routing before expensive work starts;
2. delegation of bounded subtasks to Agent OS;
3. escalation inside Agent-OS-owned model calls;
4. future-run optimization based on telemetry and validated reusable routines.

## Execution preference

Prefer the cheapest reliable execution path in this order:

1. deterministic program / existing utility;
2. cached result;
3. approved reusable skill;
4. cheap/fast API model;
5. stronger/balanced API model;
6. frontier/high-reasoning API model when justified;
7. allow the existing ChatGPT Work / Claude session to handle genuinely difficult reasoning when delegation is not useful.

Do not use an LLM for work that can be performed deterministically with comparable or better reliability.

## Provider model

Agent OS should support separately configured provider credentials, initially OpenAI and/or Anthropic, while remaining provider-neutral.

Important:

- OpenAI API access is separate from a ChatGPT subscription.
- Anthropic API access is separate from Claude desktop/subscription usage.
- API billing/quotas are separate from host-client plan allowances.
- Do not require both providers.
- Keep credentials local or in an appropriate secrets manager; never commit API keys.

Use provider-neutral capability classes instead of hard-coding vendor model names in routing policy, for example:

- deterministic
- fast
- balanced
- reasoning
- frontier

Provider adapters map those classes to currently configured concrete models.

## Telemetry

Implement privacy-preserving task telemetry for Agent-OS-controlled work.

Capture when available:

- task/project/category/subtype;
- provider/model/capability class;
- reasoning/effort setting;
- input, cached, reasoning, and output token counts when exposed;
- API cost when determinable;
- duration;
- tool sequence;
- retries/escalations;
- skill or deterministic routine used;
- files/pages/items processed as counts only where possible;
- validator/test result;
- success/failure;
- human correction or override.

Never fabricate unavailable usage metrics.

Raw telemetry should remain local or in a dedicated telemetry store and MUST NOT be committed to Git.

Do not store raw documents, OCR text, secrets, personal data, or full conversation transcripts/prompts by default. Prefer hashes, task signatures, fingerprints, aggregate counts, and redacted metadata.

GitHub remains canonical only for durable reviewed outputs such as policies, approved skills, validated automation code, schemas, architecture decisions, and compact/redacted summaries.

## Adaptive router

Implement a router that selects the cheapest reasonable starting path and escalates only when evidence justifies it.

Candidate escalation signals:

- validator failure;
- test failure;
- insufficient confidence;
- conflicting evidence;
- unresolved ambiguity;
- repeated tool failure;
- explicit high-quality requirement;
- risk policy requiring stronger review.

The router should support explanation of why a route was selected without exposing private chain-of-thought.

## Skill Miner

Analyze historical traces for repeated workflows and create candidate reusable skills.

Useful signals include:

- repeated task category/subtype;
- similar tool sequences;
- recurring inputs or schemas;
- recurring output schemas;
- recurring repository/files accessed;
- repeated prompt structure;
- repeated validation logic.

Do not silently promote generated skills.

Candidate lifecycle:

observed repeated workflow -> candidate skill -> replay/evaluation on historical or synthetic traces -> review -> approved canonical skill or rejection.

Compare quality, tests/validators, correction rate, latency, token usage, and cost.

## Automation Miner

Separately detect recurring tasks that should become normal code instead of skills or model calls.

Examples:

- hashing;
- fingerprinting;
- normalization;
- deterministic file naming;
- schema parsing;
- JSON validation;
- repository indexing;
- exact matching;
- regex extraction;
- straightforward transformations.

Prefer a deterministic utility over an LLM when it reliably solves the task.

## Usage optimizer

Provide periodic analysis such as:

- usage by project/task/provider/model;
- highest reasoning/token consumers;
- repeated expensive workflows;
- model overqualification;
- context/retrieval inefficiency;
- repeated repository discovery;
- retry/escalation hotspots;
- candidate skills;
- candidate deterministic automations;
- prompt/context optimization opportunities;
- estimated savings.

The optimizer must be allowed to conclude that expensive reasoning was justified.

## MCP / client integration

MCP should be an interface into Agent OS, not the place where canonical routing logic lives.

Expose a small stable surface, such as equivalents of:

- agent_context;
- execute_routed_task;
- record_task_outcome;
- usage_report;
- optimization_candidates;
- evaluate_skill_candidate.

The same core logic should also be callable by CLI/API/tests.

Desktop clients are front ends:

- Claude Desktop/Claude Code can use Agent OS through supported MCP integration.
- ChatGPT/Work-compatible clients can use Agent OS through whatever MCP/app transport they currently support.
- Do not assume ChatGPT and Claude have identical local MCP behavior.
- Do not make canonical state dependent on a single client.

When a host session delegates a subtask to Agent OS, Agent OS may independently call an OpenAI or Anthropic API model. This does not change the host session's visible model.

Example:

ChatGPT Work on a strong model -> MCP call to Agent OS -> Agent OS chooses deterministic code or a cheaper API model -> compact result returned -> original Work model continues.

## Implementation phases

### Phase 1 — telemetry and reporting
- local telemetry store;
- privacy/redaction policy;
- provider usage adapters;
- usage summary/top-cost commands;
- tests with synthetic traces.

### Phase 2 — adaptive routing
- capability classes;
- provider adapters;
- route policy;
- validator-aware escalation;
- route explanation;
- no live-provider dependency in normal tests.

### Phase 3 — skill and automation mining
- repeated-pattern detection;
- candidate generation;
- replay/evaluation framework;
- explicit promotion/rejection;
- audit trail.

### Phase 4 — MCP/client delegation
- stable routed-task MCP surface;
- Claude Desktop/Code integration documentation;
- ChatGPT-compatible remote/app integration documentation;
- verify client limitations at implementation time.

## Acceptance criteria

Development should not consider this complete until:

- telemetry is privacy-safe and deletable;
- raw telemetry is gitignored/outside canonical Git state;
- routing is provider-neutral;
- deterministic execution is preferred where reliable;
- escalation works on validator/test failure;
- unavailable metrics remain explicitly unavailable;
- candidate skills/automations cannot silently self-promote;
- historical/synthetic replay can compare cost and quality;
- API secrets are never committed;
- MCP cannot falsely claim to switch the host client's active model;
- documentation clearly distinguishes host-model reasoning from delegated API calls;
- automated tests cover routing, escalation, privacy, provider failure, and candidate lifecycle.

## Development note

This roadmap item should be implemented as the smallest coherent extension of the existing routing, candidate, improvement, privacy, MCP, and validation systems. Inspect and reuse current Agent OS infrastructure before creating parallel subsystems.
