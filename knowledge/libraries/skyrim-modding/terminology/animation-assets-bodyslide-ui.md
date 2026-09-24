# Skyrim Modding Terminology — Animation, NIF Assets, BodySlide, and UI

Imported: 2026-09-24
Status: sourced deep-ingestion pass 2

This reference covers asset-layer and animation/UI terminology that frequently gets mixed together during troubleshooting.

## Animation and behavior

### Animation
Motion data played by an actor/skeleton. In Skyrim, animation assets and behavior logic are related but distinct layers.

### HKX
Havok serialized file used by Skyrim for animation and behavior data.

### Havok Behavior
Middleware/system that controls animation logic through behavior graphs/state-machine structures.

### Behavior graph
Havok graph defining animation states, transitions, variables, events, and logic for an actor/skeleton behavior set.

### Animation clip
A unit of motion data referenced by behavior systems.

### Animation event
Named event sent through Skyrim's animation graph/runtime to trigger or react to transitions and gameplay logic.

### Animation graph variable
Runtime variable exposed to/used by behavior graphs and sometimes queried by SKSE/OAR conditions.

### Behavior patcher
Tool that merges/modifies behavior-graph changes into final game-ready HKX output.

### Generated behavior output
Behavior files produced by a patcher such as Pandora/Nemesis/FNIS based on installed patches/mod definitions. These generated files are assets and can themselves lose file conflicts in a mod manager.

### FNIS
**Expansion:** Fore's New Idles in Skyrim.  
Historical behavior-generation ecosystem that introduced widely used mod behavior patch conventions and animation-list formats.

### Nemesis
Behavior patching/generation tool that became a common successor/alternative to FNIS for many humanoid behavior mods.

### Pandora Behaviour Engine
Modern modular behavior patcher for Skyrim SE that patches Havok behavior/animation project files and supports Nemesis and FNIS patch formats plus its own mechanisms.

### Pandora patch
Mod-supplied behavior modification definition consumed by Pandora to alter final behavior output.

### Graph injection
Adding variables/nodes/animations or references from modded graphs into an existing behavior graph rather than fully replacing the vanilla graph.

### Behavior conflict
Two behavior modifications targeting overlapping graph structures in incompatible ways. This is distinct from two animation HKX files simply overwriting each other.

### Conditional animation replacer
Runtime framework that chooses among animation files based on conditions without itself being the tool that merges core behavior graphs.

### DAR
**Expansion:** Dynamic Animation Replacer.  
Earlier runtime conditional animation-replacement framework whose folder/condition ecosystem became widely used.

### OAR
**Expansion:** Open Animation Replacer.  
Open-source SKSE animation replacement framework that chooses animations based on configurable conditions, includes an in-game editor, and supports SE/AE/VR.

### OAR condition
Predicate controlling when a replacement/submod/animation is eligible.

### OAR submod
Logical OAR animation package/config section containing replacement animations and condition metadata.

### OAR priority
Ordering used when multiple OAR replacements are eligible for the same animation path/context. Runtime priority is separate from ordinary mod-manager file priority.

### Animation variant
Multiple possible replacement animations under one logical condition/set, chosen according to configured OAR variant behavior.

### Paired animation
Animation involving synchronized behavior between two actors/participants, requiring special handling beyond an ordinary one-actor replacement.

### Behavior patcher vs OAR
Pandora/Nemesis/FNIS modify/generated behavior graph output; OAR performs runtime conditional replacement of animation assets. A mod can require both because they solve different layers.

## Skeleton and skinning

### Skeleton
Hierarchical bone/node structure used to animate a character/creature/mesh.

### Bone
Transform node in a skeleton that influences skinned mesh vertices and animation.

### Bone weight
Amount a specific bone influences a mesh vertex.

### Skinning
Binding mesh vertices to skeleton bones with weights so the mesh deforms during animation.

### Weight painting
Editing per-vertex bone influences on a mesh.

### Reference skeleton
Skeleton file used by tools such as Outfit Studio to identify bones and transforms when editing/skinning meshes.

### Skeleton mismatch
Failure caused by an asset/mod expecting bones/nodes that are missing or named differently in the active skeleton.

## NIF and mesh terminology

