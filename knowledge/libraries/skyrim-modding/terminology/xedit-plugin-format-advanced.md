# Skyrim Modding Terminology — Advanced Plugin Structure, xEdit Analysis, and Record Identity

Imported: 2026-09-24
Status: sourced encyclopedia pass 4

This module deepens the plugin-format and xEdit layer. It focuses on record identity, group structure, master relationships, flags, error checking, and the difference between binary structure and semantic intent.

## Plugin containers and headers

### TES4 header
Top-level plugin header record used by Skyrim ESP/ESM/ESL files. It stores file metadata such as flags, author/description fields, master references and related header information.

### File header flags
Bit flags in the TES4 header that influence how the engine treats a plugin, including master/ESM and light/ESL behavior where applicable.

### ESM flag
Header state causing a plugin to be treated as a master. Filename extension and header state interact, but the extension alone is not the complete model.

### ESL flag
Header state enabling light-plugin FormID mapping when the file satisfies the applicable compact-ID constraints.

### Localized flag
Header state indicating relevant strings are looked up through external STRINGS/DLSTRINGS/ILSTRINGS files.

### Master list / MAST
Ordered list of parent plugins referenced by the file.

### Master dependency
A plugin becomes a master when records in the child file refer to forms originating in it, or when explicitly required by the format/tooling.

### Master ordering
Order of masters in the plugin header is significant for resolving on-disk FormID indices.

### Header Form Version
Plugin/header format version indicating the record serialization generation used by the producing editor/game. It is distinct from Skyrim runtime marketing labels.

### Next Object ID
Header field used when allocating new local object IDs. Tooling may repair/update it as records are added/renumbered.

## GRUP and binary organization

### GRUP
Plugin binary container grouping records by top-level type or nested spatial/relationship organization.

### Top-level GRUP
Group containing records of one signature/type.

### World children group
Nested group containing records associated with a WRLD worldspace.

### Cell children group
Nested group containing reference/navigation/etc. records associated with a CELL.

### Persistent children group
Cell child group for references stored as persistent.

### Temporary children group
Cell child group for ordinary temporary references.

### Visible-distant children
Historical/group terminology for cell child organization relevant to distant/reference data in Bethesda formats.

### Record
Binary unit beginning with a record header/signature and containing typed subrecords.

### Subrecord
Named data field/chunk within a record, generally identified by a short signature.

### Record size
Serialized byte size of a record payload.

### Compressed record
Record whose payload is compressed in the plugin and expanded by tools/runtime before interpreting subrecords.

### XXXX extended-size subrecord
Bethesda-format mechanism allowing a following subrecord to carry data larger than a normal 16-bit subrecord size.

### Unknown subrecord
Binary field that a tool does not fully identify. Preserve unknown data unless a format-aware tool explicitly handles it.

## Record identity

### FormID
32-bit loaded identity whose high-order mapping portion depends on the originating plugin/load mapping and whose local object portion identifies the form within its origin.

### Local FormID / ObjectID
Plugin-local portion of a record identity before load-order mapping.

### Originating plugin
Plugin in which the form was first created. Overrides retain that original form identity rather than becoming new local records of each overriding plugin.

### Override identity
Later record with the same underlying FormID as an existing form, signaling “modify this form” rather than “create a new form.”

### New record
Record whose FormID originates in the current plugin.

### Injected record
Advanced technique creating a record using an ID in another master namespace so multiple mods can share a stable identity without one owning a conventional new record in the usual manner. Injection must be deliberately designed and validated.

### Light FormID
Loaded FormID mapped through FE/light-index space for ESL-flagged plugins.

### Compact FormID
Local object ID moved into the range usable by a light plugin.

### FormID renumbering
Changing local identities of new records. This can break dependent plugins, scripts/configs, generated assets, FaceGen, save state and external references.

### EditorID / EDID
Human-readable identifier on many form types. Useful for tooling and runtime lookup, but it is not the stable binary identity of the record.

### EditorID collision
Different records sharing the same EditorID. Tools/frameworks resolving by EDID may become ambiguous depending on lookup implementation.

### FormKey
Mutagen-style canonical combination of originating plugin key plus local form ID.

## Record flags and specialized behavior

### Deleted flag
Record/reference marked deleted by an override.

### Initially Disabled flag
Placed-reference state causing the reference to begin disabled.

### Persistent flag
Placed-reference state/grouping indicating durable addressability beyond ordinary cell lifecycle.

### Is Full LOD / Neverfade
Reference flag causing full/distant behavior outside ordinary active cells; interacts with large-reference/LOD systems.

### Partial Form flag
Modern Skyrim record flag used by supported record types so an override can intentionally provide only part of a record instead of behaving like a conventional full data replacement. Treat as a specialized engine feature, not a universal merge flag.

### Quest item / Persistent Reference flag overlap
Bethesda record flags can reuse bit positions with different semantic labels by record type. Interpret flags through record-specific schemas rather than globally by numeric bit.

