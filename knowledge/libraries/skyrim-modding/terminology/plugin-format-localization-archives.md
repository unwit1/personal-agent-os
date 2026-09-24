# Skyrim Modding Terminology — Plugin Format, Localization, and Archives

Imported: 2026-09-24
Status: sourced deep-ingestion pass 5

This module covers low-level plugin/resource concepts that become important when troubleshooting localization, masters, record loading, BSA behavior, and porting.

## Plugin file structure

### TES4 header record
The top-level header record of a Bethesda plugin. Despite the name, TES4 is the header signature used by Skyrim plugin files. It carries plugin metadata and subrecords such as header/version information and master declarations.

### HEDR
TES4-header subrecord containing plugin header metadata including file/version-related values and record-count information as represented by tooling.

### MAST
TES4-header subrecord naming a parent master required by the plugin.

### DATA after MAST
Header data associated with a master entry. Tools preserve the MAST/DATA relationship even when some fields are not materially used by Skyrim.

### Master list
Ordered set of MAST dependencies recorded in the TES4 header. FormIDs referencing other plugins are interpreted relative to this dependency/load context.

### Record header
Binary header preceding a plugin record. It identifies the record signature, data size, flags, FormID and other format-level metadata.

### Subrecord
Typed field inside a record, usually identified by a short signature. Record schemas are combinations of subrecords whose meaning depends on the parent record type.

### Record compression flag
Record-header flag indicating that the record payload is compressed. Compression is a property of an individual record payload, not of every subrecord.

### Compressed record
Record whose data payload is zlib-compressed in the plugin file and decompressed by the engine/tool when read.

### Record flags
Bitfield in a record header encoding states such as Deleted, Initially Disabled, Persistent, ESM/Localized-related header flags where appropriate, compression, and many record-type-specific meanings.

### Form version
Version field associated with record serialization/layout in newer Bethesda plugin formats. Skyrim LE and Skyrim SE data commonly expose different form-version values for records altered/resaved by the newer CK, but form version alone is not a reliable proof that every asset or behavior has been correctly ported.

### Form 43
Community shorthand for Skyrim LE-era plugin records commonly retaining form version 43.

### Form 44
Community shorthand for records resaved by Skyrim Special Edition's Creation Kit and commonly carrying form version 44.

### Form 43 warning
CK/tool warning or community concern about loading an LE-era plugin in SE. Do not equate the number alone with a guaranteed crash: actual compatibility also depends on record contents, assets, scripts, navmesh, DLLs and other runtime differences.

### Resave in CK
Opening a plugin in the target game's Creation Kit and saving it so the editor rewrites supported record structures/header data for that CK generation.

### Mass form-version conversion
Bulk-resaving/converting plugins only to change form version. This is not automatically beneficial; current xEdit/community tooling cautions that blindly converting every Form 43 plugin is unnecessary and can create unintended changes.

### ONAM
TES4-header subrecord listing overridden temporary CELL-child records for master/ESM behavior. xEdit documents ONAM as required for ESM-flagged files so the engine can load relevant temporary records on demand.

### ONAMUpdate mode
xEdit mode that can generate ONAM for non-ESM files for special SSE Engine Fixes workflows that treat all plugins like masters. xEdit explicitly notes there is no reason to use this mode without that Engine Fixes feature.

### ESM flag
Header flag making the engine treat a module as a master. It affects load grouping and record-loading behavior beyond the filename extension.

### ESL flag
Header flag enabling light-plugin FormID mapping. It does not simply mean “small ESP” or “loads last.”

### Localized flag
TES4-header flag indicating localized string fields are externalized into language-specific string tables rather than stored directly as embedded strings.

## Localization

### Localized plugin
Plugin whose Localized flag is set and whose localizable text fields reference external string IDs.

### Embedded string
Text stored directly in the plugin record rather than looked up through an external string table.

### LString
Plugin-field concept representing a localizable string. Depending on the Localized flag, tooling interprets it as either inline text or a string-table ID.

### String ID
Numeric identifier stored in a localized plugin field and resolved through an external language string table.

### STRINGS
External table primarily containing general/display strings such as names and text fields represented as ordinary localized strings.

### DLSTRINGS
External table format used for dialogue-oriented localized strings and other length-prefixed localized entries.

### ILSTRINGS
External table format used for additional localized/UI-like strings represented with its length-prefixed table format.

### Language suffix
Filename component such as `_English` selecting the language table associated with a localized plugin.

### Localization context
xEdit/tool setting controlling which language's external tables are loaded/displayed for localized plugins.

### Missing string
Plugin references a string ID that is absent from the active language table. Symptoms can include blank text, lookup placeholders, missing dialogue/UI labels or tool warnings.

