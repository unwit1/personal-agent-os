# VICN claim-graph coverage

Status: active / generated checkpoint

## Current graph

- Claim bundles: **15**
- Unique claims: **88**
- Stable claim-to-claim edges: **18**
- Duplicate claim IDs: **0**
- Dangling graph edges: **0**

## Status distribution

- supported: 39
- synthesis supported: 6
- supported as direct dialogue: 6
- unresolved / do not promote: 6
- unresolved: 5
- supported as attributed testimony: 4
- supported as attributed metaphysical interpretation: 2
- supported as attributed participant testimony: 1
- supported within UNSLAAD: 1
- supported within DAc0da: 1
- supported as DAc0da source claim: 1
- supported as direct participant testimony + actor corroboration: 1
- supported as attributed warning: 1
- supported as direct/source-local characterization: 1
- supported as attributed theory: 1
- modeling constraint: 1
- qualified / unresolved ontology: 1
- supported as attributed claim: 1
- supported provenance fact: 1
- supported as attributed doctrinal interpretation: 1
- supported as external-text claim: 1
- supported as reported historical record: 1
- supported as attributed contradictory testimony: 1
- supported as repeated in-world tradition: 1
- supported as Insight/mythic testimony: 1
- supported as attributed doctrinal testimony: 1
- supported as attributed interpretation: 1

## Promoted areas

- `vicn-arkved-oneiromancer-claims.md`
- `vicn-atmora-saarthal-night-of-tears-claims.md`
- `vicn-dream-without-a-dreamer-claims.md`
- `vicn-gc9-lyg-claims.md`
- `vicn-jacobee-aisha-ulliss-claims.md`
- `vicn-jhunal-identity-claims.md`
- `vicn-jills-claims.md`
- `vicn-khemkel-claims.md`
- `vicn-loveletter-fifth-era-claims.md`
- `vicn-lyg-claims.md`
- `vicn-oracle-iridescent-claims.md`
- `vicn-orlando-claims.md`
- `vicn-radiance-mnemo-li-memory-claims.md`
- `vicn-unslaad-dragon-soul-claims.md`
- `vicn-yngol-tsunaltir-tstunal-claims.md`

## Parent VICN relationship threads still needing dedicated claim-bundle review

- **Augur of the Obscure** — `augur-of-the-obscure-thread.md`
- **Rolls-On-Roads / Romion** — `rolls-romion-thread.md`
- **Hjalti / Alcaire / changing names** — `hjalti-alcaire-thread.md`
- **Elder Wood** — `elder-wood-thread.md`
- **Hare / word-rewriting** — `hare-word-rewriting-thread.md`
- **Harakk / Snow Whales / twin star** — `harakk-thread.md`
- **Yelem / Y.E.L.E.M. / dream machine** — `yelem-dream-machine-thread.md`
- **Snow Whales / Atmoran sky ecology** — `snow-whales-thread.md`
- **Maria / Marcus / Bruiant** — `maria-marcus-bruiant.md`
- **Atmora / Saarthal / Night of Tears** — `atmora-saarthal-night-of-tears-thread.md`
- **Jhunal identity matrix** — `jhunal-identity-matrix.md`
- **Laza / Owls / dragon experiments** — `laza-owls-dragon-experiments.md`
- **Gray Owl / Chick Trader / Anequina** — `gray-owl-chick-trader-anequina.md`
- **Holy Pipers** — `holy-pipers-thread.md`
- **Altano / Radiance** — `altano-radiance-thread.md`
- **Brain-Billies / memory recovery** — `brain-billies-memory-thread.md`
- **Blue Star** — `blue-star-thread.md`
- **Xero-Lyg** — `xero-lyg-thread.md`

## Machine retrieval surfaces

- `vicn-claim-index.jsonl` — compact structured claim rows.
- `vicn-claim-edges.jsonl` — explicit supports/contradicts/qualifies graph.

## Retrieval policy

Use the JSONL index first for claim discovery.

Retrieve a Markdown claim bundle when:
- source wording/provenance matters;
- the claim is disputed or unresolved;
- relation notes are needed.

Retrieve raw continuity source pages only when the answer needs exact record/dialogue evidence.

## Next promotion priority

Promote the remaining parent threads in small batches, prioritizing:
1. rare exact-name or institutional recurrence;
2. explicit contradiction pairs;
3. direct cross-work pointers;
4. source-reuse/provenance bridges.

Avoid promoting thematic-only similarities into claims.