### NIF
NetImmerse/Gamebryo/Creation Engine model format used extensively by Skyrim for meshes and scene graphs.

### NifSkope
NifTools editor/viewer for reading, inspecting, editing, and writing NIF files.

### NIF block
Structured object/node/property inside a NIF file. NIFs are graphs/collections of typed blocks rather than a flat mesh-only format.

### Scene graph
Hierarchy of nodes/shapes/properties describing transform relationships and rendering/animation-related structure.

### Node
Scene-graph element that can hold transforms and children.

### Shape
Renderable geometry element within a NIF.

### BSTriShape
Common Skyrim SE geometry block representing triangle mesh data.

### Vertex
Single mesh point with position and potentially normal, tangent, UV, color, and skinning data.

### Triangle
Three vertex indices defining one polygonal face.

### Normal
Vector describing surface orientation for lighting calculations.

### Tangent / bitangent
Vectors used with normal maps/tangent-space shading.

### UV
2D texture coordinate mapping a mesh vertex to texture space.

### Vertex color
Per-vertex color/alpha data used by certain shaders/effects.

### Shader property
NIF block describing rendering behavior and texture/material inputs.

### BSLightingShaderProperty
Bethesda lighting shader property commonly used on Skyrim meshes.

### BSEffectShaderProperty
Bethesda effect-oriented shader property used for certain emissive/particle/effect-style meshes.

### Texture set
Collection of texture paths/slots used by a shader.

### Collision
Physical interaction representation associated with a model/reference, often separate from visible geometry.

### Havok collision
Collision representation using Havok-related NIF blocks/data.

### Partition
Skinned-mesh subdivision/grouping used for body/equipment rendering and skin data. Incorrect partitions/body slots can produce disappearing or malformed armor/body results.

### Body slot
Gameplay/equipment slot numbers used by armor and related rendering systems. Armor record slots and mesh partitions must be compatible.

### Mesh path
Relative path under the game data structure to a NIF asset.

### Texture path
Relative path to DDS assets referenced by NIF shader/texture data or records.

### Loose mesh
NIF supplied directly in the effective data filesystem rather than only from an archive.

### Asset overwrite
When multiple mods supply the same mesh/texture/animation path and one file wins according to mod-manager/virtual filesystem priority.

## BodySlide and Outfit Studio

### BodySlide
Tool for applying slider presets to compatible body/outfit projects and building final mesh outputs.

### Outfit Studio
Companion mesh/project editing tool used to create/convert BodySlide projects, edit shapes, conform sliders, copy bone weights, and export Skyrim meshes.

### BodySlide project
Definition containing one or more shapes plus slider data and output information so BodySlide can generate final meshes.

### Slider
Named morph control that moves vertices according to stored delta data.

### Slider value
Amount of a morph applied during preview/build.

### Slider set
Collection of sliders and project/output metadata for one compatible body/outfit set.

### Preset
Saved collection of slider values that can be applied across compatible BodySlide groups/projects.

### Group
BodySlide organization mechanism connecting projects/outfits/presets so compatible presets appear for relevant sets.

### Reference shape
Mesh used as the authoritative target for sliders/weights during outfit conversion or conforming.

### Conversion reference
Reference project/sliders designed to transform geometry from one body/base shape toward another.

### Conform
Transfer/project slider movement from a reference shape to an outfit/other mesh so it follows the same body morphs.

### Slider delta
Per-vertex displacement associated with a slider.

### Base shape
Underlying geometry at the project's base slider state.

### Low-weight mesh
Skyrim body/outfit mesh convention using the `_0.nif` variant for the low end of actor body weight.

### High-weight mesh
Skyrim body/outfit mesh convention using the `_1.nif` variant for the high end of actor body weight.

### Weight morph
Interpolation between low/high weight variants according to actor weight.

### TRI
Morph-data file used by Skyrim/RaceMenu/BodySlide-related systems for vertex morph targets.

### BodyMorph
RaceMenu ecosystem terminology for applying compatible BodySlide morph data dynamically in game instead of only baking one static mesh shape.

### Build Morphs
BodySlide option/workflow producing morph data (commonly TRI output for Skyrim SE BodyMorph use) along with built meshes.

### Batch Build
BodySlide operation that builds many compatible outfits/projects in one run using a selected preset.

