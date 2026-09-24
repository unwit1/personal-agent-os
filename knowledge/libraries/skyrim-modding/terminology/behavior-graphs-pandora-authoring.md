# Skyrim Modding Terminology — Havok Behavior Graphs and Pandora Authoring

Imported: 2026-09-24
Status: sourced deep-ingestion pass 9

## Havok Behavior architecture

### Havok Behavior
Middleware used by Skyrim to express animation logic as interconnected finite-state-machine graphs serialized into HKX packfiles.

### hkb
Havok Behavior class/object family used for behavior graphs, state machines, generators, modifiers, variables and events.

### hka
Havok Animation class/object family used for skeletons, animations, animation containers and related animation data.

### Behavior project
Collection of behavior graphs, character data, skeleton data and animation references belonging to one actor/creature family.

### Character project
Behavior data defining character variables, events, animation bindings and graph relationships.

### Skeleton project
Project-level skeleton description and indices used by behavior graphs and animations.

### Behavior graph
Serialized network of hkb nodes producing animation output and reacting to variables/events.

### State machine
Node containing discrete states and transitions.

### State
One mode inside a state machine, such as locomotion, attack ready, attack, stagger or other project-specific state.

### Transition
Rule moving from one state to another based on events/conditions/transition metadata.

### Generator
Behavior node producing animation/motion output.

### Modifier
Behavior node that alters/filters/transforms animation or behavior data.

### Clip generator
Node playing an animation clip.

### Blend generator
Node combining multiple animation sources.

### Behavior variable
Typed value—commonly bool/int/real—used by graph logic.

### Behavior event
Named/indexed signal delivered to the graph and used to trigger transitions or logic.

### Event ID
Project-local numeric/indexed representation of an animation event.

### Variable ID
Project-local index corresponding to a named behavior variable.

### Animation binding
Relationship mapping clip references/IDs to animation HKX assets.

### Annotation
Timed metadata attached to an animation clip. Skyrim behavior frameworks can use annotations to fire animation events or carry additional payload data.

### Behavior graph index instability
Internal HKX object identifiers and layout may shift when graphs are regenerated; authoring patches should target meaningful/validated paths rather than assuming arbitrary indices remain timeless.

## Pandora Behaviour Engine+

### Pandora
Modern behavior patcher for Skyrim SE that reads behavior/animation projects, applies mod-authored patches and writes merged game-ready HKX output.

### Behavior patcher
Tool merging edits from multiple behavior mods so one final graph can contain compatible changes from many sources.

### Pandora patch
Patch definition consumed by Pandora.

### Pandora native patch format
Single XML patch per target graph using operations such as replace, insert, append and loose edits.

### replace
Patch operation replacing data at a selected path.

### insert
Patch operation inserting data into a selected structure.

### append
Patch operation adding data at the end of a selected structure.

### loose
Pandora patch operation applying content without normal strict replacement semantics according to Pandora's format.

### edit path
Pandora selector identifying a target object/property path inside behavior XML.

### Native DTO
Pandora internal data-transfer representation used to parse/modify/serialize Havok structures.

### Assembler
Pandora component parsing mod patch syntax into patch operations.

### Dispatcher
Pandora component applying prepared edits to target behavior structures.

### Validator
Pandora component validating modified nodes/layout and protecting output from invalid edits.

### Exporter
Pandora stage serializing validated behavior data to game-ready binary HKX.

### Pandora Engine.log
Verbose behavior-generation log containing severity/component/data/operation/status information.

### INFO
Pandora informational log severity.

### WARN
Unexpected condition that may be a problem but did not necessarily stop output.

### ERROR
Failure that prevented a specific portion of patch work and is likely relevant.

### FATAL
Failure preventing the engine from completing output.

## File targeting

### ProjectName~FileName
Pandora full unique target identifier disambiguating graphs with the same short filename across behavior projects.

### Short target name
Convenience filename identifier when unique enough inside the current patch context.

### _1stperson project
First-person behavior project distinct from default third-person humanoid behavior.

### Creature project
Behavior project associated with a creature family such as horses/dragons/werewolves/etc.

### character file
Project metadata file describing variables/events/animation behavior relationships.

### skeleton file
Project skeleton definition.

### Indirect identifier
Pandora target syntax such as project_character or project_skeleton selecting special project files.

### Custom graph injection
Pandora experimental feature adding graph content beyond ordinary edits. High-risk and author-oriented.

## Legacy patch compatibility

### FNIS patch format
Legacy behavior patch/list format supported for compatibility by modern engines where possible.

### Nemesis patch format
Patch convention from Nemesis Behavior Engine supported substantially by Pandora.

### Pandora-native format
Newer XML format intended to be more self-contained, efficient and fault-tolerant.

### Behavior patch migration
Converting old FNIS/Nemesis patch definitions to native Pandora patches while preserving graph intent.

### Behavior engine output
Generated HKX files that must win asset conflicts over unpatched originals.

## Behavior variables/events in modern ecosystems

### Graph-variable injection
BDI-style runtime addition of variables without rebuilding static graph files.

### Static graph variable
Variable compiled/generated into behavior project data.

### Graph event injection
Runtime addition of event IDs.

### Animation event
Runtime signal passed through actor animation graph, sometimes originating in clip annotations.

### Event sink
Native listener receiving animation graph events.

### SendAnimationEvent
Papyrus/native call sending an animation event to a graph.

### Variable bridge
Framework/mod using graph variables as state interchange between native code, behavior and animations.

## Common failure modes

### Missing behavior patch
Mod expects graph state/event that was never generated.

### Stale Pandora output
Behavior generated before adding/removing/updating a dependent behavior mod.

### Output overwritten
Another mod provides behavior HKX after Pandora output in asset priority.

### Invalid patch path
Patch references a graph path/node not present in target behavior version.

### Project mismatch
Patch intended for default humanoid graph targets first-person/creature/another graph incorrectly.

### Event mismatch
Animation sends event absent from current graph or behavior expects an event no clip sends.

### Variable mismatch
Framework reads/writes a graph variable that was not generated/injected.

### Graph corruption
Invalid structural patch causes malformed output; Pandora validation may revert invalid nodes, but a successful run does not guarantee semantic correctness.

### Skeleton index mismatch
Behavior/animation refers to bone/index assumptions inconsistent with the active skeleton.

## Authoring rules

1. Identify exact behavior project and target graph before patching.
2. Keep one minimal patch concern per change where possible.
3. Use meaningful event/variable names and document ownership.
4. Prefer runtime injection when only adding supported variables/events and a static graph rewrite is unnecessary.
5. Prefer a behavior patch when new states/transitions/graph structure are actually required.
6. Regenerate output after any behavior mod update.
7. Treat WARN/ERROR/FATAL in Engine.log according to the affected patch; don't assume "Pandora finished" means every patch applied.
8. Keep debug XML only as authoring diagnostics; game consumes binary HKX.
9. Creature and first-person behavior require explicit target support.
10. Test behavior transitions in game under every supported weapon/state/race path.

## Sources

- Pandora Behaviour Engine+: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus
- Pandora wiki: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus/wiki
- SCAR behavior-patching documentation: https://github.com/max-su-2019/SCAR/tree/main/docs
- Behavior Data Injector documentation: https://www.nexusmods.com/skyrimspecialedition/mods/78146
