# Skyrim Mod Factory — One-Command Project Preparation

Created: 2026-09-24
Status: implemented

`tools/skyrim_mod_factory/prepare_project.py` is the preferred planning entry point for agents.

## It performs

1. load and verify a `skyrim-mod-project-v1` manifest;
2. derive layer/output validation requirements;
3. merge explicitly selected implementation-pattern requirements;
4. select preferred/supporting tool adapters;
5. emit runtime/negative/human tests;
6. optionally run the toolchain doctor;
7. compile the incremental build DAG;
8. write one preparation report with a single `ready_for_execution` decision.

## Outputs

Inside the requested workspace:
- `quality-plan.json`;
- `build-dag.json`;
- `preparation-report.json`.

## Readiness rule

The project is not ready for autonomous execution when:
- a pattern ID is unknown;
- a truly blocking user/product question remains;
- the toolchain doctor reports an ERROR.

Warnings can continue into a visible review state but must not be silently ignored.

## Pattern role

The layer-based quality planner answers **what evidence this kind of implementation needs**.

The implementation-pattern registry adds **how this specific idea is normally implemented**.

This prevents a feature such as actor distribution from being treated as a generic runtime-patching task when the registry already knows SPID is usually preferable to static NPC overrides or Papyrus polling.
