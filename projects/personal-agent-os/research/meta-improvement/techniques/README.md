# AI Improvement Technique Encyclopedia

Status: active breadth-first catalog  
As of: 2026-09-24

## Purpose

This catalog records **techniques, not commandments**. A method remains discoverable even when it is model-specific, expensive, superseded, dangerous, or contradicted by newer evidence.

The goal is to preserve the solution space for future models while preventing "paper says it worked once" from becoming architecture policy.

Every technique should answer:

1. What layer does it modify?
2. What mechanism is supposed to produce the improvement?
3. What evidence exists?
4. On what tasks/models/environments was that evidence produced?
5. What does it cost in tokens, latency, compute, complexity, data, and maintenance?
6. What are the known failure modes?
7. When should Agent OS consider it?
8. When should Agent OS explicitly avoid it?
9. What eval would have to pass before adoption?
10. Can a simpler intervention achieve the same goal?

## Intervention layers

The encyclopedia spans the full stack:

```text
DATA
  corpus selection
  cleaning / deduplication
  synthetic data
  active learning
  curriculum
  contamination control

TRAINING / ADAPTATION
  pretraining allocation
  instruction tuning
  SFT
  LoRA / QLoRA
  RLHF / RLAIF
  preference optimization
  distillation
  process supervision
  fine-tuning / reinforcement fine-tuning

MODEL / INFERENCE
  model choice
  quantization
  batching
  KV-cache management
  prompt/prefix caching
  speculative decoding
  test-time compute
  sample-and-select
  constrained decoding

PROMPT / CONTEXT
  instruction design
  exemplars
  example selection/order
  decomposition
  reasoning scaffolds
  prompt optimization
  context packing
  context compression

RETRIEVAL / MEMORY
  sparse / dense / hybrid search
  reranking
  query rewriting
  contextual chunks
  hierarchical retrieval
  graphs
  temporal memory
  consolidation
  forgetting / reconsolidation
  skill extraction

TOOLS / AGENTS
  tool schemas
  tool selection
  deterministic substitution
  planning
  ReAct-style loops
  workflows
  multi-agent decomposition
  review / verifier agents
  durable execution

EVALUATION / CONTROL
  deterministic validators
  model graders
  pairwise evaluation
  process/outcome verification
  adversarial tests
  shadow/canary rollout
  error budgets
  authorization / taint controls

HUMAN SYSTEM
  proactivity
  interruption timing
  explainability
  correction/undo
  approval design
  cognitive-load reduction
```

## Evidence doctrine

Technique catalog entries distinguish:

- **foundational** — broad, well-established engineering/research principle;
- **production_pattern** — used in deployed systems with strong engineering evidence;
- **replicated_research** — multiple research lines support the mechanism;
- **promising_research** — strong paper evidence but task/model dependence remains;
- **early_research** — interesting but insufficiently reproduced;
- **mixed_evidence** — gains depend materially on conditions;
- **negative_result** — evidence shows a common intuition can fail;
- **historical** — useful lineage, but newer models may invalidate assumptions.

A future model must not infer adoption priority from maturity alone. A foundational technique can be irrelevant to a particular task, while early research may be worth an isolated experiment.

## Optimization doctrine

For any candidate intervention, test in this order where applicable:

```text
remove unnecessary work
  -> deterministic code
  -> cache/reuse
  -> better retrieval/context
  -> better prompt/tool schema
  -> better routing
  -> more test-time compute
  -> stronger model
  -> fine-tuning/training
```

This is an economic heuristic, not a law. High-risk tasks may require a stronger model or independent verification immediately.

## Important anti-pattern

Do not combine five techniques, observe improvement, and claim all five work. Change one controllable variable at a time where practical, preserve exact configuration, and evaluate interactions separately.
