# Skyrim Modding Terminology — Engine Limits, Reference Counts, Save Size, File Handles, and Performance Diagnosis

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module records resource limits and performance concepts that are often confused with ordinary mod conflicts.

## File and plugin resource limits

### File handle
Operating-system/C-runtime handle used by Skyrim to keep files/resources open.

### File-handle exhaustion
Process reaches available handle/stdio limit, producing failures that can masquerade as corrupted saves or missing resources.

### MaxStdio
SSE Engine Fixes feature increasing the process's C stdio handle limit above vanilla defaults.

### False save corruption
Failure mode where save/load UI reports or behaves as though saves are corrupt because file-handle/resource exhaustion prevents normal file operations.

### Full plugin slot
Standard plugin load-order index space used by non-light plugins.

### Light plugin slot
FE light-index space used by ESL-flagged plugins.

### Master count
Number of distinct plugin masters referenced by one plugin.

### Master overflow
Generated/merged patch requires more masters than supported by the writer/format/runtime workflow.

## Reference-handle system

### Reference handle
Engine-managed handle identifying runtime references without storing raw pointers everywhere.

### Reference handle cap
Finite size of Skyrim's global reference-handle space. Extremely large load orders/new-land mods can approach it.

### Loaded reference
Object reference instantiated/represented in runtime state.

### Persistent reference
Reference kept addressable because engine/quest/script systems need it beyond ordinary temporary-cell rules.

### Temporary reference
Reference governed through cell loading/unloading and master-file behavior; ESM treatment can reduce how many references become permanently counted at startup for large plugins.

### Temporary-reference loading
Engine behavior where temporary refs from masters are loaded according to cell need rather than all contributing equally to initial reference-handle use.

### ESMification
Community term for setting a suitable plugin to master/ESM behavior so temporary references are handled as master data. This can reduce reference pressure for large new-land/location plugins but changes load-order/record semantics and requires validation.

### Reference count warning
Engine Fixes/DynDOLOD-related diagnostic warning that a load order is approaching dangerous reference-handle usage.

### New-land plugin
Plugin adding very large numbers of world references/cells, making it a common reference-count contributor.

### Reference-heavy plugin
Plugin defining many placed references even if not a new worldspace.

### Temporary=1
DynDOLOD configuration option documented as potentially reducing reference usage in some large-load-order scenarios; DynDOLOD documentation prefers appropriate ESM conversion of large new-land plugins as the more general solution.

## Save limits

### SaveGameMaxSize
SSE Engine Fixes setting increasing supported save-game size limit for sufficiently large modded saves.

### Save compression
Compression algorithm applied to save payload.

### zlib save compression
Older/alternative Skyrim save compression mode.

### LZ4 save compression
Modern/default compression mode in relevant Skyrim SE versions/configurations.

### Uncompressed save
Save mode with no compression; larger disk size and different limits/performance implications.

### Save bloat
Informal term for save growth from legitimate or pathological persistent state. File size alone does not prove corruption.

### Papyrus-state growth
Increasing saved script instances/arrays/stacks/registrations and associated data.

### ChangeForm growth
Increasing number/size of saved changed-form records as the player interacts with/modifies the world.

### Orphaned state
Saved state whose original mod/form/script relationship is no longer valid after uninstall/change.

## CPU/GPU/frame-time concepts

### FPS
Frames per second. Reciprocal of frame time, not a direct measure of simulation correctness.

### Frame time
Milliseconds required to produce one frame. Stable low frame time usually matters more than average FPS alone.

### Frame-time spike
Brief long frame causing visible stutter.

### 1% low
Performance statistic describing slower tail of frame-rate distribution; useful for stutter analysis.

### Main thread
Primary game thread handling substantial simulation/render submission/gameplay work.

### Render thread
Thread(s) involved in preparing/submitting rendering work.

### Papyrus workload
Script VM work consuming allotted processing time and producing queued stacks/events.

### Draw-call bottleneck
CPU-side cost of submitting many objects/materials/lights.

### GPU fill-rate/shader bottleneck
GPU limited by resolution, shader complexity, overdraw or post-processing.

### VRAM
GPU-local video memory used by textures, render targets, meshes and other graphics resources.

### VRAM oversubscription
Working set exceeds practical VRAM budget and causes eviction/streaming/stutter.

### RAM
System memory used by game/process/tool data.

### Commit charge
Windows virtual-memory commitment; heavy modding can fail when system RAM/pagefile commitment is exhausted even if some physical RAM remains.

