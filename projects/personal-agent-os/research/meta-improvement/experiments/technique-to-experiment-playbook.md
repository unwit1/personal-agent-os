# Technique-to-Experiment Playbook

## Rule

No catalog technique becomes an Agent OS default because it has a good paper, a popular implementation, or a persuasive model explanation.

For a technique `AIT-xxxx`:

1. **Resolve the actual problem.** Name the observed failure/cost/friction it is meant to change.
2. **Check the simpler ladder first.** Delete work → deterministic substitution → cache/reuse → retrieval/context → prompt/tool schema → routing → test-time compute → stronger model → training.
3. **Form a falsifiable mechanism.** State *why* this technique should improve this exact task family.
4. **Choose one primary metric.** Guard against metric soup.
5. **Name hard guardrails.** Correctness/security/privacy can veto an apparent speed/cost gain.
6. **Use representative cases.** Include known failures, ordinary cases, tails, and a protected holdout when optimizing.
7. **Change as few variables as practical.** If interactions are the research question, use factorial/structured design rather than an undocumented bundle.
8. **Run cheapest valid experiment first.** Offline replay before shadow; shadow before canary; canary before full promotion.
9. **Preserve uncertainty.** Inconclusive is a valid result.
10. **Record negative results.** A failed technique on one model/task becomes capability evidence, not a reason to erase the technique.
11. **Verify rollback.** A rollback method that has never been exercised is a hypothesis.
12. **Monitor after promotion.** Offline wins can fail on production task mix.
13. **Revisit later.** A technique rejected for GPT-X or corpus vN may become worthwhile after model/tool/data changes.

## Minimal experiment example

```yaml
id: EXP-xxxx
techniques: [AIT-xxxx]
micro_optimizations: [MIC-xxxx]
hypothesis:
  statement: "Hybrid retrieval + reranking lowers missed evidence without increasing context tokens beyond 10%."
  mechanism: "Sparse search recovers exact identifiers; dense search recovers paraphrases; reranker removes merged noise."
  falsifier: "Recall does not improve on protected cases or task success regresses."
baseline:
  version_refs: [...]
treatment:
  changed_variables: ["retrieval candidate generation", "reranker"]
  held_constant: ["generator model", "prompt", "eval corpus"]
primary_metrics:
  - name: retrieval_recall_at_candidate_pool
    direction: increase
    success_threshold: ">= +5 percentage points"
guardrails:
  - name: task_success
    constraint: "noninferior within predefined margin"
    hard_veto: true
  - name: context_tokens
    constraint: "<= +10%"
    hard_veto: false
isolation:
  method: offline_replay
promotion:
  rollout_plan: "shadow, then bounded canary"
rollback:
  method: "restore previous retrieval config"
```

## Interaction tests

If a technique has a plausible interaction with another knob, encode that explicitly.

Examples:
- prompt compression × model family;
- chunk size × embedding model × reranker;
- reasoning effort × tool availability;
- prompt prefix layout × cache behavior;
- multi-agent fanout × task decomposability;
- context length × relevant-information position;
- repair strategy × failure class;
- proactivity threshold × interruption context.

Use factorial/fractional-factorial designs when multiple interactions matter. Do not call a five-change bundle a single improvement.
