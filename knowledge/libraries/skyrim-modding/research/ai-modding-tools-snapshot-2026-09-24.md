# AI-Integrated Skyrim Modding Tools — 2026-09-24 Snapshot

Status: dated research snapshot

## Direct Skyrim AI/MCP tooling

### houseCARL
Repository: https://github.com/Avick3110/houseCARL
Observed repository update: 2026-09-24.

Current README reports:
- MCP over stdio;
- Claude Code or OpenAI Codex hosts;
- MO2 profile/data access;
- Mutagen 0.54.4 substrate;
- 31 tools;
- generated record schema with 133 record types;
- safe new-patch default;
- dry-run and readback;
- Papyrus/NIF/BSA/SKSE/SkyPatcher/Nexus tooling;
- seven bundled skills.

High strategic fit for Agent OS static data-plane integration.

### SkyLink AI
Repository: https://github.com/jarvann/SkryimMCM
Repository describes 74 live Skyrim runtime MCP tools via a CommonLib SKSE DLL + .NET server.

High strategic fit for runtime test automation.

### SkyrimNet
Repository: https://github.com/MinLL/SkyrimNet-GamePlugin
Observed active 2026 development.

Current README describes:
- native in-process AI stack;
- OpenAI-compatible endpoints/OpenRouter support;
- prompt/action/trigger framework;
- web dashboard;
- 44+ MCP tools;
- live YAML validation/reload;
- item-to-image rendering;
- game data explorer;
- developer Papyrus/C++ APIs.

Best fit for AI-NPC features and as an optional live-game context plane.

### Skyrim Forge
Standalone: https://github.com/SenjuWoo/SkyrimForge
Status explicitly says unsupported; development moved to Ultimate AI Starter Bundle.

Architectural ideas worth retaining:
- typed jobs;
- tool allowlists;
- input snapshots;
- receipts;
- rights gates;
- schema/config validators;
- safety hooks.

### Skyrim Claude Code Modding Toolkit
Repository: https://github.com/WingedGuardian/skyrimvr-claude-toolkit
Current docs describe:
- Spriggit/xeditlib workflows;
- PyNifly/NifSkope/headless rendering;
- DevBench runtime testing;
- crash/Papyrus triage with explicit denominator checks;
- MO2 awareness;
- safety hook canaries.

Especially useful as evidence for closed-loop AI testing and safety design.

## Generic AI tools with direct modding value

### Blender MCP
Representative active projects:
- https://github.com/teamipc/blender-mcp
- https://github.com/kleer001/blender-mcp

Capabilities observed:
- inspect/edit Blender scene;
- materials/mesh;
- animation/rigging/physics in typed variants;
- screenshots/render;
- Python execution;
- AI 3D generation integrations.

### Papyrus Tools
- https://github.com/joelday/papyrus-lang
- https://github.com/MrTrilB/PapyrusVSCode

Features include language intelligence, diagnostics/build tooling; the latter also advertises Copilot chat and optional MCP.

### Papyrus Debug Adapter
https://github.com/joelday/papyrus-debug-server
Standalone repo archived, but provides a DAP design for live Papyrus debugging. Verify current integrated papyrus-lang runtime support before adoption.

### Papyrus Index
https://github.com/BellCubeDev/papyrus-index
Parser-backed cross-provider API index suitable for Agent OS ingestion.

## Deterministic tools that become AI-friendly through adapters

- Spriggit — text plugin source.
- Mutagen — typed plugin generation/query.
- Synthesis — load-order patch pipelines.
- xEdit/xDump — schema/error oracle.
- CKPE — improved Creation Kit.
- PyNifly/NifSkope — NIF authoring/validation.
- Pyro/Caprica/PapyrusCompiler — script build.
- Lilac — Papyrus tests.
- Mutagen.Bethesda.Analyzers — bug predicate research/analyzers.
- Crash Logger — runtime crash evidence.
- DynDOLOD/xLODGen/TexGen/Pandora/BodySlide/ParallaxGen — deterministic generators callable by Agent OS adapters.

## AI voice/runtime generation

### xVASynth
https://github.com/DanRuta/xVA-Synth
ML speech synthesis focused on game voice sets; backend/server architecture can be automated.

### Mantella
https://github.com/art-from-the-machine/Mantella
STT -> LLM -> TTS AI NPC stack using Moonshine/Whisper and Piper/xVASynth/XTTS options.

## Research conclusions

1. Do not build every integration from scratch.
2. Adopt/wrap houseCARL-style generated schemas for data access.
3. Keep xEdit as independent plugin oracle.
4. Use a separate runtime MCP/test plane.
5. Bring Blender into the same MCP ecosystem.
6. Use source-indexed Papyrus APIs, never model memory.
7. Require deterministic build/check tools around every AI-generated artifact.
8. AI-generated visual/voice content requires rights/provenance and human quality gates.
9. Every tool adapter must expose version, coverage and known blind spots.
10. A tool reporting "success" is not enough; Agent OS should independently read the output back.
