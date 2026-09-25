# Skyrim Mod Factory — Toolchain Lock and Doctor

Created: 2026-09-24
Status: implemented first-pass preflight

## Problem

A correct implementation plan can still fail for reasons unrelated to the mod idea:

- wrong Skyrim executable;
- wrong SKSE/Address Library;
- stale compiler/generator;
- missing CLI;
- tool path changed;
- binary silently replaced;
- output points at real Data/Overwrite/mods root;
- AI assumes a preferred adapter exists when it does not.

These should be detected **before any generation or mutation**.

## Toolchain lock

`schemas/skyrim-toolchain-lock-v1.schema.json` records:

- exact game runtime/distribution;
- SKSE and Address Library;
- Creation Kit/CommonLib when applicable;
- host build tools;
- adapters;
- executable paths;
- versions/source refs;
- optional SHA-256 pins;
- generated output roots.

The lock is project-specific. It should not be inferred from a generic "AE" label.

## Doctor

`tools/skyrim_mod_factory/doctor_toolchain.py` checks:

- duplicate/missing adapter locks;
- executable existence;
- optional executable SHA-256;
- required adapter pinning;
- preferred adapters from the quality plan;
- explicit manifest adapter requirements;
- native runtime/SKSE/Address Library completeness;
- CK pinning for editor-owned content;
- unsafe output roots.

## Severity

### Error
Architecture/build cannot be trusted:
- explicitly requested adapter missing;
- required executable missing/hash mismatch;
- native runtime unpinned;
- output points directly at Skyrim/Data.

### Warning
Build may still be valid but reproducibility/support is weaker:
- recommended adapter missing;
- required adapter lacks version/source ref;
- editor-owned project without CK version;
- output uses broad MO2 mods/Overwrite root.

## Integration order

1. validate project manifest;
2. derive quality plan;
3. validate dependency lock;
4. run toolchain doctor;
5. only then construct/execute the build DAG.

The autonomous-debugger should not "repair" a missing/wrong tool by mutating project artifacts. Toolchain failures are environment/configuration failures and should be fixed at the environment layer.
