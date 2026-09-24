# Skyrim Mod Factory — AI-Native Modding Stack

Created: 2026-09-24
Status: canonical architecture extension

## Goal

Make an AI agent capable of taking a Skyrim mod idea from natural-language intent to a reproducible, validated implementation with the smallest possible amount of manual tool operation.

The target loop is:

idea -> retrieve relevant Skyrim knowledge -> choose implementation layer -> inspect real load order -> generate/patch source -> validate against independent schemas -> build -> launch isolated test environment -> observe the running game -> compare expected/observed state -> repair -> rerun only affected tests -> package with evidence

The AI is an orchestrator. Deterministic tools remain the authority for binary formats, compilation, runtime state and validation.

## Preferred planes

### 1. Canonical project/source plane
Git + Agent OS.

Stores:
- project manifest;
- design decisions;
- source PSC/C++/Python/C#;
- Spriggit YAML/JSON where appropriate;
- configuration source;
- tests;
- generated-output manifests;
- validation reports;
- source/version locks.

### 2. Static Skyrim data plane
Preferred adapter: **houseCARL** where its coverage fits.

houseCARL exposes an MO2 Skyrim SE load order over MCP using Mutagen. Current upstream describes:
- 31 MCP tools;
- generated record schema coverage;
- records/assets/NIF/Papyrus/BSA/SkyPatcher/SKSE/Nexus surfaces;
- dry-run writes;
- pre-flight schema validation;
- new-plugin/new-MO2-mod output by default;
- readback verification;
- explicit opt-in before in-place plugin edits.

Use it for:
- inspecting real winners/override chains;
- querying typed fields;
- creating/forwarding/copying records;
- drafting safe patches;
- checking scripts/dialogue/FaceGen;
- resolving VFS asset winners;
- inspecting NIF and SKSE/config layers.

Do not assume Mutagen coverage equals xEdit coverage. houseCARL itself reports gaps where Mutagen lacks a modeled type.

### 3. Textual plugin source plane
Preferred adapter: **Spriggit**.

Use Spriggit to serialize plugin records into versioned YAML/JSON so:
- AI can edit data as ordinary text;
- Git diffs are readable;
- code review is possible;
- merge conflicts are visible;
- the translation package/version is stamped into the serialized data;
- binary plugin output can be regenerated.

For source-controlled authored plugins, Spriggit should often be the canonical human/AI-editable representation even when Mutagen/houseCARL creates the first draft.

### 4. Binary/schema oracle plane
Use **xEdit/xDump** as an independent schema/record validator.

Agent OS already captures:
- xEdit-native schema export;
- official-master record dumps;
- record signatures;
- CTDA schema;
- ActorValues;
- record flags.

xEdit is the independent cross-check against Mutagen/Spriggit generated output.

### 5. Papyrus authoring plane
Use:
- Papyrus Language Tools / Papyrus Tools for editor diagnostics and symbol resolution;
- Papyrus Index for provider/API lookup;
- official compiler and/or Caprica/Pyro for deterministic compilation;
- Lilac for in-game unit-style Papyrus tests where practical;
- Papyrus Debug Adapter for live stepping/debugging when the runtime/plugin remains compatible.

The AI should never invent a Papyrus function signature when it can query the pinned provider corpus.

### 6. Native SKSE plane
Use CommonLibSSE-NG + Address Library + source-locked build presets.

AI generates:
- plugin skeleton;
- lifecycle registration;
- event sinks;
- Papyrus bindings;
- serialization schema;
- API version negotiation;
- logging;
- tests.

Automated checks must independently validate:
- supported runtime declaration;
- relocation IDs;
- imports;
- DLL metadata;
- API-provider availability;
- hook expected bytes where applicable;
- serialization version;
- thread affinity.

### 7. Runtime observation/control plane
Use one or more of:

#### SkyLink AI
Current project exposes a C# MCP server + CommonLib SKSE DLL with 74 game/runtime tools, including:
- player/inventory/quest/NPC/world/combat state;
- console commands with captured output;
- save/load;
- events;
- Papyrus catalog and VM call bridge;
- load-order/SKSE scanning;
- game safety checks.

Best role: deterministic runtime assertions and active test scenarios.

#### DevBench via Skyrim Claude Toolkit
The current toolkit documents read/write test loops against a running game:
- live VM health;
- active effects/equipment/quests/reference grid;
- console commands with returned output;
- Papyrus calls with return values;
- event waits;
- hung-vs-paused health checks.

Best role: mod-development test bench rather than player-facing AI.

#### SkyrimNet MCP
SkyrimNet exposes an in-game MCP server with 44+ tools for:
- game data queries;
- prompt rendering;
- memory/knowledge management;
- action eligibility;
- YAML validation;
- live reload;
- item rendering for vision models;
- console commands.

