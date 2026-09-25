# Skyrim Mod Factory — Automatic Quality Plan

Created: 2026-09-24
Status: implemented first-pass deterministic planner

## Purpose

A user describing a mod idea should not need to know which validators, tools, test fixtures, negative tests, or generated outputs are required.

`tools/skyrim_mod_factory/derive_quality_plan.py` consumes the canonical `skyrim-mod-project-v1` manifest and derives a `skyrim-quality-plan-v1` document containing:

- risk tier;
- applicable G00–G29 validation gates;
- preferred and supporting adapters;
- static checks;
- runtime scenarios;
- validator mutation tests;
- human/subjective checks;
- generated-output invalidation triggers;
- architecture-blocking questions only;
- machine-readable reasons for every inferred gate.

## Principle

**Ask the user about design intent, not Skyrim implementation trivia.**

The planner should answer automatically:
- which plugin validators to run;
- whether ESL integrity applies;
- whether Papyrus needs compile/lifecycle/migration tests;
- which native runtime matrix tests apply;
- which asset parsers and render checks apply;
- whether world/navmesh/quest scenarios require live game tests;
- which generated outputs become stale after an upstream change.

The user should be asked only when the answer materially changes:
- target runtime;
- save compatibility promise;
- architecture;
- licensing/redistribution;
- creative/gameplay behavior.

## Gate inference examples

### Plugin-only balance mod
Expected:
- schema/master/conflict gates;
- independent xEdit/Mutagen/Spriggit validation;
- touched-field intent diff;
- load/readback smoke test.

### Papyrus gameplay mod
Adds:
- compile/provider/PEX/VMAD checks;
- lifecycle and registration audit;
- new-game/save-load scenarios;
- mutation fixtures for stale PEX, missing parent, bad property and missing native provider.

### Native SKSE plugin
Adds:
- target build matrix;
- static analysis/API/relocation checks;
- startup/load/save/revert tests;
- dependency-absent and API-mismatch tests;
- performance budget.

### Navmesh/world mod
Adds:
- CELL/WRLD/LAND/NAVM validation;
- CK/xEdit;
- path-traversal runtime fixtures;
- visual/spatial human check.

### Asset mod
Adds:
- NIF/DDS structural checks;
- asset closure;
- independent parser/render validation;
- provenance gate for generated assets.

## Invalidation

Each implementation layer emits triggers that should invalidate downstream outputs/tests.

Examples:
- skeleton change -> revalidate NIF/animation/physics;
- PSC provider change -> recompile PEX and rerun script tests;
- load-order change -> rerun Synthesis/LOOT/compatibility and downstream LOD;
- mesh/texture priority change -> rerun PGPatcher and LOD consumers.

Long term, these triggers should feed a true incremental build DAG rather than rerunning the entire factory.

## Files

- schema: `schemas/skyrim-quality-plan-v1.schema.json`
- planner: `tools/skyrim_mod_factory/derive_quality_plan.py`
- tests: `tools/skyrim_mod_factory/tests/test_quality_plan.py`

## Next stage

Merge the quality plan with:
- implementation pattern selection;
- dependency lock;
- installed adapter discovery;
- touch-set overlap;
- runtime fixture generation;

to produce an executable build/test DAG with no unanswered low-level questions.
