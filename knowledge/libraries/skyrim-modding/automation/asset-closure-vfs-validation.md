# Skyrim Mod Factory — Asset Closure and VFS Validation

Created: 2026-09-24
Status: graph schema + closure validator implemented

## Goal

Every required asset reference should resolve **before Skyrim launches**.

Implemented:
- `schemas/skyrim-asset-graph-v1.schema.json`;
- `tools/skyrim_mod_factory/validate_asset_graph.py`.

## Producers

The asset graph should be populated by specialized adapters:

### Plugin producer
Extract paths from record fields such as:
- models;
- icons;
- texture sets;
- sounds;
- scripts;
- voice/localization resources;
- UI paths where represented.

### NIF producer
PyNifly/Nifly extracts:
- texture slots;
- behavior graph extra data;
- controller/animation resource references;
- external collision/material references where applicable.

### Papyrus producer
Resolve:
- PEX for every shipped PSC;
- imported/provider script dependencies as compile evidence, not necessarily release assets.

### UI producer
Resolve:
- SWF;
- fonts;
- images;
- external config/data.

### Voice producer
Resolve expected:
- FUZ/XWM/WAV/LIP paths;
- plugin/VoiceType/INFO identity.

### Runtime-config producer
Resolve forms and any referenced files used by framework configs.

## Resolution planes

### Staging tree
The clean release candidate.

### MO2 VFS inventory
The actual file winner seen by the game/test process.

### Archive inventory
Files inside BSA/BA2-equivalent archive where relevant.

Validation against source directories alone is insufficient if another mod wins in the VFS.

## Case policy

Windows game runtime is commonly case-insensitive, but:
- archives/tools;
- Linux/Proton;
- Git;
- cross-platform build tooling
can expose case errors.

The validator reports case mismatches even when a case-insensitive match exists.

## Duplicate candidates

Multiple roots can contain the same relative path.

A duplicate is not automatically an error:
- the VFS winner can be intentional.

The build report should record:
- all candidates;
- actual winner;
- intended winner;
- mod priority.

If actual and intended winner differ, fail compatibility validation.

## Missing generated assets

If a missing required path is declared as generated output:
- identify its generator;
- rebuild the minimal downstream node;
- rerun closure.

Do not patch the reference path merely to silence the check unless the source intent says the path was wrong.

## Orphans

Future inverse check:
- files shipped but never referenced;
- source-only/development files;
- obsolete old-version outputs.

Orphan detection should be warning-first because some assets are loaded dynamically by naming convention or native/plugin code.

## Release condition

G11 passes when:
- all required paths resolve;
- expected generated files are fresh;
- VFS winner matches intent for overwrite-sensitive assets;
- unexplained case mismatches are dispositioned.