Best role:
- testing SkyrimNet integrations;
- AI-NPC mod features;
- prompt/action/trigger authoring;
- vision-aware game-state inspection.

These runtime planes should be permission-scoped. Destructive or save-persistent commands require explicit project policy.

### 8. 3D/asset AI plane
Use Blender + PyNifly/Nifly as the authoritative conversion/validation path.

AI integration options:
- Blender MCP variants for typed scene/object/material/animation/rigging/physics operations;
- visual screenshot/render feedback;
- Blender Python for deterministic tasks;
- PyNifly for NIF/TRI/HKX-specific transformations and parsing;
- NifSkope as independent visual/structural inspection.

AI-generated 3D systems such as Hunyuan3D/Hyper3D can be used for **prototype/source geometry**, not assumed release-ready Skyrim assets. Generated output must pass cleanup, topology, UV, weights, material, collision, NIF and licensing gates.

### 9. Voice/audio AI plane

#### xVASynth
ML voice synthesis framework designed around game-character voice sets; supports model/plugin ecosystem and batchable synthesis backend.

#### Piper / XTTS
Useful local TTS families in Mantella/SkyrimNet-style stacks.

#### Mantella
Primarily an AI-NPC runtime/conversation framework using STT -> LLM -> TTS. It is relevant as a reference architecture for voice pipelines and for mods intentionally built around freeform AI conversation, but it is not a general plugin-authoring replacement.

AI voice output must preserve:
- voice/model provenance;
- permission/licensing policy;
- exact line text;
- generated WAV;
- lip/FUZ conversion;
- INFO/Form/VoiceType path identity;
- human QA for pronunciation, emotion and clipping.

### 10. Automated health-analysis plane

#### Mutagen.Bethesda.Analyzers / Antigen
Research-stage programmable analyzer project cataloging crash/oddity conditions with CLI/library ambitions and live responsiveness.

Treat as:
- useful upstream bug-knowledge source;
- candidate analyzer integration;
- not a sole release gate until coverage/stability is validated.

#### Crash Logger + project-specific parsers
Use crash signatures, PDBs, load order and involved FormIDs as evidence.

#### Framework logs
SPID/KID/BOS/OAR/Pandora/houseCARL/SkyPatcher/DynDOLOD etc. need their own parsers.

## AI tool routing

When an agent receives a task, choose tools by the question:

### "What does my real load order currently do?"
houseCARL -> xEdit cross-check when needed.

### "Create a record/patch for this load order."
houseCARL dry-run/new patch or Mutagen/Synthesis -> xEdit -> Spriggit serialization/diff.

### "Edit the authored plugin source."
Spriggit YAML/JSON or source generator, then deserialize -> xEdit/Mutagen reload.

### "Why does this script fail?"
Papyrus language diagnostics -> provider API index -> compile -> Lilac/runtime test -> Debug Adapter/DevBench if needed.

### "Why does the game behave differently than xEdit?"
runtime patcher audit + save/ExtraData + SkyLink/DevBench query.

### "Make/modify a mesh."
PyNifly/Blender MCP -> independent NifSkope/PyNifly parse -> render views -> game test.

### "Create AI dialogue/NPC behavior."
SkyrimNet/Mantella-style framework only if freeform model behavior is intended; otherwise prefer deterministic Quest/Scene/Papyrus systems.

## Source-of-truth hierarchy

For a generated result:
1. project manifest and explicit design intent;
2. authoritative source schemas;
3. actual user load order/VFS;
4. generated artifact;
5. independent validator;
6. running-game observation;
7. human visual/gameplay acceptance where semantics are subjective.

An LLM statement never outranks a deterministic tool result.

## Safety defaults

- Never write directly into Skyrim Data as source of truth.
- Never edit third-party plugins in place by default.
- Prefer new MO2 mod folders and generated patches.
- Require dry-run before plugin writes.
- Snapshot/commit before consequential edit.
- Preserve failing evidence before repair.
- Never modify a real save as an automated first response.
- Keep AI-generated external assets in staging until rights/provenance and format gates pass.
- Runtime MCP actions that alter game/save state must be classified as reversible/test-only or consequential.

## Long-term Agent OS interfaces

- `skyrim.ai.plan`
- `skyrim.ai.context.resolve`
- `skyrim.data.query`
- `skyrim.data.patch.dry_run`
- `skyrim.data.patch.apply`
- `skyrim.schema.triangulate`
- `skyrim.runtime.query`
- `skyrim.runtime.assert`
- `skyrim.runtime.scenario.run`
- `skyrim.blender.inspect`
- `skyrim.blender.edit`
- `skyrim.asset.render_verify`
- `skyrim.voice.synthesize`
- `skyrim.test.generate`
- `skyrim.test.execute`
- `skyrim.repair.loop`
