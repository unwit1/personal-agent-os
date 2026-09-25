# Skyrim Mod Factory — Progress Checkpoint and Resume Point

Updated: 2026-09-25
Status: canonical resume checkpoint

## Why this exists

Future Agent OS / ChatGPT / Claude / Codex sessions **must not restart this project from broad Skyrim-modding research**.

The broad knowledge-ingestion phase is already mature. Resume from the executable automation gaps in this file unless a new mod idea exposes a genuinely uncovered subsystem.

## Current measured repository state

- Skyrim terminology/reference modules: **165**
- Tool/framework capability entries: **54**
- Implementation patterns: **46**
- Analyzer rules: **24**
- Validation gates: **30** (G00–G29)
- Skyrim-specific JSON Schemas: **41**
- Mod Factory Python tools: **39**
- Mod Factory unit-test modules: **33**
- Dedicated adapter manifests: **50** plus capability-only/manual/framework entries

These are repository counts, not estimates of ecosystem completeness.

## Maturity scale

- **M0 — idea only**: discussed but not persisted.
- **M1 — documented**: architecture/semantics are written and source-backed.
- **M2 — typed**: machine-readable schema/registry/intent exists.
- **M3 — executable**: deterministic tool can perform or validate the operation.
- **M4 — regression-tested**: executable path has fixtures/tests/self-checks.
- **M5 — closed-loop autonomous**: Agent OS can plan → execute → read back → diagnose → safely repair/retry → prove postconditions without ordinary user intervention.

## Current subsystem maturity

| Subsystem | Maturity | Current state |
|---|---:|---|
| Skyrim technical knowledge / terminology | M4 | Broad system coverage plus source-derived finite catalogs and version provenance. |
| Mod idea decomposition / architecture selection | M4 | Feature intent, implementation patterns, provider registry, least-invasive selection rules, readiness resolver. |
| Project manifest / typed contracts | M4 | Project, toolchain, DAG, quality, test, runtime-patch, repair, regression, adapter and report schemas. |
| Tool/framework discovery registry | M4 | 54 capability entries with adapter manifests, gaps, safety and provenance. |
| Toolchain preflight / version pinning | M4 | Toolchain doctor, dependency lock model, current-version research surfaces. |
| Build DAG planning | M4 | Incremental DAG compiler with invalidation triggers and layer-specific generate/validate nodes. |
| Generic adapter execution | **M4** | DAG executor now has end-to-end fake-toolchain coverage, typed artifact contracts, per-node checkpoint/resume, content-hash invalidation and mutation-aware retry checkpoints. |
| Validation gates | **M4** | G00–G29 are machine-readable and evidence-aware; required blocking warnings prevent a final PASS. |
| Schema triangulation | **M4 static baseline** | xEdit Check-for-Errors parser/wrapper, xDump semantic producer, pinned Mutagen semantic producer, canonical FormKey reconciliation, coverage-aware cross-oracle comparison and reusable FormID/master/ESL/CTDA/VMAD analyzers are implemented/tested. CK/runtime quorum remains P1 runtime work. |
| Runtime patch config generation | M4 partial | Typed intent plus deterministic SPID/KID/BOS renderers; FLM/SkyPatcher/OAR and more still need typed renderers. |
| Static plugin generation | M3 | Mutagen/houseCARL/Synthesis/Spriggit architecture and adapters exist; generic semantic record generator is not yet universal. |
| Papyrus build automation | M4 static | Pyro/compiler/tooling adapters plus PSC property extraction, typed symbol inventories and inheritance-aware VMAD binding validation; runtime binding behavior still needs the game harness. |
| Native SKSE build automation | M3/M4 | CommonLib/CMake configure/build adapters; runtime hook assertion still requires game harness. |
| Mesh/NIF/TRI automation | M2/M3 | PyNifly/Blender/NifSkope/CAO adapters and invariants documented; universal validator/repair pass still incomplete. |
| Texture/material automation | M2/M3 | DirectXTex/ParallaxGen/renderer knowledge exists; asset-generation + visual validation loop remains incomplete. |
| Animation/behavior automation | M3 | Pandora/OAR ecosystem mapped; behavior generation runnable; runtime movement/contact validation remains necessary. |
| Creation Kit world/navmesh/quest automation | M2 | CK/CKPE bridge design and adapters exist, but reliable headless authoring worker is not complete. |
| Runtime testing | M2/M3 | devbench/SkyTest/SkyLink/SkyrimNet/AutoTest research/adapters; local Windows/MO2 closed-loop harness still not production-ready. |
| Crash/log diagnosis | M2/M3 | Error catalog/analyzer rules exist; generic parser + signature clustering by build ID remains incomplete. |
| Save migration validation | M2/M3 | ESS/Fallrim knowledge, schemas and gate policy exist; automated migration fixture runner needs integration. |
| Auto repair planning | **M4** | Evidence-first planner is typed/tested and selects automatic mutation only when a registered reversible handler and provable postconditions exist. |
| Auto repair execution | **M4 baseline** | Bounded loop can classify a failed step, select a registered automatic handler, checkpoint outputs/state, invalidate only the downstream closure, rerun via the normal executor, compare postconditions, roll back regressions and escalate unproven results. `--auto-repair` connects this loop to the executor. Current executable mutation coverage is intentionally narrow: generated-output invalidation/regeneration is the registered automatic handler. |
| Bug → regression learning | **M4** | Regression candidates are typed and successful repairs automatically promote only when explicit root-cause + reproduction evidence already exists. |
| Packaging/FOMOD | M2 | Gate and architecture exist; deterministic typed FOMOD generator + option-matrix simulator still needed. |
| Release audit/reproducibility | M3 | Build report/provenance/audit schemas exist; final executor integration remains incomplete. |
| Dependency/license audit | M3 | Policies/validators exist; needs stronger automatic source/license resolution. |
| Tool/framework update watching | M1/M2 | Version/provenance policy and watchlist exist; recurring automated watcher/regression trigger not finished. |
| Natural-language idea → manifest compiler | M2 | Question-preemption and typed intent are strong, but a dedicated NL compiler that emits complete manifest/feature intent is still missing. |

