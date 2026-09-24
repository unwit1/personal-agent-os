# Dealing with Daedra claim relationship normalization — pass 01

This layer makes the existing contradiction and unresolved-identity work directly retrievable alongside the consolidated claim index.

## Relations materialized

- Contradiction / perspective / chronology relations: **7**
- Explicit uncertainty-boundary relations: **7**
- Total relation records: **14**

## Policy

This file does not flatten every relation into a binary contradiction.

It preserves the source index's own distinction among:
- direct doctrinal or taxonomic contradiction;
- partial metaphysical conflict;
- perspective conflict;
- official-record vs occult reconstruction;
- chronology-resolved reversal;
- terminology conflict;
- unresolved identity inference.

Temporal development and mere perspective differences are therefore not rewritten as simultaneous factual contradictions.

The relation layer is derived from:
- `claims/contradiction-index.jsonl`
- `claims/unresolved-identity-index.jsonl`

Those source indexes remain authoritative for explanatory notes.
