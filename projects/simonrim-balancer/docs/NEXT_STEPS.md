# Next Development Steps

Status after the 2026-09-23 continuation pass:

1. **P1 — Master-aware FormID resolver — COMPLETE for current snapshot**
   Canonical Form keys, source/master slots, resolved relations/effects, and imported override chains are generated with zero resolution failures.

2. **P2 — High-value field decoders — IN PROGRESS**
   Complete now: MGEF DATA, CTDA, PERK effect-entry structures, WEAP DNAM/critical/reference fields, ENCH ENIT/effect composition, CSTY combat-style fields, and MOVT movement profiles. Next: AVIF perk trees and VMAD attachments/property values.

3. **P3 — Override/delta engine — PARTIAL / WORKING**
   Exact raw and typed deltas work whenever the prior master record is also imported. Current snapshot has 537 exact imported baselines. Import Skyrim/DLC master evidence later to cover the remaining 1,619 external-baseline overrides.

4. **P4 — Domain baselines — STARTED**
   Current descriptive outputs cover spell, perk, weapon, enchantment, combat-style, and movement evidence. Next subdivide by semantic role, remove compatibility/reversion pollution, add perk-tree progression profiles, and identify explicit exceptions.

5. **P5 — Rule-candidate engine — NEXT ARCHITECTURAL MILESTONE**
   Generate evidence-backed hypotheses from observed patterns + author metadata + deltas, but never auto-promote to approved rules. Every candidate needs evidence IDs, scope, confidence basis, counterexamples, and exception checks.

6. **P6 — Analysis API/MCP**
   Add selective queries for records, mechanics, dependencies, deltas, observed patterns, candidates, and approved rules.

7. **P7 — External-mod analyzer**
   Import a target mod and generate compatibility/balance findings against version-scoped approved rules and patterns.

8. **P8 — Patch planner/generator**
   Produce deterministic patch specifications and eventually plugin patches.