### Ignored flag
Record flag used by some engine/tool contexts. Meaning is record/game-specific and should not be generalized without schema evidence.

## ONAM and overridden-record metadata

### ONAM
TES4-header metadata listing overridden forms for master files in applicable Bethesda plugin formats.

### Overridden Forms list
xEdit-visible/header metadata associated with masters. It is not a substitute for scanning the actual record tree.

### ONAM update
Tool/editor operation rebuilding overridden-form metadata after changes where required by the target game/file type.

### ONAM diagnostic rule
Do not manually fabricate ONAM data. Let format-aware current tooling manage it when needed.

## xEdit analysis

### Background Loader
xEdit subsystem that loads selected modules and builds record/reference context before editing.

### Reference information
xEdit's indexed knowledge of which records refer to other records, enabling “Referenced By” style navigation and safe master/reference analysis.

### Referenced By
xEdit view showing other records that contain a reference to the selected form.

### View tab
xEdit pane comparing override-chain field values across loaded plugins.

### Record tree
Left-side hierarchy of plugins, groups and records.

### Conflict color
xEdit visual classification describing whether values differ/override/conflict. Color is diagnostic metadata, not a verdict about compatibility.

### Filter for Conflicts
xEdit operation narrowing displayed records to relevant override/conflict classes.

### Very Quick Show Conflicts
Faster xEdit conflict-oriented startup/view path for a configured plugin selection.

### Check for Errors
xEdit validation scanning selected records for malformed/unresolved/invalid references and format-specific issues.

### Error
Tool-detected structural or reference problem. Not every gameplay incompatibility is detectable as an xEdit error.

### Unresolved FormID
Reference field points to an identity not resolvable in the active master/load set.

### Unexpected subrecord
Record contains data inconsistent with the schema/tool expectations for that record/version.

### Remove Identical to Master
Cleaning operation deleting selected accidental ITM overrides.

### Undelete and Disable References
Cleaning operation converting unsafe hard-deleted placed refs into a safer disabled state where supported.

### Build Reference Info
xEdit operation/index phase collecting cross-record links.

### Compare to
xEdit comparison workflow examining plugin/record differences beyond simple load-order conflict display.

### Apply Filter
General xEdit filtering framework used for conflict/error/record searches.

### Apply Script
Execute an xEdit Pascal script over selected plugin/record context.

### Change FormID
Explicit identity-changing operation; high risk when dependencies already exist.

### Clean Masters
Remove masters no longer actually referenced by the plugin after editing.

### Sort Masters
Normalize/order master list and remap on-disk indices as needed through xEdit-aware processing.

### Add Masters
Add parent plugin dependencies before copying/creating references into a patch.

### Copy as override into
Create an override of the same form in a destination plugin.

### Copy as new record into
Duplicate data as a new form with a new identity in the destination plugin.

### Deep copy
Copy a record plus selected referenced child/dependent data into new identities; semantics depend on tool/script and record family.

## Cleaning and intent

### Dirty edit
Accidental/unnecessary edit introduced by editor workflow or author mistake.

### Intentional ITM
Identical override deliberately included to block another mod's change. It is structurally an ITM but semantically intentional.

### Wild edit
Unintended edit to unrelated data, often caused by accidental selection/CK behavior.

### Cleaning report
Tool output identifying removable ITMs, deleted refs and related issues.

### Mod-specific cleaning instruction
Known instruction from LOOT/mod author/tool maintainers that a particular version should or should not be cleaned.

### “Clean everything” anti-pattern
Running cleanup indiscriminately without respecting intentional edits or official guidance.

## Advanced compatibility rules encoded for Agent OS

1. Record identity is defined by origin/FormID, not EditorID or display name.
2. Copy-as-override and copy-as-new are fundamentally different operations.
3. Renumbering/compaction is an identity migration and requires downstream dependency analysis.
4. Unknown binary fields should be preserved rather than normalized away by ad-hoc tooling.
5. xEdit structural errors and gameplay conflicts are different evidence classes.
6. Conflict coloring requires semantic interpretation of the affected fields.
7. Header/master changes should be performed by format-aware tools so indices and references are remapped consistently.
8. Do not treat the same numeric record-flag bit as the same semantic flag across all record types.
9. Partial-form behavior is specialized; ordinary Skyrim overrides remain field/record winner semantics unless the format/record explicitly supports otherwise.
10. Before automated plugin surgery, snapshot the plugin hash, masters, FormIDs and dependent plugins so identity changes can be audited.

## Sources

- Tome of xEdit documentation: https://tes5edit.github.io/docs/
- xEdit What's New: https://tes5edit.github.io/docs/18-whatsnew.html
- Tome of xEdit conflict methodology: https://tes5edit.github.io/docs/5-conflict-detection-and-resolution.html
- Tome of xEdit The Method: https://tes5edit.github.io/docs/6-themethod.html
- xEdit source: https://github.com/TES5Edit/TES5Edit
- Mutagen plugin model: https://github.com/Mutagen-Modding/Mutagen
