# Next Development Steps

1. Master-aware FormID resolver — complete for the supplied snapshot.
2. High-value decoders — MGEF, CTDA, PERK, WEAP, ENCH, CSTY, MOVT, AVIF and generic MGEF VMAD are complete.
3. Next bounded decoder batch — generic VMAD on PERK, NPC_, ARMO and ACTI. Keep QUST fragments/aliases separate.
4. Then decode QUST VMAD with a record-specific fragment/alias parser.
5. Continue semantic subdivision of spell/perk/combat evidence and overlay PERK CTDA gating onto AVIF tree topology.
6. Build a review-gated rule-candidate engine. Candidates must carry evidence IDs, scope, counterexamples and exception checks.
7. Add selective MCP/API queries for mechanics, behavior attachments, dependencies, deltas, observations, candidates and approved rules.
8. Later import external mods for Simonrim compatibility/balance analysis and deterministic patch planning.

Skyrim/DLC master evidence is still needed to replace external-baseline unknowns with exact vanilla-to-Simonrim deltas.
