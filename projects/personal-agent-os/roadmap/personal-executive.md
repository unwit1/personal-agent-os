# Personal Executive Function Roadmap

Status: planned  
Owner: Personal Agent OS  
Created: 2026-09-18

## Vision

Evolve Personal Agent OS from a project-context layer into a model-independent personal executive assistant that reduces the user's need to remember, organize, prioritize, initiate, and repeatedly explain work.

The Personal Executive sits above project-specific and provider-specific agents. Its primary optimization target is not engagement or number of interactions. It is:

> Minimize forgotten commitments, unnecessary decisions, abandoned intentions, context-switching, and avoidable interruptions while preserving user control.

Git remains canonical for durable, non-sensitive Agent OS knowledge. Sensitive/work data must obey domain-specific privacy boundaries and may remain local. Derived indexes and caches remain rebuildable.

## Core design principles

1. **Attention is scarce.** Surface the smallest useful decision or next action.
2. **Organization is the system's job.** Accept messy brain dumps and structure them automatically.
3. **Progressive autonomy.** Every action has an autonomy level: OBSERVE, SUGGEST, PREPARE, ASK_THEN_ACT, or AUTO_ACT.
4. **Selective context.** Retrieve only context relevant to the current decision/task.
5. **Learn from outcomes.** Accepted, rejected, delayed, modified, ignored, successful, and failed actions become evidence.
6. **Ask high-value questions.** Proactive questions must close a meaningful knowledge gap; curiosity alone is insufficient.
7. **Explain recommendations.** The user can ask why something was surfaced or prioritized.
8. **Reversible memory.** Learned preferences and assumptions carry provenance, confidence, timestamps, and supersession.
9. **Safety boundaries.** Sending communications, changing appointments, spending money, deleting data, or other consequential actions require explicit policy/authorization.
10. **Provider neutrality.** ChatGPT, Codex, Claude, Siri, local models, and future agents are interfaces/reasoning engines; Agent OS owns durable state.

## Target architecture

Inputs (chat, voice, calendar, email, documents, project agents)
→ Event Bus
→ Context/Entity Resolution
→ Personal Executive
→ Executive Queue
→ Attention Manager / Delegation Engine
→ user decision OR authorized agent action
→ Outcome Event
→ Learning / candidate memory / skill evolution

## EXEC-0 — Executive foundation

Define canonical schemas and APIs for:
- task
- commitment
- project
- next_action
- blocker
- waiting_on
- decision_request
- question
- idea
- appointment
- communication
- attention_state
- executive_event
- executive_queue_item
- outcome

Add stable entity IDs and provenance. Support created_at, updated_at, last_confirmed, confidence, source, sensitivity/domain, expires_at, and superseded_by where applicable.

Acceptance criteria:
- schemas validate deterministically;
- sensitive domains can be marked local-only;
- all later EXEC features can communicate through these contracts.

## EXEC-1 — Next Action Engine

Every active project should expose:
- goal;
- current state;
- concrete next action;
- blockers;
- waiting-on dependencies;
- decisions needed from the user;
- work agents can perform without the user.

Detect projects that have no actionable next step, have stalled, or repeatedly get deferred. Convert vague work such as "work on project X" into a small executable next action.

Acceptance criteria:
- active projects can be queried for one next action;
- stalled/no-next-action projects are detectable;
- project agents can distinguish user decisions from delegable work.

## EXEC-2 — Knowledge-Gap / Interview Engine

Maintain explicit unknowns that would materially improve assistance. Score candidate questions by expected future utility, recurrence, confidence gap, urgency, interruption cost, and sensitivity.

Prefer opportunistic questions during relevant conversations. Enforce a question budget so Agent OS does not interrogate the user.

Example unknowns:
- prioritization preferences;
- preferred working windows;
- recurring sources of friction;
- what may be automated;
- communication preferences by context;
- project-specific design preferences.

Acceptance criteria:
- low-value questions are discarded/deferred;
- each proactive question records why it was worth asking;
- answers become candidate durable knowledge rather than silently rewriting canonical memory.