## What was just fixed / added at this checkpoint

Small frequent commits now exist for:

1. reusable `run_adapter()` execution primitive;
2. adapter execution regression tests;
3. build-report schema support for rich adapter evidence;
4. regression test proving real adapter records fit build-report schema;
5. typed `skyrim-execution-context-v1`;
6. conservative `execute_build_dag.py` orchestration engine;
7. DAG executor tests;
8. machine-readable G00–G29 validation-gate schema;
9. executable validation-gate registry;
10. evidence-aware gate evaluator + tests;
11. CI structural validation for the gate registry;
12. phase-aware gate integration into the DAG executor;
13. two-node fake-toolchain end-to-end executor integration coverage;
14. typed intermediate-artifact contracts with executor enforcement;
15. typed retry checkpoints plus mutation-aware retry fail-closed behavior;
16. deterministic repair-checkpoint restore, including deletion of outputs absent before repair;
17. post-repair assessment that distinguishes repaired, unproven/escalated and failed/worse outcomes;
18. automatic rollback when a repair rerun regresses;
19. typed regression-candidate schema and callable promotion primitive;
20. automatic regression-candidate hook for eligible validated repairs;
21. bounded `run_repair_loop.py` orchestration preserving original failure evidence;
22. executor `--auto-repair` bridge with nested-run recursion prevention;
23. explicit `jsonschema` installation in the Mod Factory CI workflow;
24. typed xEdit Check-for-Errors report schema, parser, wrapper and adapter;
25. conservative xDump semantic normalizer with raw evidence retention;
26. canonical load-order FormID → Mutagen FormKey mapping for full/light records;
27. pinned Mutagen.Bethesda 0.54.4 semantic exporter + schema-validating harness/adapter;
28. typed semantic diff reports with fail-closed identity comparability;
29. coverage-aware Mutagen/xDump differential oracle;
30. typed static invariant report model;
31. runtime-aware FormKey/master/ESL invariant analyzer + tests;
32. CTDA full-predicate schema/analyzer + mutation tests;
33. VMAD/Papyrus symbol schemas + inheritance-aware binding analyzer/tests;
34. PSC property extraction + schema-valid Papyrus symbol inventory output;
35. project-plugin xDump semantic export wrapper + adapter.

## Current resume point

**Do not restart at terminology research.**

Continue from:

### P0 — Closed-loop executor baseline — COMPLETE

The original P0 baseline is now implemented:

