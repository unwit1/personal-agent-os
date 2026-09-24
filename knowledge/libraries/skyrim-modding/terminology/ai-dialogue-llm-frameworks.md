# Skyrim Modding Terminology — AI Dialogue, LLM, STT, and TTS Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 9

This module documents the architecture of modern generative-AI Skyrim mods without treating model output as canonical game state.

## General pipeline

### AI NPC framework
Mod system using speech/text generation models to create dynamic NPC conversation or actions beyond authored dialogue trees.

### STT
**Expansion:** Speech-to-Text. Converts microphone/player speech into text.

### ASR
Automatic speech recognition; general technical term for STT systems.

### LLM
Large language model generating NPC dialogue, reasoning text or structured action decisions from prompts/context.

### TTS
Text-to-Speech. Converts generated dialogue text into voice audio.

### Voice model
TTS model/config representing an NPC voice.

### Prompt
Instructions/context supplied to the LLM.

### Character bio
Structured/unstructured prompt context describing an NPC personality, history, goals and relationships.

### World context
Current game-state/lore/environment information exposed to the model.

### Memory
Stored conversation/event summaries recalled into later prompts.

### Retrieval
Selecting relevant knowledge/memories from a larger store for the current prompt.

### Action
Structured capability allowing model output to trigger a game/mod function.

### Action schema
Machine-readable definition constraining which action names/arguments are allowed.

### Tool execution
Framework validates generated action then invokes Papyrus/native/game operation.

### Hallucination
Generated claim not grounded in game data, authored lore or stored state.

### Grounding
Supplying trusted state/knowledge and constraining output/actions to reduce unsupported claims.

### Prompt injection
Untrusted text attempts to alter framework/model instructions. Relevant when mods ingest arbitrary external/user/community text.

### Context window
Maximum model input capacity; frameworks summarize/retrieve rather than passing unlimited world history.

### Conversation turn
One user/NPC exchange.

### Latency
Delay across STT, LLM and TTS before NPC response.

### Streaming
Returning text/audio incrementally before whole response completes.

### Local model
LLM/TTS/STT running on user's machine.

### Remote provider
Cloud/API service processing generation.

### API key
Credential for remote model provider; should not be bundled/logged/exposed by mod distributions.

## Mantella

### Mantella
Open-source Skyrim/Fallout 4 AI NPC framework using a Speech-to-Text → LLM → Text-to-Speech pipeline.

### Mantella server/application
External Python-based application coordinating model/STT/TTS services and Skyrim integration.

### Moonshine / Whisper
Speech-recognition engines supported by Mantella lineage.

### Piper
Local TTS engine used by AI NPC frameworks.

### xVASynth
TTS ecosystem for game-character voice synthesis.

### XTTS
Neural TTS model family supported by Mantella.

### Mantella conversation
Runtime session with one or more NPCs whose prompt context and generated responses are coordinated externally.

## SkyrimNet

### SkyrimNet
AI integration platform for Skyrim whose current architecture uses an in-process SKSE plugin rather than requiring an external WSL/server process for core integration.

### SkyrimNet prompt tree
Structured prompt/content hierarchy used to shape NPC behavior/context.

### SkyrimNet base library
Content library package containing templates, translations and vanilla/DLC/Creation character bios.

### Bio pack
Per-mod/community package providing AI character biographies/context for NPCs introduced by another plugin.

### SkyrimNet plugin
Content extension bundle that may contain prompts, triggers, actions, knowledge packs or virtual entities.

### Trigger
YAML-defined rule responding to game events and generating dialogue/narration/diary/bio behavior.

### Action definition
YAML entry exposing an approved Papyrus mod function/action to NPC AI behavior.

### Knowledge pack / .sknpack
Packaged world knowledge entries made retrievable when conditions match.

### Virtual entity
AI conversational character without ordinary physical NPC body/reference, represented by entity YAML and prompt/voice configuration.

### Plugin manifest
Metadata describing SkyrimNet content plugin.

### Freeform conversation
LLM-driven conversation separate from vanilla dialogue INFO/topic trees.

### Vanilla dialogue integration boundary
Current SkyrimNet documentation notes vanilla quest dialogue trees still use Skyrim's ordinary system; freeform AI dialogue is a separate pathway.

### Spriggit source plugin
SkyrimNet keeps ESP content in text/Spriggit form for version control and builds binary ESP during release.

## State/action safety

### Read-only context
Game state exposed to model for conversation but not directly modifiable.

### Consequential action
Model-generated request that changes quest/inventory/actor/world state.

### Action allowlist
Explicit set of functions AI framework is permitted to invoke.

### Argument validation
Checking generated target/forms/values before game execution.

### NPC agency boundary
Rules defining what an AI NPC may decide versus authored quest/game logic.

### Canonical quest state
Actual Skyrim quest/stage/alias state. Generated dialogue should not be treated as changing it unless a validated action actually does so.

### AI memory vs save state
Framework conversational memory can live outside ESS and differ from game quest/reference state.

### Lore pack vs canonical lore
Prompt/knowledge content should retain provenance; community bio/knowledge does not become Bethesda canon merely because an NPC says it.

## Diagnostic rules

1. Split failures by STT, LLM/provider, retrieval/prompt, TTS, game bridge and action execution.
2. Generated dialogue is not proof of game-state change.
3. Preserve exact model/provider/prompt/plugin versions for reproducible AI behavior.
4. Inspect external memory/config stores when established conversations behave differently from fresh setups.
5. Never expose provider API keys in logs/mod packages.
6. Action execution should be schema/allowlist validated rather than arbitrary model-generated code.
7. Vanilla dialogue/quest systems and AI freeform conversation can coexist but are separate control paths.

## Sources

- Mantella upstream: https://github.com/art-from-the-machine/Mantella
- SkyrimNet game plugin: https://github.com/MinLL/SkyrimNet-GamePlugin
- SkyrimNet plugins/content ecosystem: https://github.com/MinLL/SkyrimNet-Plugins
