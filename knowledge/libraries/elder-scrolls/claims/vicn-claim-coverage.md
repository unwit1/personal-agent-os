# VICN claim-graph coverage

Status: active / generated checkpoint

## Current graph

- Claim bundles: **31**
- Unique claims: **188**
- Stable claim-to-claim edges: **45**
- Duplicate claim IDs: **0**
- Dangling graph edges: **0**
- Self-edges: **0**

## Status distribution

- supported: 79
- synthesis supported: 20
- unresolved / do not promote: 17
- unresolved: 8
- supported as direct dialogue: 7
- modeling constraint: 5
- supported as direct testimony: 5
- supported as attributed testimony: 4
- unsupported by current evidence / do not merge: 2
- supported as attributed cosmology: 2
- supported as attributed metaphysical interpretation: 2
- supported as dream content: 2
- supported as attributed participant testimony: 1
- supported within UNSLAAD: 1
- supported as direct self-report: 1
- supported as attributed written/source statement: 1
- supported as direct explanation: 1
- supported as attributed technical/metaphysical record: 1
- supported as direct dialogue/branch outcome: 1
- supported within DAc0da: 1
- supported as DAc0da source claim: 1
- supported as attributed historical testimony: 1
- supported as direct participant testimony + actor corroboration: 1
- supported as memory testimony: 1
- supported as attributed characterization: 1
- supported as direct dialogue/tradition: 1
- supported as memory/ghost testimony: 1
- supported as attributed warning: 1
- supported as source-local biography: 1
- supported as direct/source-local characterization: 1
- supported as attributed theory: 1
- supported as high-confidence source-local hypothesis: 1
- qualified / unresolved ontology: 1
- supported as attributed claim: 1
- supported provenance fact: 1
- contradicted / do not promote: 1
- supported as attributed doctrinal interpretation: 1
- supported as external-text claim: 1
- supported as reported historical record: 1
- supported as attributed contradictory testimony: 1
- supported as repeated in-world tradition: 1
- supported as mythic/dialogue tradition: 1
- supported as Insight/mythic testimony: 1
- supported as attributed doctrinal testimony: 1
- supported as attributed interpretation: 1
- supported as direct ecology testimony: 1
- supported as direct participant testimony: 1

## Promoted bundles

- `vicn-altano-radiance-claims.md`
- `vicn-arkved-oneiromancer-claims.md`
- `vicn-atmora-saarthal-night-of-tears-claims.md`
- `vicn-augur-of-the-obscure-claims.md`
- `vicn-blue-star-claims.md`
- `vicn-brain-billies-claims.md`
- `vicn-dream-without-a-dreamer-claims.md`
- `vicn-elder-wood-claims.md`
- `vicn-gc9-lyg-claims.md`
- `vicn-gray-owl-chick-trader-anequina-claims.md`
- `vicn-harakk-claims.md`
- `vicn-hare-word-rewriting-claims.md`
- `vicn-hjalti-alcaire-claims.md`
- `vicn-holy-pipers-claims.md`
- `vicn-jacobee-aisha-ulliss-claims.md`
- `vicn-jhunal-identity-claims.md`
- `vicn-jills-claims.md`
- `vicn-khemkel-claims.md`
- `vicn-laza-owl-dragon-experiments-claims.md`
- `vicn-loveletter-fifth-era-claims.md`
- `vicn-lyg-claims.md`
- `vicn-maria-marcus-bruiant-claims.md`
- `vicn-oracle-iridescent-claims.md`
- `vicn-orlando-claims.md`
- `vicn-radiance-mnemo-li-memory-claims.md`
- `vicn-rolls-romion-claims.md`
- `vicn-snow-whales-claims.md`
- `vicn-unslaad-dragon-soul-claims.md`
- `vicn-xero-lyg-claims.md`
- `vicn-yelem-dream-machine-claims.md`
- `vicn-yngol-tsunaltir-tstunal-claims.md`

## Parent VICN relationship coverage

- Indexed parent relationship entries: **31**
- Covered by one or more claim bundles: **31**
- Still needing dedicated claim review: **0**

- **All currently indexed parent relationship threads are covered.**

Some parent threads intentionally map to a combined claim bundle rather than a one-file/one-bundle mirror. For example:
- `jhunal-saarthal-owls-thread.md` is covered by the Jhunal identity and Atmora/Saarthal claim bundles;
- GC9/LYG and Lyg have separate but cross-linked claim bundles;
- parent threads remain richer human-readable syntheses while JSONL is the compact claim surface.

## Machine retrieval surfaces

- `vicn-claim-index.jsonl` — compact structured claim rows.
- `vicn-claim-edges.jsonl` — explicit supports/contradicts/qualifies graph.

## Validation policy

A graph refresh must reject:
- duplicate stable claim IDs;
- dangling stable claim references;
- self-edges.

Prose under Supports/Contradicts/Qualifies that is not a valid stable claim ID stays as a relation note instead of entering the edge graph.

## Retrieval policy

Use the JSONL index first for claim discovery.

Retrieve a Markdown claim bundle when:
- source wording/provenance matters;
- the claim is disputed or unresolved;
- relation notes are needed.

Retrieve raw continuity source pages only when the answer needs exact record/dialogue evidence.

## Next phase

Parent-thread promotion is now effectively complete for the current VICN relationship index.

Next high-value work:
1. contradiction-oriented indexes over the claim graph;
2. entity/relationship materialization from the claim bundles;
3. source-ID normalization where evidence currently points only to prose dossiers;
4. selective promotion of high-value work-local UNSLAAD claims not represented by parent threads;
5. deterministic regeneration/validation tooling so future claim-bundle changes do not require manual index maintenance.