1. ✅ end-to-end fake adapter/toolchain integration coverage;
2. ✅ declared intermediate-artifact JSON-schema contracts and fail-closed enforcement;
3. ✅ per-node persisted checkpoint/resume;
4. ✅ content-hash invalidation with downstream dependency fingerprints;
5. ✅ mutation-aware safe-retry checkpoint records;
6. ✅ bounded automatic repair path: classify → policy/handler selection → checkpoint → invalidate/mutate → minimal rerun → postcondition compare → rollback if worse → eligible regression promotion;
7. ✅ final required blocking gate warnings/needs-review prevent PASS.

Important scope boundary: **P0 completion does not mean the entire Mod Factory is M5.** Automatic mutation remains deliberately limited to registered reversible handlers, and the runtime/visual/CK parts below still need executable harnesses and validators.

Operational CI note (2026-09-24): GitHub Actions workflow files are configured and the Mod Factory workflow now installs `jsonschema`, but current Actions jobs are ending without an assigned runner/steps (`runner_id=0`). Do not treat those no-runner failures as test evidence. Re-run the suite once runner availability is restored.

## Current resume point

**Do not restart at P0 or broad terminology research.**

Continue from the remaining P1 runtime harness, deterministic generator, and asset-validator gaps below. The static/schema-oracle baseline is complete; extend record-specific semantic coverage only when a generator/bug requires it.

### P1 — Runtime harness

Build the Windows-first MO2 test worker that can:
- launch a dedicated disposable profile;
- select test save/new-game fixture;
- run scripted actions;
- wait for state/events;
- query forms/quests/actors/logs;
- take screenshots;
- capture crash logs and frame-time traces;
- restore fixture/profile state;
- feed typed runtime assertions to G19/G20/G21/G26.

### P1 — Static/schema oracles — BASELINE COMPLETE

Implemented:
- ✅ xEdit Check-for-Errors wrapper + structured parser with completion/count reconciliation;
- ✅ xDump project-plugin semantic export + conservative normalization;
- ✅ load-order-aware canonical FormID → FormKey conversion for regular and light records;
- ✅ pinned Mutagen semantic producer with canonical FormKeys and asset-link enumeration;
- ✅ coverage-aware Mutagen vs xEdit/xDump differential comparison;
- ✅ FormID/master/ESL reusable analyzer with runtime/BEES/header-version policy;
- ✅ full CTDA predicate preservation/invariant analyzer;
- ✅ PSC property extraction → Papyrus symbol inventory → inheritance-aware VMAD binding analyzer.

Static-oracle scope boundary: current cross-producer semantic intersection is intentionally narrow (`editor_id` + listed asset paths) until record-specific typed emitters are added. Producer-private raw evidence is retained for audit but does not create false semantic diffs.


### P1 — High-value deterministic generators

Complete typed renderers/generators for:
- FLM;
- SkyPatcher;
- OAR;
- FOMOD;
- common xEdit/Mutagen static patch patterns;
- MCM Helper config;
- common SPID/KID/BOS combinations;
- common perk/spell/COBJ/leveled-list patterns.

### P1 — Asset validators

Add deterministic validation for:
- FaceGen NPC_ ↔ FaceGeom/FaceTint fingerprint coherence;
- NIF blocks/shaders/texture closure;
- TRI vertex/topology consistency;
- skin partitions/weights/skeleton bones;
- DDS format/mipmap/channel semantics;
- animation skeleton/behavior/event dependencies.

### P2 — Continuous improvement

- current tool/framework release watcher;
- source API/schema diff watcher;
- crash-signature corpus;
- validated compatibility-pattern learning;
- generated CI workflows per mod;
- project-specific mod profiles;
- automatic research tasks when implementation readiness reports an evidence gap.

## Commit discipline

To reduce Resume Stream loss:

- prefer **one logical change per commit**;
- commit after every schema, tool, test, adapter, rule pack, or documentation checkpoint;
- do not accumulate a long multi-file uncommitted conceptual batch;
- after any interruption, inspect recent Git history and this file before continuing;
- update this checkpoint whenever the resume point materially changes.

## Definition of success

The target is **not** “the AI knows Skyrim modding.”

The target is:

> The user describes an intended mod behavior. Agent OS resolves ordinary technical questions itself, chooses the safest architecture, generates deterministic artifacts, independently validates schemas/assets, builds only what changed, launches isolated tests, reads back actual game state, diagnoses failures, applies only provably safe repairs, re-tests, records regressions, and surfaces only creative decisions or genuinely unautomatable game/visual judgments.

That is the remaining work.
