# Skyrim Mod Factory — AI Tool and MCP Adapter Matrix

Snapshot: 2026-09-24
Status: current research registry

This catalog focuses on tools that let an AI agent **inspect, edit, build, test, or observe Skyrim mod projects directly**.

## Tier A — immediately useful core integrations

### houseCARL
Role: typed Skyrim/MO2 **static data-layer MCP**.

Current upstream reports:
- Mutagen-backed generated schema;
- 31 tools;
- record queries/writes/creation/forward/copy/merge/compact;
- asset winner/status;
- NIF inspect/set;
- Papyrus compile/decompile;
- BSA operations;
- SkyPatcher and SKSE config inspection;
- Nexus lookup/update tools;
- 7 bundled skills including generated Mutagen and Papyrus references.

Strongest properties:
- dry-run write pipeline;
- schema preflight before disk;
- default new patch/new MO2 folder;
- readback verification;
- explicit acknowledgement for in-place overwrite;
- MO2/VFS-aware asset provenance.

Recommended use:
**primary AI data-plane adapter** where its Mutagen model supports the record.

Do not replace xEdit as independent schema oracle.

Source: https://github.com/Avick3110/houseCARL

### SkyLink AI
Role: live Skyrim **runtime MCP**.

Current project reports:
- 74 runtime tools;
- C# MCP server;
- CommonLibSSE-NG SKSE plugin over named pipe;
- player/inventory/quest/NPC/world/combat/economy/magic/event actions;
- console output capture;
- Papyrus VM bridge/catalog;
- game-safety checker.

Recommended use:
runtime smoke/regression assertions on an isolated development profile/save.

Source: https://github.com/jarvann/SkryimMCM

### SkyrimNet MCP
Role: live game/context MCP plus AI-NPC framework development.

Current upstream reports 44+ MCP tools for:
- game data;
- memories/world knowledge;
- prompt rendering;
- action eligibility;
- item screenshots;
- console commands;
- YAML validation;
- live prompt/trigger/action reload.

Recommended use:
- AI NPC/prompt/action/trigger development;
- runtime game-state queries;
- screenshot/vision-assisted testing where the SkyrimNet dependency is acceptable.

Source: https://github.com/MinLL/SkyrimNet-GamePlugin

### Spriggit
Role: plugin <-> Git-friendly YAML/JSON source.

AI advantage:
- ordinary text edits and diffs;
- per-record files;
- versioned translation packages;
- deterministic binary regeneration.

Recommended use:
canonical authored-plugin source representation when workflow permits.

Source: https://github.com/Mutagen-Modding/Spriggit

### Blender MCP
Role: LLM-controlled Blender.

Current community implementations expose:
- scene inspection;
- object/material/mesh operations;
- Python execution;
- rendering/screenshots;
- rigging/animation/physics in richer variants;
- optional AI 3D generators such as Hunyuan3D/Hyper3D.

Preferred selection criteria:
- typed first-class tools over one unrestricted Python endpoint;
- screenshot/visual feedback;
- undo/checkpoint support;
- main-thread dispatch;
- explicit version compatibility;
- no unauthenticated remote bind by default.

Skyrim-specific constraint:
always put PyNifly/NifSkope/game-format validation after Blender.

Representative sources:
- https://github.com/teamipc/blender-mcp
- https://github.com/kleer001/blender-mcp

## Tier A/B — engineering workbench/reference implementations

### Skyrim Forge / Ultimate AI Starter Bundle
Role: safety-first AI automation fabric.

The standalone SkyrimForge repository is explicitly unsupported at v6.0.0; development moved into the Ultimate AI Starter Bundle.

The published design is nevertheless highly relevant:
- typed JSON jobs rather than AI clicking arbitrary GUIs;
- input snapshots;
- allowlisted adapters;
- captured logs/outputs;
- reopen/readback verification;
- audit receipts;
- rights/publication gate;
- FOMOD generator;
- Papyrus/native analysis;
- external-tool hash pinning;
- xEdit/LOOT/Wrye Bash/CK adapters;
- MCP exposure.

Recommended action:
ingest architectural patterns; evaluate the active bundle before adopting executable code.

Sources:
- https://github.com/SenjuWoo/SkyrimForge
- https://github.com/ShugokiFable/Ultimate-AI-Starter-Bundle

### Skyrim Claude Code Modding Toolkit
Role: pre-integrated AI Skyrim development environment with safety hooks and live test tooling.

Current documentation includes:
- Spriggit/xeditlib plugin workflows;
- PyNifly/NifSkope/headless Blender validation;
- NIF/VFX authoring;
- Papyrus/crash triage;
- MO2-aware routing;
- DevBench live test loop;
- hook canaries and safety lessons.

