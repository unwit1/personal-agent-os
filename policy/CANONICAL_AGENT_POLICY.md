# Canonical agent policy

Use Personal Agent OS as the lifecycle gateway for controlled agent execution.
Do not load all available history.

1. Run `agent.begin_task` before controlled work, including ordinary prompts.
   Consume an existing gateway envelope instead of starting a duplicate task.
2. Use selective envelope context and `agent.continue_task` for further turns.
   Inspect project-local policy and compact Git state before meaningful work.
3. Treat project-local policies as authoritative for that project.
4. Preserve unrelated work and respect privacy, secret, and data boundaries.
5. Prefer deterministic checks and scripts before model review.
6. Record only durable, evidenced knowledge; proposed memories begin as candidates.
7. Run `agent.finish_task` after work with explicit decisions, evidence, validation,
   remaining work and useful candidate proposals. Mark summaries sanitized only
   when they contain engineering abstractions, never private source material.
   Postflight creates material handoffs and stages candidates. Record interruption
   through `agent.abort_task`; inspect local task status before retrying postflight.
8. Do not commit or push unless the current user request authorizes it.
9. During technical work, capture durable changes and improvements only as compact,
   deduplicated candidates with evidence references; they remain hypotheses until tested.
10. Form intake may retain sanitized template fingerprints only. Never store source
    documents, completed values, raw OCR, or personal data; Google is not its fallback.

Raw transcripts and broad history are archival sources, not default prompt input.
Derived indexes must remain disposable and rebuildable from canonical Git state.

Raw prompts may transit to a configured worker but are never task journal content.
Decision summaries are explicit artifacts, never private hidden chain-of-thought.
Tasks and reviewed evidence use stable task IDs; staging does not verify memory.
High-risk work reports independent review as unavailable when none is configured.
The controlled gateway enforces preflight and postflight around worker execution.
MCP and hosted UI instructions alone cannot intercept every prompt or enforce use.
