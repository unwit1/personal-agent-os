# Skyrim Modding Knowledge Repository

Status: active deep-ingestion corpus
Created: 2026-09-24
Canonical home: `knowledge/libraries/skyrim-modding/`

## Purpose

This library is Agent OS's technical Skyrim-modding knowledge base for:

- troubleshooting and root-cause analysis;
- mod design and implementation;
- compatibility/conflict analysis and patch planning;
- Creation Kit, xEdit, Papyrus, SKSE/CommonLib, assets, animation, rendering, LOD, UI, physics and tooling reference;
- version-aware reasoning across Skyrim LE, SE/AE, GOG, VR and Linux/Proton environments;
- reusable findings from the user's own Skyrim projects.

It is intentionally separate from Elder Scrolls lore. Technical implementation knowledge lives here; lore repositories may link to it.

## Current corpus

As of 2026-09-24, the live terminology directory contains **164 specialist terminology/reference modules**, plus authoring guides, playbooks, troubleshooting routers/catalogs, source provenance, research/frontier documents and extraction tooling.

The old manually maintained heading total has been retired from this README. Exact module/heading counts are generated from a checkout by:

`python tools/knowledge/rebuild_skyrim_terminology_index.py`

The generated/maintained index lives at `indexes/terminology-index.md`.

## Major coverage

The corpus now covers, at minimum:

- plugin binary structure, ESM/ESL/FormIDs, header 1.71/BEES, localization and BSA resources;
- xEdit conflict analysis, record schemas, cleaning, Wrye Bash, Mator Smash, Mutagen and Synthesis;
- Creation Kit records, worldspaces, landscape, navmesh, Room Bounds/Portals, weather, lighting and authoring;
- Papyrus language semantics, API/event maps, performance, persistence, fragments, registration and migration;
- PapyrusUtil, JContainers, MCM Helper, powerofthree Papyrus Extender and external/save-local settings models;
- SKSE/CommonLib plugin lifecycle, interfaces, events, serialization, relocations, hooks, trampolines and inter-plugin APIs;
- actors, processing levels, AI/packages/detection, followers, relationships, crime, merchants, encounters and transformations;
- quests, aliases, Story Manager, dialogue, scenes, voice and localization;
- perks/Entry Points, MagicEffect archetypes, spells, crafting, alchemy, enchanting, progression and custom skills;
- NIF blocks, shaders, texture slots, collision, Blender/PyNifly, BodySlide and asset conversion;
- skeletons, RaceMenu, BodyMorph/BodyGen/OBody, NPC FaceGen/EasyNPC and physics;
- OAR, Pandora, BDI, Payload Interpreter, AMR, Precision, SCAR/MCO and animation-object systems;
- SPID, KID, BOS, FLM, SkyPatcher, CID/CDF, IPM, SRD, DSD, MTD and other runtime mutation frameworks;
- Community Shaders render-pipeline internals, ReShade, HDR/display, parallax/PBR and water;
- xLODGen/TexGen/DynDOLOD, grass, seasons, occlusion and distant rendering;
- SkyUI/MCM/Scaleform, I4/COCKS, QuickLoot/Wheeler, native menus and PrismaUI;
- MO2, Vortex, Wabbajack, LOOT, Nexus Collections and reproducible release/source-control workflows;
- Skyrim VR, HIGGS, PLANCK, VRIK, VR Address Library and Linux/Proton/Steam Deck;
- crash/save/tool diagnostics, exact-error routing and recurring compatibility patterns;
- AI-NPC/LLM frameworks, Skyrim Platform and multiplayer architecture.

## Directory map

- `terminology/` — specialist technical concepts and field-level schema maps.
- `authoring/` — authoring/release workflows.
- `troubleshooting/` — symptom router, error catalog and compatibility patterns.
- `playbooks/` — operational diagnostic/release procedures.
- `indexes/` — generated/manual retrieval indexes and aliases.
- `sources/` — source registry and provenance/coverage material.
- `research/` — frontier, version/provenance policy and current-version snapshots.
- `automation/` — Mod Factory architecture, adapters, validation gates, analyzers, fixtures and implementation playbooks.

## Primary retrieval surfaces

Start here instead of loading the entire corpus:

- `troubleshooting/diagnostic-router.md` — symptom → likely subsystems.
- `troubleshooting/tool-error-catalog.md` — tool warning/error → diagnostic path.
- `troubleshooting/compatibility-patterns.md` — recurring cross-mod patch designs.
- `indexes/terminology-index.md` — module inventory.
- `sources/registry.md` — source authority and provenance.
- `research/frontier.md` — remaining open research.
- `research/version-provenance-model.md` — how version-sensitive facts are stored.
- `research/current-version-matrix.md` — dated verified version snapshots.
- `automation/README.md` — idea-to-release Mod Factory entry point.
- `automation/implementation-question-preemption.md` — questions the agent should resolve before asking the user.
- `automation/validation-gates.md` — mandatory build, schema, compatibility and release gates.

## Knowledge model

Entries distinguish:

1. **Documented fact** — authoritative documentation/source.
2. **Established technical convention** — widely used and strongly corroborated.
3. **Reverse-engineered behavior** — source/runtime/test evidence.
4. **Project-specific finding** — validated for one mod/runtime/load order.
5. **Unverified lead** — useful evidence candidate, not canonical fact.

Every durable version-sensitive entry should preserve provenance.

## Source priority

Prefer:

1. Bethesda/Creation Kit documentation and game data;
2. current upstream source/documentation for the relevant framework/tool;
3. xEdit/Tome of xEdit for plugin-record behavior;
4. SKSE/CommonLib source;
5. maintained specialist references such as DynDOLOD;
6. reproducible tests and inspected plugin/source data;
7. high-quality community technical material as secondary evidence.

Old advice stays historical until applicability to current versions is demonstrated.

## Ingestion and promotion

The pipeline is:

source acquisition → extraction → normalization → provenance/version tagging → deduplication/contradiction detection → validation → canonical promotion

High-volume generated indexes should live in local/index storage unless a reviewed durable snapshot belongs in Git.

Extraction scaffolding lives in `tools/knowledge/` and currently includes:

- terminology-index rebuilding;
- Papyrus PSC API extraction;
- CommonLib Doxygen symbol extraction;
- xEdit schema candidate extraction.

## Troubleshooting principle

Diagnose by layer rather than by symptom name alone. A visible problem may involve:

- static plugin records;
- loose/BSA assets;
- runtime patchers;
- Papyrus/quest state;
- native DLL hooks/APIs;
- animation behavior;
- skeleton/morph/physics;
- UI;
- world/navmesh/portal data;
- save ChangeForms/co-saves/external JSON;
- generated patches/LOD.

Retrieve evidence from every plausible layer before proposing destructive changes.

## Exhaustiveness model

The goal is not to pretend a continuously evolving reverse-engineered ecosystem can be permanently complete. The operational target is:

- every major subsystem has a canonical home;
- important finite engine schemas are cataloged deeply;
- source/version provenance is preserved;
- unknowns are explicit;
- new frameworks can be classified into the existing taxonomy;
- source extractors can deepen schemas systematically;
- troubleshooting can trigger targeted research into remaining gaps.

Remaining work is tracked in `research/frontier.md`.
