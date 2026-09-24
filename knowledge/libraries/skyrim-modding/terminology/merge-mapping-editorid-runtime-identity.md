# Skyrim Modding Terminology — Merge Mapping, EditorIDs, and Runtime Form Identity

Imported: 2026-09-24
Status: sourced deep-ingestion pass 21

## Identity layers

### FormID
Runtime/plugin numeric identifier whose high bits/load mapping depend on plugin type and load order.

### Local FormID / ObjectID
Plugin-local part of a form identity before current load-order mapping.

### FormKey
Stable conceptual identity combining originating plugin with local form ID, as used by Mutagen-style tooling.

### EditorID / EDID
Human-readable author identifier such as `GuardWhiterun` or `RecipeArmorIronDagger`.

### Display name
Localized/full user-facing name. Distinct from EditorID.

### Runtime form pointer
In-process memory address of a loaded form. Not a persistent/stable identity.

### Reference identity
Placed/runtime reference has its own FormID/EditorID relationship separate from base form identity.

### Origin plugin
Plugin in which a form was originally created.

### Winning plugin
Last static override providing current plugin-record data; does not become form's origin.

## Plugin merging

### Merge
Combining records from multiple source plugins into a new output plugin.

### zMerge
zEdit tool/workflow producing merged plugins plus mapping metadata.

### Merge map
Mapping from old source plugin + FormID identities to new merged plugin + FormID identities.

### Remapped FormID
New identity assigned to form after merge.

### Merge metadata
JSON/data produced by zMerge describing source plugins and form mappings.

### Merged plugin
Output ESP/ESM containing records previously spread across multiple source modules.

### Source plugin removal
Original plugins are disabled after merge; any external config/script still naming them can break unless remapped.

### Merge identity breakage
Papyrus/native/config lookup using old plugin filename/FormID no longer resolves after zMerge changes identity.

### External reference
INI/JSON/script/native data referring to a form by plugin name/FormID outside plugin master relationships.

### Config remap
Runtime/tool conversion of old external identity into merged output identity.

## MergeMapper

### MergeMapper
SKSE/SKSEVR DLL by alandtse that exposes zMerge merge mappings so Papyrus scripts and other DLLs can resolve original identities after plugins have been merged.

### MergeMapper JSON
zMerge-produced mapping files that MergeMapper must be able to locate alongside the merge setup.

### Merge discovery
Startup scan finding actual zMerge metadata. MergeMapper intentionally disables itself when no merges exist.

### No-merges state
Normal state where MergeMapper reports no merges and shuts down to avoid unnecessary memory/work. This is not a failure if user does not use zMerge.

### Original FormID lookup
Consumer supplies source mod name + old FormID.

### Mapped FormID
MergeMapper resolves to new merged module/form identity.

### Papyrus support
MergeMapper lets Papyrus consumers use merge-aware form lookup rather than hardcoded original identities.

### Native API support
Other SKSE DLLs can integrate with MergeMapper to remap IDs internally.

### Optional dependency
Frameworks such as SPID/other distributors can use MergeMapper for merged setups but normally function without it when no merges are present.

### MergeMapper warning
Another framework may log that MergeMapper dispatch failed/was unavailable. Determine whether user actually has merges before treating it as actionable.

### Dummy-merge anti-pattern
Forcing MergeMapper to remain active with an empty merge when no real merged plugin exists wastes resources and is not required according to the framework author.

### MergeMapper 1.6.x
2026 release line with updated CommonLib/address-library handling and fixes for ambiguous merge wildcards/log-only merged plugin names.

## Merge-aware frameworks

### SPID merge awareness
Runtime distributor can map configs referring to original plugin identities when merge support/API is available.

### KID merge awareness
Keyword distribution configs may require current framework/version-specific support for merged identities.

### OAR merge awareness
Modern OAR can resolve merge-mapped identities used by conditions/configs where current support applies.

### MCM Helper merge awareness
Current MCM Helper includes MergeMapper support so settings/forms tied to merged plugins can resolve correctly.

### SRD merge awareness
Sound Record Distributor supports MergeMapper, but current documentation warns not to merge the plugin that owns/config-associates an SRD config because config discovery itself is tied to plugin identity.

