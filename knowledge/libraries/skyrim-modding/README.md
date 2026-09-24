# Skyrim Modding Knowledge Repository

Status: active foundation
Created: 2026-09-24
Canonical home: `knowledge/libraries/skyrim-modding/`

## Purpose

This library is the technical Skyrim-modding knowledge base for Agent OS. It is intended to support:

- troubleshooting and root-cause analysis;
- mod design and implementation brainstorming;
- compatibility and conflict analysis;
- patch planning;
- Creation Kit, xEdit, Papyrus, SKSE, CommonLibSSE-NG, asset, animation, LOD, and tool reference;
- source-backed explanations of modding terminology;
- version-aware reasoning across Skyrim LE, SE, AE, GOG, and VR;
- reusable findings from the user's own modding projects.

It is intentionally separate from the Elder Scrolls lore library. Lore projects may link to this library for technical implementation knowledge without duplicating it.

## Knowledge model

Entries should distinguish:

1. **Documented fact** — directly supported by authoritative tool/project documentation or game/editor documentation.
2. **Well-established technical convention** — broadly used terminology or workflow with strong community/tool support.
3. **Reverse-engineered behavior** — supported by source code, runtime inspection, controlled testing, or multiple technical sources.
4. **Project-specific finding** — observed in a particular mod, plugin, runtime, load order, or test environment.
5. **Unverified community claim** — useful lead, but not safe to treat as canonical until corroborated.

Every durable entry should retain provenance and, where relevant, game/runtime/tool version applicability.

## Source priority

Prefer, in roughly this order:

- Bethesda/Creation Kit documentation and game data;
- current upstream source code and documentation for the tool/framework being described;
- xEdit/Tome of xEdit documentation for plugin-record behavior;
- SKSE and CommonLibSSE-NG upstream documentation/source;
- maintained specialist technical documentation such as DynDOLOD;
- reproducible testing and inspected plugin/source data;
- high-quality community guides, forum posts, Reddit, Discord, and mod pages as secondary evidence.

Community material is valuable, but contradictory or version-sensitive claims should remain explicitly qualified.

## Initial sections

- `terminology/` — normalized glossary with aliases and cross-links.
- `sources/` — source registry and provenance notes.
- Future sections should cover plugin architecture, records, Creation Kit, xEdit, Papyrus, SKSE/native plugins, assets, animations, worldspaces/navmesh, quests/dialogue, LOD, mod managers, crash analysis, compatibility/patching, distribution, and testing.

## Ingestion rules

- Do not copy large copyrighted guides or mod pages wholesale.
- Store concise definitions, structured facts, compatibility notes, claims, and source links.
- Preserve important disagreements instead of flattening them into one unsupported answer.
- Record version scope where behavior differs across Skyrim/runtime/tool versions.
- Treat exact mod-specific findings as overlays linked to the relevant project or mod record.
- Prefer normalized terminology with aliases so searches for common shorthand resolve to the same concept.

## Current ingestion

The first terminology pass is stored in `terminology/core-glossary.md` and is sourced from the Creation Kit Wiki archive/mirror, Tome of xEdit, the official SKSE site, DynDOLOD documentation, Mod Organizer 2 source/documentation, and Open Animation Replacer upstream documentation.


## Current terminology corpus

As of 2026-09-24, the library contains **2,374 indexed headings across 28 terminology/reference modules**, plus dedicated operational playbooks, a 76-entry canonical alias map, a troubleshooting routing matrix, an expanded source registry, a research coverage manifest, and an explicit research frontier.

Major covered domains include plugin formats/xEdit/FormIDs; Creation Kit/worldbuilding/navmesh; Papyrus/quests/Story Manager/save persistence; SKSE/CommonLib/native plugins/crash diagnosis; engine fixes and extension frameworks; SPID/KID/BOS/FLM/SkyPatcher; Mutagen/Synthesis/Spriggit; MO2/Vortex/Wabbajack; animation/OAR/Pandora; NIF/textures/BodySlide; RaceMenu/FaceGen; FSMP physics; SkyUI/Scaleform/MCM; audio/localization/archives; gameplay records; renderer/shader systems; performance/engine limits; and the full xLODGen/TexGen/DynDOLOD/grass/seasons/occlusion stack.

Navigation:
- `indexes/terminology-index.md` — module inventory and counts.
- `indexes/aliases.json` — canonical acronym/synonym routing.
- `indexes/troubleshooting-routing.md` — symptom/task → relevant subsystem mapping.
- `sources/registry.md` — source authority/provenance.
- `sources/coverage-manifest.md` — current research coverage.
- `sources/research-frontier.md` — deliberately unresolved/evolving areas.
- `playbooks/` — operational diagnostic/release procedures.

## Troubleshooting retrieval principle

Agent OS should diagnose Skyrim issues by layer rather than by symptom name alone. For each issue, identify which of these layers may be involved: plugin records/load order; physical or virtual assets; Papyrus/quest state; native SKSE runtime; runtime distributor/config frameworks; animation behavior; mesh/skeleton/morph data; UI; worldspace/navmesh; save-persisted state; and LOD/distance systems. Retrieve evidence from every plausible layer before proposing destructive changes or declaring a culprit.

## Continuous ingestion principle

This repository is designed to become more accurate through use. When a troubleshooting, authoring, reverse-engineering, or compatibility task produces a durable finding, Agent OS should stage it with its source, game/runtime/tool versions, reproduction evidence, confidence, and affected subsystem. Only validated findings should be promoted into canonical knowledge; forum/Discord/Reddit claims remain evidence candidates until corroborated.

The corpus should never claim permanent exhaustiveness because Skyrim modding tooling and reverse engineering continue to evolve. The operational goal is exhaustive coverage of known high-value domains plus explicit, searchable uncertainty and automatic research-on-demand for uncovered edge cases.
