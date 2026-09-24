# Skyrim Modding Tool Error Catalog

Imported: 2026-09-24
Status: active troubleshooting catalog

This catalog maps common tool warning/error classes to the subsystem that should be investigated. Exact message text/version should still be searched in current tool documentation.

## xEdit / SSEEdit

### Unresolved reference / Could not be resolved
Record field points to FormID/master that cannot be resolved.
Check:
- missing master;
- wrong master order/header;
- compacted/renumbered form;
- broken merge;
- deleted/missing Creation;
- malformed plugin.

### Error: record contains unexpected subrecord
Plugin binary/schema mismatch or corruption; verify game mode/tool version before editing.

### Found a reference, expected ...
Field contains incompatible form type.
Often caused by malformed plugin or incorrect script/automated patch.

### Deleted Navmesh
High-risk plugin state. Prefer navmesh repair/cleaning workflow rather than undelete-and-disable as for ordinary REFR.

### Deleted Reference
Clean with current xEdit Quick Auto Clean when appropriate; understand intentional deletions/official guidance.

### Identical To Master / ITM
Override reproduces master state. Often cleaning candidate, but context/version matters.

### FormID outside ESL range
Plugin flagged light but contains invalid local IDs for target runtime/format.

### Too many masters
Generated/plugin dependency count exceeds format/tool constraints.

## LOOT

### Cyclic interaction detected
Ordering metadata/master/group rules form a cycle.
Fix metadata/root conflict; do not randomly force more load-after rules.

### Missing requirement
Declared requirement absent. Distinguish LOOT metadata requirement from actual plugin MAST master.

### Incompatibility
Masterlist/user metadata declares two files incompatible; verify current versions and reason.

### Dirty plugin warning
CRC-specific cleaning information. Match exact file version/hash.

### Group ignored
Soft group order conflicts with hard master/dependency constraint.

## Mod Organizer 2

### Overwrite contains files
Tool generated loose output into MO2 Overwrite.
Move into named generated-output mod.

### Missing masters
Active plugin references disabled/absent master.

### Form 43 warning
Plugin appears LE-era; investigate actual port requirements, don't blindly resave everything.

### File conflict / lightning bolt
Asset overwrite relation, not ESP record conflict.

### Executable can't see virtual files
Tool not launched through MO2 or incompatible process/VFS context.

### Locked during external program
MO2 protects state while child process running.

### Mod is unmanaged
Files exist in real Data outside MO2 ownership.

## Vortex

### Deployment required
Staging state differs from game deployment.

### Cyclic rules
Before/after file/mod rules create cycle.

### Redundant mod
Every file overwritten by another deployment.

### External changes
Files in deployment target changed outside Vortex.

### Hardlink deployment failed
Filesystem/source/target cannot create expected hardlinks.

## Creation Kit

### Multiple master warning/failure
Editor config/version doesn't allow intended master load or file has unsupported dependency structure.

### MASTERFILE: File ... is a higher version than this EXE can load
CK/runtime/tool format mismatch.

### Navmesh finalize warnings
Unfinalized/invalid navmesh edges/doors/islands.

### Duplicate FormID/EditorID warning
Conflicting creation/identity; investigate before saving.

### Reference has no 3D
Missing model/resource or invalid base.

### FaceGen export missing
NPC/headpart/assets not loaded/valid or output path blocked.

### Lip generation failed
Audio/text/VoiceType/tool path/format problem.

### Assert / CK crash
Could be editor engine bug; reproduce with CKPE/current editor and minimal masters before assuming plugin corruption.

## Papyrus Compiler

### Cannot open store for class
Dependency PSC missing from compiler import path.

### Unknown type
Required parent/type script unavailable or misspelled.

### No viable alternative / mismatched input
Syntax error.

### Function does not exist
PSC dependency version doesn't declare called function.

### Cannot call a member function on a non-object
Compile-time type mismatch.

### Native function has a body
Native declaration syntax wrong.

### Property type mismatch
CK property/plugin value no longer compatible with script source.

### PEX succeeds but runtime Native function not found
Native DLL dependency failed to register; compiler cannot validate runtime implementation.

## SKSE/native plugins

### DLL plugin failed to load
Check:
- exact runtime;
- SKSE version;
- Address Library;
- VC++ runtime/import dependencies;
- correct architecture;
- duplicate variants.