### Merge-aware vs merge-safe
A framework can remap form references while other parts of a mod (BSA naming, localized strings, script GetFormFromFile, plugin-tied config discovery) still make the mod unsafe to merge.

## Native EditorID Fix

### Native EditorID Fix / NEIF
SKSE plugin restoring/extending EditorID lookup at runtime and adding safer engine string-formatting behavior.

### EditorID -> form lookup
Resolve loaded forms by bare EditorID in engine paths that would not normally preserve/offer full EditorID access.

### form -> EditorID lookup
Retrieve an EditorID string from a loaded form at runtime.

### Reference EditorID lookup
Current VR port documentation explicitly supports EditorIDs for placed references/actors as well as base forms.

### Bare EditorID resolution
Console/runtime config can refer to forms by EditorID without plugin-local numeric ID where lookup is enabled.

### Console help integration
Help searches names/EditorIDs according to plugin behavior.

### NEIF API
Exported native interface used by other DLLs to query EditorID lookup state and retrieve EditorIDs.

### NEIF_GetEditorID
Public API function in current implementation lineage returning EditorID information for a form.

### EnableNativeEditorIDLookup
INI option controlling native EditorID lookup functionality.

### Node naming compatibility
Engine patches that expose EditorIDs can alter generated node-name behavior; NEIF retains compatibility mode because some mods expect empty/non-EditorID node naming.

### EditorID cache
Other frameworks such as po3 Tweaks can expose/cache EditorID-related data; integrations should declare which source they use.

### EditorID collision
EditorIDs are intended to be meaningful identifiers but are not a universally globally unique persistent database key across all mods. Context may still be required.

### EditorID stripping/loss
Skyrim runtime traditionally does not retain/expose every EditorID consistently, which is why native lookup fixes/framework caches exist.

## Runtime identity selection

Prefer, by use case:
- plugin data dependencies: FormID/master relationship;
- external config: EditorID where stable/unique **or** local FormID~plugin;
- generated patch tooling: FormKey/ModKey-style stable identity;
- merged setup: merge-aware mapping through MergeMapper where supported;
- save persistence: SKSE ResolveFormID/serialization mapping;
- native transient objects: handles/re-resolve rather than raw pointers.

### Identity provenance
Store both human-readable EditorID and stable source plugin/local FormID when possible.

### Identity drift
Plugin author renames EditorID, compacts FormIDs, merges/splits plugin or recreates form, breaking external configs even though visible object seems equivalent.

### Semantic identity
Concept that a form is "the same gameplay thing" despite technical ID migration. Tools should not infer semantic identity without evidence.

## Diagnostic rules

1. If a runtime config fails after zMerge, inspect source-to-merged identity before changing load order.
2. MergeMapper is only needed when actual merges exist; its self-disable state is expected otherwise.
3. "Supports MergeMapper" does not mean every asset/config/package aspect of the mod is safe to merge.
4. EditorID is excellent for readable configs but can be renamed/collide; preserve plugin/FormID provenance too.
5. Native EditorID Fix changes runtime lookup capability, not plugin record identity itself.
6. Distinguish origin plugin from winning override when explaining an EditorID/FormID.
7. Never persist a raw native pointer as a form identity.

## Sources

- MergeMapper current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/74689
- MergeMapper upstream: https://github.com/alandtse/MergeMapper
- Native EditorID Fix: https://www.nexusmods.com/skyrimspecialedition/mods/85260
- Native EditorID Fix VR: https://www.nexusmods.com/skyrimspecialedition/mods/179558
- Mutagen identity/load-order docs: https://github.com/Mutagen-Modding/Mutagen
- MCM Helper changelog: https://www.nexusmods.com/skyrimspecialedition/mods/53000
- Sound Record Distributor merge notes: https://www.nexusmods.com/skyrimspecialedition/mods/77815

## Dated snapshot

MergeMapper 1.6.2 was current on 2026-09-24, updated 2026-09-17. Native EditorID Fix 1.2.3 was current and updated 2026-09-21, with separate files for current 1.6.1130+/1.7.104+, older 1.6.317–1.6.659 and 1.5.x runtimes.