### Mismatched string table
External strings belong to a different plugin build/version than the ESP/ESM/ESL currently installed, so IDs resolve to wrong/missing text.

### Translation
Creating equivalent localized string tables for another language while retaining the plugin's string IDs/record relationships.

### Codepage
Character encoding interpretation used by tooling for localized/translatable strings in legacy contexts. xEdit exposes language/codepage controls and overrides.

### Localization packaging
Shipping every required language table with exactly the filenames/path expected by the plugin. Localized ESP without its string tables is incomplete.

## Archives and resources

### BSA
Bethesda Softworks Archive used by Skyrim to package assets such as meshes, textures, scripts, interface files, sounds and voice data.

### Archive member
Individual file stored inside a BSA using a virtual game-data path.

### BSA packing
Creating an archive from a Data-like directory tree.

### BSA extraction
Unpacking archive members to loose files for inspection/editing.

### Archive name association
Vanilla Skyrim automatically associates/load-selects BSAs according to recognized archive/plugin naming conventions and configured archive lists. A correctly packed archive with an unrecognized load relationship may simply never be mounted.

### Plugin-associated archive
BSA whose recognized basename/prefix corresponds to an active plugin so the engine automatically loads it.

### Main archive
Archive conventionally named after a plugin/module basename.

### Textures archive
Recognized texture archive naming variant associated with a plugin in Skyrim SE conventions.

### Archive prefix extension
Native framework can expand recognized plugin-associated BSA suffixes beyond vanilla defaults. This is a runtime extension, not a vanilla packaging assumption.

### Loose file
Asset existing as an ordinary Data-path file instead of inside a BSA.

### Loose-over-archive conflict
When an effective loose file and archive member have the same virtual path, loose/archive resolution rules and manager deployment determine which asset is used. Diagnose the effective filesystem, not merely archive contents.

### Archive conflict
Two loaded BSAs contain the same virtual asset path. Effective winner depends on archive/plugin loading order and any loose-file override.

### Resource path
Game-relative path such as `meshes\...`, `textures\...`, `scripts\...`, `sound\voice\...` used to identify an asset regardless of whether it is loose or archived.

### Archive format version
BSA internal format/settings appropriate to a particular Bethesda game/runtime generation. An archive packed for the wrong game can fail to mount or read correctly.

### Archive size constraint
Practical/format/tool limit requiring large asset sets to be split into multiple archives in some Skyrim workflows. Validate against current tooling/runtime rather than assuming arbitrary giant archives are safe.

### Archive compression
Per-file/archive compression choice that reduces disk size at the cost of decompression work. Already-compressed media may gain little.

### Archive invalidation
Historical Bethesda modding term for making loose/replacement resources override vanilla archives. Modern Skyrim mod managers/settings usually manage equivalent resource behavior without the older Oblivion-era procedure.

### Resource provenance
For every effective asset, record whether it came from loose files, which BSA, which installed mod and which manager priority. This is critical when record data looks correct but the wrong physical asset is used.

## Archive/plugin diagnostic rules

1. Separate **plugin load order** from **archive/asset precedence**.
2. Verify the BSA is actually mounted before debugging its contents.
3. A localized plugin is incomplete without the matching active-language string tables.
4. Do not “fix” missing text by clearing the Localized flag unless you intentionally rebuild inline strings.
5. ONAM is an engine record-loading concern, not generic metadata decoration.
6. Do not bulk-resave plugins solely because a scanner reports Form 43; first determine whether target-runtime record conversion is actually needed.
7. Porting a plugin does not port its NIF/HKX/DDS/native DLL assets.
8. Archive packing must preserve exact Data-relative paths.
9. When an asset seems ignored, inspect effective virtual/deployed paths and loose-vs-BSA conflicts before editing the ESP.

## Sources

- xEdit What's New — ONAM and localization behavior: https://tes5edit.github.io/whatsnew.html
- BethesdaLibrary plugin-format documentation: https://github.com/BadDogSkyrim/BethesdaLibrary/blob/main/docs/file-formats/plugins.md
- Creation Kit Wiki File Menu / archive packaging: https://ck.uesp.net/wiki/File_menu
- Cathedral Assets Optimizer upstream: https://github.com/Guekka/cathedral-assets-optimizer
- Archive Name Extender current documentation: https://www.nexusmods.com/skyrimspecialedition/mods/171480

## Provenance notes

Bethesda has not published a complete modern binary plugin-format specification. Low-level layout descriptions are therefore partly tool/reverse-engineering knowledge. xEdit behavior is preferred evidence for practical plugin semantics; third-party binary-format libraries should be corroborated before Agent OS performs automated binary mutation.
