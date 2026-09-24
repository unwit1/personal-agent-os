# Skyrim Modding Terminology — EasyNPC, NPC Replacers, and Appearance Synthesis

Imported: 2026-09-24
Status: sourced deep-ingestion pass 18

## NPC replacer problem

### NPC replacer
Mod changing NPC appearance through NPC_ record data, HeadParts and/or FaceGen assets.

### Appearance source
Mod selected as authoritative visual appearance for one NPC.

### Default/source plugin
Plugin providing desired gameplay data/identity for NPC before appearance merge.

### Face source
Replacer whose headparts/morph/tint/FaceGen should win.

### NPC conflict
Multiple overhauls edit same NPC_ record for appearance and gameplay changes.

### Dark-face conflict
Winning NPC_ appearance fields do not match winning FaceGeom/FaceTint assets.

### Record/asset split
NPC appearance depends on both plugin values and external generated files, so ordinary conflict resolution must coordinate both.

## EasyNPC

### EasyNPC
Tool selecting per-NPC appearance from multiple replacers and building a consolidated NPC appearance/output mod.

### EasyNPC Next
2026 modern continuation/rework adding fixes and quality-of-life improvements to original EasyNPC workflow.

### Profile
Saved EasyNPC selection data mapping NPCs to appearance/default sources.

### Default plugin
Chosen source for non-appearance/gameplay NPC record basis.

### Face plugin
Chosen appearance/replacer source.

### Build
Process generating output plugin and collecting/copying required FaceGen/assets.

### Merged NPC output
Generated plugin forwarding selected gameplay data while applying selected appearance.

### FaceGen copy
Generated output copies matching face mesh/tint from selected appearance source into consolidated mod.

### Asset mapping
Tool determines original replacer FaceGeom/FaceTint paths based on source plugin/FormID and remaps/copies into output.

### HeadPart master
Plugin required because selected replacer's NPC references custom hair/eyes/high-poly head parts.

### Mugshot/preview
UI representation helping user choose among available NPC replacers.

### Blacklist
NPC/mod excluded from automatic merge or handled manually.

### Custom NPC
Mod-added actor requiring correct source FormID/plugin identity.

### Face mismatch report
Tool/build warning where expected FaceGen assets cannot be found or source data is inconsistent.

## Replacer selection semantics

### One visual source per NPC
Choose coherent head appearance from one replacer unless manually rebuilding FaceGen from combined parts.

### Gameplay forwarding
Preserve changes from AI/combat/perk/quest mods into generated NPC_ output while appearance fields come from selected replacer.

### Appearance fields
HeadParts, head texture, face morphs, tint layers, hair color, weight and other appearance-relevant NPC_ data.

### Gameplay fields
Stats, factions, perks, outfits, packages, combat style, class and other nonappearance values.

### Mixed field hazard
Some fields such as weight/race can affect both gameplay and generated appearance, so clean separation is not always possible.

### Replacer master pruning
Remove masters no longer required after output consolidation only after verifying all records/assets.

### Standalone assets
Replacer uses private texture/mesh paths rather than global skin/hair paths.

### High Poly Head dependency
Selected NPC appearance references HPH HeadPart assets and requires corresponding master/assets.

### KS Hair/other hair dependency
Custom HeadParts can become output dependencies.

## Build/load-order strategy

### Source replacers disabled after build
Common EasyNPC workflow disables original NPC replacer plugins/assets once consolidated output contains selected results, while required asset/master dependencies remain enabled.

### EasyNPC output priority
Generated output plugin/assets should win relevant NPC/FaceGen conflicts.

### Regeneration trigger
Adding/removing/updating replacer, gameplay NPC overhaul, high-poly-head/hair dependency or changing selections -> rerun/review output.

### Patch after EasyNPC
Downstream compatibility patch can target generated NPC output if it needs final gameplay adjustments.

### Appearance patch before EasyNPC
Source compatibility mods may need to be included/visible before build depending on desired data selection.

## Synthesis/SynthEBD relationship

### SynthEBD
Synthesis patcher ecosystem assigning appearance/body/height/asset distributions across NPCs with deterministic/consistent rules.

### Appearance synthesis
Generated NPC appearance based on rules rather than manual one-NPC selection.

### Asset pack
Set of skins/bodies/textures/etc. from which SynthEBD assigns NPC assets.

### Consistency file
Stored assignment history keeping same NPC appearance across reruns when possible.

### NPC group
Rule grouping actors by race/sex/faction/etc. for assignment.

### EasyNPC vs SynthEBD
EasyNPC primarily selects/merges authored NPC replacer faces; SynthEBD primarily distributes configurable asset/body combinations. They can coexist if responsibilities/output order are planned.

## FaceGen regeneration

### CK FaceGen export
Generate head mesh/tint from final NPC_ record rather than copying replacer-supplied assets.

### Copied FaceGen
Preserve original replacer's handcrafted/generated face exactly.

### Regenerated mismatch
CK generation can differ from replacer's custom sculpt/tool pipeline; don't regenerate if exact replacer FaceGen should be preserved unless necessary.

### FormID filename mapping
FaceGen filename corresponds to NPC local/base FormID under plugin-name directory; merged output can require remapping/copying to output plugin identity.

## Diagnostic rules

1. Final NPC_ and FaceGen must come from a coherent appearance decision.
2. Do not forward individual face fields from multiple replacers casually.
3. Preserve non-appearance gameplay edits from AI/combat/quest mods.
4. Check custom HeadPart masters/assets after pruning source replacers.
5. Weight/race can affect both visual and gameplay state.
6. Rebuild generated NPC synthesis after relevant source changes.
7. EasyNPC output itself becomes part of load order and can be overwritten later by another NPC patch.
8. Established save can contain actor inventory/package/morph state, but NPC_ face mismatch is still primarily a current record+asset issue.

## Sources

- EasyNPC Next current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/187138
- Original EasyNPC lineage/documentation: current EasyNPC project archives/community documentation
- SynthEBD upstream: https://github.com/Synthesis-Collective/SynthEBD
- Creation Kit FaceGen packaging/path references: https://ck.uesp.net/wiki/File_menu

## Dated snapshot

EasyNPC Next 1.3.0.0 was current on 2026-09-24, updated 2026-08-30. Preserve output tool version/profile/source-mod versions for reproducibility.