### Pagefile
Disk-backed virtual memory used to satisfy committed memory beyond physical RAM.

### Working set
Pages of process memory currently resident in physical RAM.

### I/O bottleneck
Loading/decompression/storage latency limits asset streaming or startup.

### Shader compilation stutter
Frame/startup stalls while new shader variants compile.

### Asset streaming
Loading textures/meshes/audio as needed rather than keeping every asset resident.

## Script performance

### Stack dump
Papyrus diagnostic emitted when VM workload/backlog reaches problematic conditions; it is evidence of script pressure, not necessarily one script's fault.

### Event storm
Large number of events delivered in a short period.

### Unbounded polling
Script repeatedly schedules/checks without sensible interval/termination.

### Update loop
Recurring OnUpdate/RegisterForUpdate logic.

### Single-update loop
Recurring pattern re-registering one update at a time, allowing better control over scheduling.

### Latent backlog
Many suspended stacks waiting on latent operations.

### Script latency
Delay between when an event/state change occurs and when Papyrus code gets CPU time to process it.

### Save-time script state
Papyrus stacks/instances/registrations serialized into saves, contributing to persistence and load time.

## Object/render performance

### Reference density
Number of active/rendered objects in nearby cells.

### Draw distance
Distance at which object/actor/item/grass/detail classes remain active/rendered.

### LOD distance
Thresholds controlling transitions to distant representations.

### Large reference distance
Separate system controlling full-model display of large references beyond ordinary active cells.

### Occlusion culling
Skip rendering objects hidden behind other geometry/rooms/occluders.

### Frustum culling
Skip objects outside camera viewing volume.

### Portal culling
Interior Room Bound/portal system limiting visible room sets.

### Shadow distance
Distance over which shadow-casting objects/lights are processed.

### Shadow resolution
Pixel resolution of shadow maps; higher values increase GPU/memory cost.

### Grass density
Amount of generated/displayed grass; affects CPU/GPU/geometry cost.

### Grass cache
Precomputed grass placement data used by certain modding workflows/frameworks.

### Grass LOD
Distant grass representation generated/used by modern DynDOLOD/No Grass In Objects-related ecosystems.

### Object LOD atlas
Texture atlas used by generated object LOD meshes.

## Large references

### Is Full LOD / Neverfade
Reference flag/behavior causing full model to remain visible outside normal active cells.

### Large reference
Skyrim SE/VR system listing eligible references to render as full models farther away.

### Large-reference bug
Engine bug class caused by incompatible modifications/state of large references, producing flicker/disappearance/transition problems.

### Large-reference workaround
DynDOLOD DLL NG/scripts system mitigating known large-reference bugs under documented prerequisites.

### RNAM large-reference data
Worldspace data identifying large references/cell associations.

### Partial Form flag
Supported record flag where certain override record types only replace provided portions instead of behaving as full ordinary overwrite; modern DynDOLOD versions explicitly support applicable partial-form use.

## Diagnostic rules encoded for Agent OS

1. Do not conflate file-handle exhaustion with reference-handle exhaustion; they are different limits and have different remedies.
2. Do not recommend ESM-flagging solely because plugin count is high; use reference-count evidence and validate plugin suitability.
3. Save size, Papyrus state and ChangeForms are separate contributors to save behavior.
4. FPS averages can hide stutter; collect frame-time data.
5. Determine CPU vs GPU bound before lowering random visual settings.
6. When performance degrades over a long save but a new game is fast, investigate persistent script/changeform/runtime state.
7. Large-reference warnings are world-rendering/record-structure evidence, not generic “LOD is broken.”
8. Treat pagefile/commit exhaustion separately from VRAM exhaustion.
9. Generated LOD, grass and shader caches must be regenerated after relevant source changes.
10. Prefer logs/measurements over folklore tweaks to Papyrus budgets, uGridsToLoad or memory settings.

## Sources

- SSE Engine Fixes: https://www.nexusmods.com/skyrimspecialedition/mods/17230
- DynDOLOD FAQ: https://dyndolod.info/FAQ
- DynDOLOD Large References: https://dyndolod.info/Help/Large-References
- DynDOLOD Changelog/current implementation notes: https://dyndolod.info/Changelog
- SSE Display Tweaks: https://github.com/SlavicPotato/SSEDisplayTweaks
- Creation Kit Wiki Papyrus logging/stack notes: https://ck.uesp.net/wiki/User:DavidJCobb/Papyrus_logging
