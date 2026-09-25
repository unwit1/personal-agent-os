# Skyrim Mod Factory — Incremental Build DAG

Created: 2026-09-24
Status: implemented first-pass compiler

## Purpose

The factory should not behave like one giant batch file.

`compile_build_dag.py` transforms:
- project manifest;
- automatic quality plan;

into a typed build DAG with:
- dependencies;
- parallel groups;
- selected adapters;
- gates;
- invalidation triggers;
- output ownership.

## Parallelism

After source lock, independent layers can build concurrently.

Example:
- plugin records;
- Papyrus;
- native DLL;
- meshes;
- textures;

do not need to wait on each other unless the project explicitly creates a dependency.

Cross-layer validation waits for all applicable layer validators.

## Incremental invalidation

Each node records what invalidates it.

Examples:
- PSC-only change -> Papyrus generation/validation + cross-layer/runtime/package, not texture conversion;
- DDS-only change -> texture validation + material/runtime/LOD consumers;
- load-order change -> compatibility/Synthesis/LOOT and generators that consume final load order;
- skeleton change -> mesh/animation/physics and all downstream runtime tests;
- runtime/SKSE change -> native builds/tests, not unrelated plugin-source generation.

The Orchestrator can later hash node inputs and skip nodes whose input closure has not changed.

## Fixed convergence stages

Regardless of parallel generation:
1. preflight;
2. source lock;
3. per-layer generation/validation;
4. cross-layer integration;
5. quality gates;
6. runtime smoke;
7. regressions/migrations;
8. packaging;
9. release audit.

## Why runtime happens before final packaging

The release package should contain the exact payload that passed runtime tests. If packaging itself transforms files (archive compression/FOMOD variants), package validation must additionally round-trip/extract and compare hashes/semantics.

## Files

- schema: `schemas/skyrim-build-dag-v1.schema.json`
- compiler: `tools/skyrim_mod_factory/compile_build_dag.py`
- tests: `tools/skyrim_mod_factory/tests/test_build_dag.py`

## Next stage

Add node input/output hashing and a local state database so Orchestrator can:
- identify dirty nodes;
- schedule independent nodes concurrently;
- checkpoint after every passing node;
- roll back only failed repair attempts;
- resume from the last valid node after interruption.
