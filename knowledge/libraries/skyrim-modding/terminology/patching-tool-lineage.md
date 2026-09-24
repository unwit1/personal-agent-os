# Skyrim Modding Terminology — Wrye Bash, Mator Smash, zEdit, and Patch Tool Lineage

Imported: 2026-09-24
Status: sourced deep-ingestion pass 4

## Core automated patch concepts

### Rule of one
Bethesda plugin behavior where, for most ordinary record fields, the last effective override wins rather than all plugin versions being automatically merged.

### Automated conflict resolution
Tool applies predefined field/rule logic to combine data from multiple plugins into a generated patch.

### Semantic conflict
Conflict whose correct result depends on mod intent and gameplay design, not just mechanically combining arrays/fields.

### Automated patch limitation
No generic patcher fully understands every author's intent; generated patches should be inspected for high-risk record families and known exceptions.

## Wrye Bash

### Wrye Bash
Long-running Bethesda modding utility with mod management, plugin inspection and Bashed Patch generation.

### Bashed Patch
Generated plugin that imports/merges selected data from other plugins according to Bash Tags and configured patchers/tweaks.

### Bash Tag
Metadata label telling Wrye Bash which categories of changes from a plugin should be imported/merged into the Bashed Patch.

### Relev
Tag historically used to mark leveled-list entries that should be treated as relevant additions/changes.

### Delev
Tag historically used to preserve deliberate deletions from leveled lists.

### Invent
Inventory-related Bash tagging family.

### Names
Bash tag/category allowing names from a plugin to be imported.

### Stats
Bash tag/category for selected stat data.

### Tweak Settings
Bashed Patch feature applying user-selected game-setting tweaks.

### Leveled-list merge
Bashed Patch specialization combining list changes so additions/removals from multiple mods can coexist according to tags/rules.

### Merge Patches
Historical Wrye Bash function for merging eligible plugins into the Bashed Patch to reduce plugin count; modern ESL usage reduces the importance of plugin-count merging for many setups.

### Bashed Patch regeneration
Patch should be rebuilt when relevant input plugins, Bash Tags, or load order change.

## Mator Smash

### Mator Smash
Automatic conflict-resolution tool based on the xEdit framework.

### Smashed Patch
Generated plugin combining changes from selected plugins according to Smash Settings.

### Smash Setting
Rule set controlling how record/subrecord data are combined.

### Smash.All
Broad default rule intended to combine compatible changes across many record types.

### Smash.ForceAll
More aggressive setting forcing inclusion/combination behavior.

### ITPO
**Expansion:** Identical To Previous Override. Override in generated patch that has no effect relative to immediately preceding effective state.

### Smash verification
Upstream documentation explicitly recommends checking generated output in xEdit and correcting incorrectly resolved conflicts.

### Smashed-patch bisect
Diagnostic technique deleting groups/records from a generated patch in halves/groups to isolate which generated record causes a crash or behavior problem.

### Smash plugin-count limit
Original xEdit-based Mator Smash architecture inherits legacy plugin-loading constraints; modern forks/workflows may differ, so verify tool version.

## zEdit / zPatch / zMerge

### zEdit
Bethesda modding tool environment by matortheeternal historically supporting plugin editing and patcher ecosystems.

### zPatch
Patcher framework/workflow associated with zEdit that generated load-order-specific patches.

### zMerge
Plugin merging workflow used to combine plugins and assets according to merge configuration.

### Merge
Combining multiple plugin files into one output plugin. This changes FormID/master relationships and is distinct from conflict resolution.

### Merge map
Mapping from original plugin/FormID identities to merged-plugin identities, needed by some tools to preserve references across merges.

### Merge rebuild
When input plugins change, merged output may need rebuilding and downstream generated patches may also need regeneration.

## xEdit merged patch

### Merged Patch
xEdit-generated patch that combines selected conflict data. Historically used as a generic patch baseline but less semantically capable than dedicated/manual patching for many record types.

### Manual xEdit patch
Author/user-created conflict-resolution plugin where individual fields are intentionally forwarded/combined.

### Conflict filter
xEdit view restricting records to conflicts to facilitate manual patch creation.

## Patch order

### Generator dependency chain
Order in which generated patches depend on other generated outputs.

### Upstream-generated patch
Patch that should exist before a later patcher scans the load order.

### Downstream-generated patch
Patch generated after prior patch outputs so it can see/consume them.

### Final conflict-resolution patch
Manually curated late-loading plugin intended to correct any remaining automatic patcher errors.

### Regeneration graph
Dependency graph identifying which generated artifacts must be rerun when an input mod changes.

## Modern relation to Synthesis/runtime patchers

- Wrye Bash: specialized imports/leveled-list/tweak ecosystem.
- Mator Smash: broad automatic static conflict resolution.
- xEdit: manual/automated record-level editing and analysis.
- Synthesis: code-based generated patch pipeline.
- SkyPatcher/SPID/KID/BOS/FLM: runtime/config-driven mutation that may avoid generating static overrides.
- DynDOLOD/Pandora/BodySlide: generate non-equivalent specialized outputs and must not be treated as generic conflict patches.

## Diagnostic rules

1. A generated patch is code/output, not truth. Inspect suspicious records in xEdit.
2. Rebuild generated patches after relevant inputs/load order change.
3. Never confuse plugin merging with conflict resolution.
4. FormID compaction/merging can invalidate external configs or generated patch references.
5. Keep generated outputs in separate managed mods with clear provenance.
6. Maintain a patch-order/regeneration graph in complex modlists.
7. Prefer domain-specific patchers over broad generic patchers when the domain semantics are known.
8. Manual final patching remains appropriate for conflicts requiring human intent.

## Sources

- Wrye Bash upstream: https://github.com/wrye-bash/wrye-bash
- Mator Smash upstream: https://github.com/matortheeternal/smash
- Mator Smash documentation/Nexus: https://www.nexusmods.com/skyrim/mods/90987
- Mutagen/Synthesis: https://mutagen-modding.github.io/Synthesis/
- xEdit documentation: https://tes5edit.github.io/docs/

## Provenance notes

Patching practices change as runtime distribution and ESL-capable workflows evolve. Historical recommendations such as aggressively merging plugins should not be promoted automatically into current best practice without checking the user's toolchain and constraints.