Recommended action:
mine its proven test/safety patterns and DevBench integration; do not copy Claude-specific assumptions into Agent OS without abstraction.

Source: https://github.com/WingedGuardian/skyrimvr-claude-toolkit

## Papyrus AI/developer tooling

### Papyrus Language Tools
LSP-grade VS Code support:
- completion;
- jump-to-definition;
- hovers;
- symbol search;
- PPJ builds;
- live diagnostics.

Source: https://github.com/joelday/papyrus-lang

### Papyrus Tools for VS Code
Modern all-in-one extension with:
- Papyrus Index-backed intelligence;
- game profiles;
- compile wizard;
- workspace/project explorers;
- Copilot chat participant;
- optional MCP server.

Use as a candidate AI/editor bridge, but validate its API/provider coverage and compiler behavior against the canonical Agent OS source locks.

Source: https://github.com/MrTrilB/PapyrusVSCode

### Papyrus Debug Adapter
Websocket-based Debug Adapter Protocol xSE plugin for live Papyrus debugging. The standalone repository is archived, but a debug-server project remains inside the papyrus-lang solution.

Use only after verifying current runtime compatibility.

Source: https://github.com/joelday/papyrus-debug-server

### Papyrus Index
Cross-provider searchable parser/index of vanilla/extender/mod API PSCs.

Excellent source for:
- API discovery;
- provider distinction;
- signature generation.

Source: https://github.com/BellCubeDev/papyrus-index

### Lilac
Papyrus unit-test framework with Jasmine-like assertions and log output.

Despite its age, the pattern remains valuable:
- dedicated test quest;
- deterministic assertions;
- tests run only on demand.

Source: https://github.com/chesko256/Lilac

### Pyro
Parallel/incremental build automation:
- Papyrus compile;
- archive packaging;
- distribution prep;
- IDE integration.

Useful as a build backend/reference even if Agent OS separately implements its own graph.

Source: https://github.com/fireundubh/pyro

## Static health analysis

### Mutagen.Bethesda.Analyzers / Antigen
Research-stage bug/analyzer framework intended to expose programmable library/CLI checks and eventually live-responsive load-order health analysis.

Recommended use:
- ingest known bug predicates;
- run available stable analyzers;
- contribute Agent OS regression findings upstream where useful.

Do not treat incomplete research coverage as a clean bill of health.

Source: https://github.com/Mutagen-Modding/Mutagen.Bethesda.Analyzers

### xEdit/xDump
Not AI-specific, but essential as the independent binary/schema truth plane the agent calls.

### CKPE
Not AI-specific, but improves/extends CK and exposes a more stable editor base for supervised operations.

## AI voice/conversation tooling

### xVASynth
ML speech synthesis app focused on game character voice models.

Automation opportunity:
- local HTTP/backend integration;
- batch synthesis;
- line manifest;
- generated WAV -> lip/FUZ pipeline.

Source: https://github.com/DanRuta/xVA-Synth

### Mantella
Skyrim/Fallout AI conversation framework using STT -> LLM -> TTS with Whisper/Moonshine and Piper/xVASynth/XTTS options.

Use:
- reference implementation for AI conversation architecture;
- player-facing conversational mods.

Do not use as a general mod compiler/data editor.

Source: https://github.com/art-from-the-machine/Mantella

### SkyrimNet
Also belongs here because it combines native game state, LLM interaction, memory, actions, TTS and MCP tooling.

## Generative asset tools

### Blender MCP + Hunyuan3D/Hyper3D/Meshy/Tripo/ComfyUI backends
Good for:
- concepts;
- blockouts;
- source meshes;
- texture/material experiments;
- rapid variants.

Not release-ready by default.

Required downstream:
- topology cleanup;
- scale/origin;
- UV;
- textures;
- normals/tangents;
- collision;
- Skyrim skeleton/weights/partitions;
- NIF conversion;
- visual/game tests;
- rights/provenance.

## AI adapter selection rules

### Prefer typed MCP tools
A typed `set_weapon_damage(form, value)`/schema-aware record op is safer than arbitrary terminal or Python execution.

### Preserve an escape hatch
Arbitrary code execution is still useful for novel workflows, but should be sandboxed/staged and never the default mutation route.

### Prefer query before mutation
Every agent mutation should be preceded by:
- current state read;
- intended diff;
- dry-run/validation where possible.

### Prefer readback
Every write should be followed by an independent read.

### Keep static and runtime planes separate
houseCARL can prove what records/assets declare.
SkyLink/DevBench/SkyrimNet can prove what the running game currently observes.
Neither alone proves the other.

### Provider-neutral Agent OS wrapper
Agent OS should expose one stable internal interface and adapt to whichever MCP/CLI is installed.

Do not bake Claude, Codex, or one vendor's configuration format into canonical mod project state.
