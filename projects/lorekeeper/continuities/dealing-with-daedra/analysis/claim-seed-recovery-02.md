# Dealing with Daedra claim-seed recovery — refinement pass 02

## Problem discovered

The consolidated claim-index audit found nine missing numeric claim IDs:
- dwd-187 through dwd-190;
- dwd-200 through dwd-204.

These were not intentionally unused IDs.

Historical Git commits showed that the claims had been created during semantic pass 13, but two later batches reused the same claim-seed filenames and replaced the earlier contents:

- commit `9bb09ceb210f4f4ca2dfa424ad1d51c8af4ea31b` originally added Family-support claims dwd-187–190 in `claim-seeds-13i.jsonl`;
- commit `7738c5d2b407c56525d8f80ab9f6810ce3d32dae` originally added Drelas/transmutation claims dwd-200–204 in `claim-seeds-13k.jsonl`.

The current repository later contained different claims under those same filenames, proving filename reuse caused claim-seed loss while the prose analysis survived.

## Recovery

The historical claim rows were recovered exactly from the Git commit diffs and restored to new non-colliding files:

- `claims/claim-seeds-13i-family-recovered.jsonl`
- `claims/claim-seeds-13k-drelas-recovered.jsonl`

The consolidated `claims/claim-index.jsonl` was then rebuilt to include them.

## Post-recovery integrity

- Numeric claims: **341**
- Numeric range: **dwd-001 through dwd-341**
- Missing numeric IDs: **0**
- Specialized named claims: **18**
- Total indexed claim records: **359**
- Duplicate claim IDs: **0**
- Exact duplicate subject/predicate/object triples detected during consolidation: **0**

## Prevention rule

Claim-seed filenames are append-only identities.

Do not reuse a previous batch filename for a later semantic batch. If a batch label collides, create a more specific filename rather than replacing the older file. Historical claim bundles remain provenance artifacts even after their claims are consolidated into `claim-index.jsonl`.