### REL/ID not found
Address Library/plugin mapping doesn't contain requested relocation.

### Unsupported runtime
Plugin deliberately refuses unknown executable.

### Trampoline allocation failed
Insufficient requested trampoline memory or initialization error.

### Hook byte mismatch
Wrong runtime or another plugin already modified target.

### API version mismatch
Consumer requests interface provider doesn't support.

### Plugin API unavailable at PostLoad
Some providers require PostPostLoad or explicit ready message.

## Pandora / Nemesis / behavior generators

### Missing behavior file
Source graph/patch dependency absent.

### Invalid patch path
Patch targets node/path not present in current behavior version.

### Duplicate/invalid animation event
Two patches or malformed definition conflict.

### ERROR/WARN/FATAL
Use generator log component/patch name; successful process can still contain skipped patch warnings.

### Generated output overwritten
Behavior files exist but another mod wins asset priority.

### Too many animations / loading pressure
Behavior generation can succeed while runtime animation queue/asset load still struggles.

## BodySlide / Outfit Studio

### No image / purple preview
Texture path unavailable.

### Outfit not in group
SliderGroup XML doesn't include project.

### Preset not showing
Preset groups/body project mismatch.

### Build output not visible in game
Wrong output path/profile or another mod overwrites generated NIF.

### Clipping after morph
Outfit lacks matching sliders/TRI topology/weights.

### Exploded mesh
Bad weights/partitions/topology/skeleton.

## DynDOLOD / TexGen

### Unresolved FormID
Fix plugin/load-order error in xEdit first.

### File not found
Missing source mesh/texture/BSA resource.

### Error: LODGen failed
Inspect worldspace LODGen log and upstream asset/plugin errors.

### Texconv out of memory
Reduce memory/GPU workload, concurrent processes, resolution/settings; tool docs expose adapter/CPU fallback options.

### Too many full models
LOD rule/settings issue causing excessive full-model assignment.

### Billboard not found
Required tree/grass billboard/resource generation missing.

### Large reference bugs/errors
Worldspace/reference/plugin data conflict with large-ref system.

### Stale output
Inputs/load order changed after generation; regenerate.

### DynDOLOD warning policy
Official docs explicitly state warnings should be investigated because ignored issues can cause visual/gameplay problems or CTDs.

## xLODGen

### Terrain texture generation failure
Missing/invalid landscape texture or resource.

### LOD mesh generation failure
Worldspace height/landscape/plugin error.

### Out of memory
Reduce resolution/threading or split work where supported.

### Wrong game mode/path
Tool points to incorrect Data/runtime.

## ParallaxGen

### Missing texture
Mesh references map that does not exist.

### Unsupported shader
Source NIF/material cannot safely convert.

### Bad output mesh
Compare generated NIF to source and blocklist known exception.

### Wrong source winner
Generator's mod-manager priority differs from actual deployed asset winner.

## Synthesis

### Patcher failed to compile/download
Git/NuGet/.NET/network/repository issue.

### ModKey not found
Expected plugin absent/renamed.

### LinkCache resolve failure
Form link points to missing/unresolved form.

### Patcher exception
Inspect stack trace and exact record/form; isolate malformed input.

### Stale Synthesis patch
Load order/source changed; rerun pipeline.

## CAO / asset converters

### NIF conversion failed
Malformed/special mesh unsupported by selected profile.

### BSA packing failed
Invalid path/archive format/size/tool access.

### Texture conversion failed
Unsupported/corrupt DDS/source format.

### Destructive batch mistake
Process only copies/isolate source and retain originals.

## General troubleshooting sequence

1. Preserve exact error text and full log.
2. Record tool version/game mode/runtime/profile.
3. Identify first real error, not downstream cascades.
4. Resolve missing masters/unresolved forms before generating downstream output.
5. Reproduce with current tool version.
6. Validate filesystem permissions/path/VFS.
7. Isolate malformed input record/asset.
8. Rerun only downstream generated artifacts after fix.
9. Keep error + validated fix in corpus as version-scoped evidence.

## Sources

- DynDOLOD Messages: https://dyndolod.info/Messages
- DynDOLOD FAQ: https://dyndolod.info/FAQ
- xEdit documentation: https://tes5edit.github.io/docs/
- LOOT documentation: https://loot.github.io/docs/
- Pandora upstream/wiki
- BodySlide/Outfit Studio upstream