### Output conflict
Two BodySlide projects generating the same output NIF path. Batch Build normally requires selecting which project should own that output.

### Zap
BodySlide slider/flag designed to hide/remove selected mesh geometry in generated output.

### Clipping
Visible intersection where one mesh penetrates another, commonly body through clothing/armor or overlapping outfit geometry.

### Copy Bone Weights
Outfit Studio operation that transfers skin weights from a reference mesh to selected outfit geometry.

### ShapeData
BodySlide/Outfit Studio project data directory containing project source mesh/slider data used to generate outputs.

### SliderSets
Directory/config layer containing BodySlide slider-set/project definitions such as OSP/XML data.

### SliderPresets
Directory containing saved preset XML values.

## UI and configuration menus

### SkyUI
Major Skyrim UI overhaul/framework that also provides the Mod Configuration Menu API used by many mods.

### MCM
**Expansion:** Mod Configuration Menu.  
SkyUI-provided in-game menu surface for mod-specific configuration.

### MCM script
Papyrus script implementing a mod's MCM behavior through SkyUI's API.

### MCM registration
Process by which a mod's MCM script becomes known/available to SkyUI.

### MCM Helper
Framework that streamlines SkyUI MCM creation and supports configuration-driven menu definitions/settings persistence.

### SWF
Shockwave Flash/Scaleform movie format used by Skyrim's UI system.

### Scaleform
Flash-based UI middleware underlying Skyrim menus. Mods such as SkyUI replace/extend SWF menu assets and interact with the UI runtime.

### UI asset conflict
File conflict where one mod's SWF/interface assets overwrite another's. This is separate from plugin-record load order.

### Interface folder
Data-path area containing menu SWFs and UI-support assets.

### MCM settings persistence
Mechanism by which menu values survive between sessions/saves. Depending on the mod/framework, settings may live in save-side Papyrus state, INIs, JSON/config files, FISS/JContainers/PapyrusUtil data, or MCM Helper settings.

## Troubleshooting rules encoded for Agent OS

1. Determine whether an animation problem is a **behavior-generation problem**, an **animation-file overwrite**, or an **OAR runtime-condition problem** before recommending fixes.
2. Do not tell users to regenerate Pandora/Nemesis output for a pure OAR-condition issue unless behavior generation is actually involved.
3. Inspect generated behavior output as ordinary assets in the mod manager; another mod can overwrite it.
4. For armor/body problems, inspect ARMO/ARMA records **and** NIF partitions, skeleton/bones, weights, BodySlide output, and asset priority.
5. Treat BodySlide output as generated assets with their own overwrite priority.
6. A preset changes slider values; it does not by itself fix bad weights, partitions, clipping, missing bones, or incompatible topology.
7. NIF shader/texture problems and plugin-record texture-set problems are separate paths to a visually similar symptom.
8. UI/MCM registration problems can be Papyrus/framework issues even when the SWF assets load correctly.
9. Distinguish MCM configuration persistence from save-game gameplay state.
10. Record which behavior generator and which conditional replacer are in use; “animation mod” is not specific enough for diagnostics.

## Sources

- Open Animation Replacer upstream: https://github.com/ersh1/OpenAnimationReplacer
- Pandora Behaviour Engine+ upstream: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus
- Pandora wiki: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus/wiki
- NifSkope upstream: https://github.com/niftools/nifskope
- NifSkope architecture docs: https://github.com/niftools/nifskope/blob/develop/DOXYGEN.md
- BodySlide and Outfit Studio upstream: https://github.com/ousnius/BodySlide-and-Outfit-Studio
- BodySlide/Outfit Studio wiki — creating projects: https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Creating-a-BodySlide-project
- BodySlide/Outfit Studio wiki — conversion references: https://github.com/ousnius/BodySlide-and-Outfit-Studio/wiki/Conversion-references-and-using-them
- SkyUI upstream: https://github.com/schlangster/skyui
- MCM Helper documentation: https://github.com/Exit-9B/MCM-Helper/wiki

## Provenance notes

Animation terminology evolves quickly. Pandora and OAR are active projects; exact supported patch formats, runtime versions, config grammar, and priority rules should be checked against installed/current releases when implementing or debugging.
