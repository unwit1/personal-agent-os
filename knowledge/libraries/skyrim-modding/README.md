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
