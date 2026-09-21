# Scene resolution batch 03

Continued through the remaining high-priority Gerhard / Ja'zel scene cluster.

## Scene records normalized

- `01730E zzzGHMq05ChScGerhard`
- `00C98C zzzGHMq05ScJazelMad`
- `00C969 zzzGHMq05ScJazelBoy`
- `00C961 zzzGHMq05ScJazelChild`

## Preservation decision

These records are now indexed as distinct authored scenes, but no dialogue line is assigned solely from the human-readable EDID. Exact attribution continues to require SCEN Actor ID → QUST alias → filled reference/NPC, followed by DIAL → INFO.

This is consistent with documented Skyrim scene behavior: a scene dialogue action's Actor ID corresponds to a quest reference alias, and INFO conditions remain active. 

## Next extraction

Decode each scene's action blocks and emit exact dialogue rows where the alias chain resolves uniquely. If Child/Boy resolve to different aliases or references, preserve that distinction in the identity graph.