## EXEC-3 — Brain Dump Processor

Accept unstructured text/voice and extract candidate:
- tasks;
- ideas;
- reminders;
- appointments;
- decisions;
- project updates;
- research requests;
- communications/follow-ups.

Resolve known entities/projects where confidence is sufficient. Ask only about ambiguity that materially blocks correct routing. Preserve original input ephemerally where privacy policy permits; persist structured derived records instead of raw sensitive content by default.

Acceptance criteria:
- one utterance can produce multiple typed records;
- duplicates are detected;
- unresolved references become clarification items rather than guessed assignments.

## EXEC-4 — Executive Prioritizer

Build an Executive Queue that scores possible attention items using:
- deadline/urgency;
- importance;
- dependency/blocking impact;
- estimated effort;
- available time;
- current context;
- waiting-on status;
- repeated deferral;
- interruption cost;
- user-stated priority.

Output should normally be a small number of actions, not a ranked backlog.

Every recommendation must be explainable using concrete contributing factors.

## EXEC-5 — Attention Manager

Support operational states such as:
- focused;
- normal;
- low_energy;
- overwhelmed;
- do_not_disturb.

These are user-controlled context states, not medical diagnoses. They modify interruption thresholds and task presentation.

Implement interruption budgets, deduplication, cooldowns, urgency thresholds, and batching.

## EXEC-6 — Delegation Engine

Classify work into:
- requires user;
- agent can research;
- agent can prepare;
- agent may execute after approval;
- explicitly authorized autonomous execution.

Route work to appropriate agents/providers using Agent OS context packets. Require validation before consequential outputs/actions. Record results as events and handoffs.

## EXEC-7 — Daily Executive Brief

Generate a deliberately compact daily brief centered on:
- today's real commitments;
- preparation required;
- communications needing attention;
- blockers requiring a user decision;
- one or a few high-value next actions;
- useful forgotten/stalled items only when relevant.

Avoid dumping the entire backlog.

## EXEC-8 — Rescue Mode

Provide a first-class "What should I do?" / "I'm overwhelmed" workflow.

Behavior:
1. inspect immediate calendar/commitments and deadlines;
2. suppress nonessential backlog;
3. choose one manageable next action;
4. explain only enough to make starting easy;
5. optionally prepare/delegate adjacent work;
6. re-evaluate after completion.

Acceptance criterion: Rescue Mode can return one actionable step without requiring the user to manually triage all projects.

## EXEC-9 — Outcome Learning

Capture evidence from:
- accepted recommendations;
- rejected recommendations;
- modifications;
- ignored/deferred items;
- completed actions;
- failed actions;
- repeated patterns.

Use this evidence to propose preference, routing, prioritization, skill, and automation candidates. Do not treat behavior as certain intent. Promotion remains reviewable and provenance-backed.

## EXEC-10 — Calendar Intelligence

Integrate calendar events with project/person/task context.

Capabilities:
- preparation detection;
- travel/setup buffers when reliable data exists;
- deadline and appointment awareness;
- conflict detection;
- pre-event briefing;
- post-event capture;
- scheduling preference learning;
- suggested rescheduling/preparation.

Calendar writes remain subject to progressive-autonomy policy.

## EXEC-11 — Communication Intelligence

Connect email/messages to people, projects, commitments, and tasks.

Capabilities:
- detect likely response/follow-up requirements;
- summarize low-priority information;
- prepare contextual drafts;
- identify promises/commitments;
- create follow-up events;
- surface unanswered important threads.

Sending messages requires the configured authorization level.

## EXEC-12 — Proactive Executive

Consume events such as:
- project.stalled;
- agent.blocked;
- decision.required;
- appointment.approaching;
- communication.needs_response;
- task.overdue;
- idea.unresolved;
- preference.observed;
- context.changed.

For every event answer:
1. Does the user need to know/do anything?
2. If yes, when is the least disruptive useful time?
3. Can Agent OS prepare or delegate work first?
4. What is the smallest decision/action to surface?

