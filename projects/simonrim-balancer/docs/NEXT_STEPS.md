# Next Development Steps

Status after full source exhaustion and initial candidate generation on 2026-09-23.

1. **P1 — Master-aware FormID resolver — COMPLETE for current snapshot**
   Canonical Form keys, source/master slots, resolved relations/effects and imported override chains are generated with zero resolution failures.

2. **P2 — Supplied-source semantic ingestion — COMPLETE**
   All 6,009 records across all 53 record types have an explicit treatment: full gameplay/behavior decoding, typed support, identity-only handling, presentation inventory, or plugin provenance. There are zero unmapped record types.

3. **P3 — Override/delta engine — COMPLETE where the baseline is supplied; BLOCKED externally**
   Exact raw/typed/semantic deltas are generated when the prior imported record exists. The remaining 1,619 external-baseline overrides require Skyrim/Update/DLC record bodies rather than more work on the four supplied archives.

4. **P4 — Source behavior / optional-module semantics — COMPLETE for supplied source**
   VMAD fragments/aliases, Papyrus PSC behavior, runtime config, SPID/KID, Scrambled Bugs settings, FOMOD semantics, crafting/distribution, controller quests, world support and presentation inventories are captured.

5. **P5 — Rule-candidate engine — STARTED / WORKING**
   273 review candidates exist. Evidence strength, generalizability and promotion readiness are separate axes. 17/17 nontrivial author-statement candidates have implementation corroboration. Approved rules remain 0.

6. **P6 — Baseline expansion — NEXT DATA PRIORITY**
   Import matching Skyrim.esm, Update.esm and required DLC/Creation master record bodies for the 1,619 unresolved external baselines. Recompute exact deltas and candidate confidence afterward.

7. **P7 — Candidate synthesis and review**
   Cluster related candidates into design-principle families, attach counterexamples/exceptions, deduplicate near-equivalent observations and promote only narrowly scoped, evidence-backed rules.

8. **P8 — Analysis API/MCP**
   Add selective queries for mechanics, dependencies, deltas, evidence, candidates, approved rules, exceptions and compatible design space.

9. **P9 — External-mod analyzer**
   Import a target mod and produce Simonrim compatibility/balance findings with separate Strict and Complementary modes.

10. **P10 — Patch planner/generator**
    Produce deterministic patch specifications and eventually plugin patches.