## EXEC-13 — Voice Executive

Create a provider-neutral Voice Gateway, beginning with an authenticated API suitable for Siri Shortcuts and later a native iPhone/Watch client.

Initial intents:
- Ask Agent OS;
- Brain Dump;
- Remember/Capture This;
- What Should I Do?;
- Add Project Idea;
- Start/Change Attention State;
- Daily Brief.

Voice is an interface to the same Executive/Event Bus, not a separate memory system.

## EXEC-14 — Executive Autonomy

Allow explicitly authorized low-risk actions to execute automatically under policy.

Requirements:
- per-action autonomy policy;
- audit trail;
- idempotency;
- rollback where possible;
- confidence thresholds;
- escalation on ambiguity;
- domain privacy controls;
- kill switch / global pause;
- no inferred expansion of authorization.

## Event Bus

Introduce standardized events instead of allowing integrations to write directly to canonical memory.

Initial vocabulary:
- conversation.completed
- idea.captured
- task.created
- task.completed
- task.deferred
- project.modified
- project.stalled
- decision.required
- decision.made
- agent.blocked
- agent.completed
- appointment.created
- appointment.approaching
- communication.received
- communication.needs_response
- preference.observed
- skill.used
- skill.failed
- outcome.recorded
- context.changed

Consumers decide whether an event is ignored, deferred, processed, delegated, or surfaced.

## Executive explainability

Every surfaced recommendation should be able to answer "Why?" with evidence such as deadline, dependency, available time, repeated deferral, upcoming appointment, waiting person, or explicit user priority.

Do not expose hidden model reasoning. Store concise decision factors and source references.

## Privacy and storage

Use domain-aware storage zones:
- public/non-sensitive durable knowledge: private Git canonical repository as appropriate;
- personal durable preferences/projects: private Agent OS canonical state;
- work/sensitive document processing: local-only when policy requires;
- secrets/credentials: never canonical plaintext;
- ephemeral raw captures: expire or discard after structured extraction when feasible.

Cross-zone learning should prefer sanitized derived knowledge over raw source material.

## Implementation order

**Milestone A — Executive Core:** EXEC-0, Event Bus, EXEC-1, basic Executive Queue.

**Milestone B — Capture & Interaction:** EXEC-2, EXEC-3, EXEC-8.

**Milestone C — Attention & Delegation:** EXEC-4, EXEC-5, EXEC-6, EXEC-7.

**Milestone D — Learning:** EXEC-9 plus integration with existing candidate-memory and skill systems.

**Milestone E — Life Integrations:** EXEC-10 and EXEC-11.

**Milestone F — Proactivity & Voice:** EXEC-12 and EXEC-13.

**Milestone G — Controlled Autonomy:** EXEC-14 after sufficient outcome history, auditing, and policy validation.

## Near-term engineering tasks

1. Add executive event and queue schemas.
2. Implement append-only local/event storage plus deterministic event IDs and deduplication.
3. Add project next-action/blocker/decision fields without breaking existing project-state files.
4. Implement `agent-os exec next`, `agent-os exec capture`, and `agent-os exec explain`.
5. Expose read-oriented Executive methods over MCP.
6. Add tests for ambiguous capture, duplicate events, attention filtering, privacy zones, and authorization boundaries.
7. Integrate existing candidate capture/curation so learned observations remain reviewable.
8. Add compact context-packet support for executive decisions.
9. Prototype Rescue Mode before external calendar/email writes.
10. Add Voice Gateway only after the same intents work through CLI/MCP.

## Success metrics

Track system quality using outcomes rather than engagement:
- fewer active projects without a next action;
- fewer forgotten/overdue commitments;
- reduced repeated prompting/context restatement;
- percentage of agent-blocking questions resolved;
- recommendation acceptance/modification/ignore rates;
- number of tasks safely delegated;
- interruption rate and dismissed-interruption rate;
- successful recovery of stalled projects;
- context/token cost per completed outcome;
- zero unauthorized consequential actions.

These metrics should be privacy-preserving and local/aggregate where appropriate.
