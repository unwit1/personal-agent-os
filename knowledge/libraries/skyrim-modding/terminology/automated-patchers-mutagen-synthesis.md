# Skyrim Modding Terminology — Automated Patchers, Mutagen, Synthesis, Spriggit, and Data-Layer Tooling

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module covers code-generated conflict resolution and programmatic Bethesda-plugin manipulation.

## Programmatic patching

### Patcher
Tool/program that reads a load order and produces a plugin/config/output tailored to that specific setup.

### Static patch
Hand-authored compatibility plugin with predefined masters/overrides.

### Dynamic/generated patch
Patch generated from the user's current load order and rules.

### Rule-based patcher
Program applying deterministic transformation rules to matching records.

### Load-order-aware patcher
Patcher that evaluates winning overrides/conflict chains rather than only one input plugin.

### Idempotent patcher
Running it repeatedly on the same effective inputs yields an equivalent output.

### Deterministic patch
Output reproducible from the same load order/config/tool version.

### Patch pipeline
Ordered sequence of patchers where output from one stage can be consumed/augmented by later stages.

### Output plugin
ESP/ESM/ESL produced by a patcher.

### Generated master
Input plugin referenced by output records, causing the patch plugin to require it as a master.

### Master list
Plugins the generated patch depends upon.

### Master overflow
Output references too many masters for the applicable plugin-format/tool constraints.

### Patch split
Dividing generated output across multiple plugins when one plugin cannot safely represent all dependencies/content.

### Stale patch
Generated output no longer corresponds to the current load order/config after mods are added/removed/updated.

### Rerun requirement
Need to regenerate a patch after relevant inputs change.

## Mutagen

### Mutagen
.NET/C# library for reading, analyzing, creating and modifying Bethesda plugin files with strongly typed record APIs.

### Mutagen.Bethesda
Core NuGet/package namespace for Mutagen's Bethesda tooling.

### Mutagen.Bethesda.Skyrim
Typed Skyrim record model.

### GameEnvironment
Mutagen abstraction that discovers/loads game data, plugins and load-order context.

### SkyrimRelease
Mutagen enum/config indicating target Skyrim format/runtime family such as SkyrimSE.

### ModKey
Stable identifier composed from plugin filename/name and mod type used by Mutagen APIs.

### FormKey
Mutagen identifier combining a form's local ID with the originating ModKey.

### FormLink
Typed reference from one record to another through FormKey semantics.

### Resolved form
FormLink/FormKey successfully mapped to a record in the current load-order context.

### WinningOverrides()
Mutagen load-order query pattern returning final winning records for a form type.

### PriorityOrder
Load-order traversal oriented from higher-priority winners through lower-priority inputs.

### Typed record
C# interface/class exposing fields of a specific Bethesda record type.

### Getter interface
Read-only Mutagen record interface, conventionally suffixed Getter.

### Mutable record
Writable record object suitable for patch generation/modification.

### Deep copy / override into patch
Create a patch-record copy derived from an input/winner so fields can be changed and written to output.

### LinkCache
Mutagen lookup/cache facility for resolving form links efficiently.

### LoadOrder
Mutagen model of ordered plugin listings and metadata.

### Record context
Information tying a resolved record to its source mod, override chain and load-order environment.

### Binary overlay
Performance mechanism allowing Mutagen to read fields over plugin binary data with minimal up-front object creation.

### Strong typing
Compile-time APIs expose record-specific fields rather than arbitrary raw subrecords.

## Synthesis

### Synthesis
GUI/framework for running collections of code-based patchers, commonly built on Mutagen, and funneling their results into generated plugin output.

### Synthesis patcher
Program conforming to Synthesis pipeline interfaces and operating on game/load-order state.

### Patcher pipeline
Ordered set of Synthesis patchers executed for one profile/environment.

### Patcher group
Organizational/output grouping of Synthesis patchers.

### Synthesis profile
Saved patcher collection/configuration/environment setup.

### Patcher repository
Git repository containing source/build definition for a Synthesis patcher.

### Git patcher
Synthesis mode retrieving/building patcher code from a Git source/revision.

### NuGet patcher
Patcher/package distributed through .NET package tooling where supported.

### Local patcher
Patcher executed from local source/build configuration.

### Settings
Patcher-specific user configuration serialized by Synthesis.

### Pipeline output
Generated patch plugin(s) after ordered patchers finish.

### SourcePath
Synthesis command-line concept allowing a patcher/output to build on a previous result.

### OutputPath
Target plugin path for generated patch output.

### Post-run processing
Host stage after patcher execution that may validate, split, write or modify output according to Synthesis/framework options.

### Split files if max masters exceeded
Synthesis feature intended to handle output requiring more masters than one plugin can safely contain.

### Patcher version pinning
Locking to a specific Git revision/release/package so results do not silently change when upstream code updates.

### Patcher regression
New patcher/framework version produces different/broken output on the same intended inputs.

## Spriggit

### Spriggit
Mutagen ecosystem tool converting Bethesda plugin data to/from text-based representations suitable for version control.

### Plugin-to-text
Serialize plugin records into deterministic structured text/YAML/JSON-like representation depending on Spriggit configuration.

### Text-to-plugin
Rebuild binary Bethesda plugin from supported text representation.

### Git-friendly plugin representation
Human-diffable/mergeable serialized record data used instead of committing only opaque binary ESP/ESM files.

### Serialization version
Spriggit data/schema version that must be considered when reading older exported repositories.

### Round trip
Convert plugin to text then rebuild and verify semantic equivalence.

### Semantic diff
Compare meaningful record/field changes rather than only binary-byte differences.

## xEdit scripting

### xEdit script
Pascal-like script executed by xEdit to automate record scanning, transformation, validation or patch creation.

### Apply Script
xEdit command running a script against selected records/plugins.

### IInterface
xEdit scripting object abstraction used to represent plugin elements/records/subrecords.

### ElementByPath
Common xEdit scripting method for accessing nested fields by path.

### WinningOverride
xEdit scripting concept/function for retrieving the final override of a record.

### MasterOrSelf
Pattern used to navigate to a source/master version of a record.

### AddRequiredElementMasters
xEdit scripting helper pattern for ensuring output patch masters are added for referenced records.

### Copy as override
Create patch override of an existing record in another plugin.

### Copy as new record
Duplicate data with a new identity rather than overriding the same FormID.

### Renumber FormIDs
Identity-changing operation that must be treated as a migration.

## zEdit / zMerge lineage

### zEdit
Bethesda plugin editing/patcher host/tooling ecosystem by Mator, historically supporting modular patchers.

### zPatch
Generated patch produced by zEdit patcher framework.

### zMerge
Tool/workflow for merging plugin content to reduce plugin count or package related data.

### Merge
Combine multiple plugins into another plugin while attempting to preserve references/assets/metadata. Merging is not equivalent to ESL-flagging.

### Merge mapping
Metadata mapping old plugin/FormIDs to merged identities so dependent assets/scripts/tools can be adjusted where supported.

### Merge prerequisite
Plugins being merged should be compatible with merge tooling constraints; scripts/FaceGen/MCM/native configs/external references can complicate merging.

## Automated patching design rules

1. Generated patches are derived artifacts; preserve the patcher config/version and regenerate after relevant input changes.
2. Do not hand-edit generated output unless the workflow explicitly supports preserving those edits.
3. Pin patcher revisions for reproducible modlists.
4. Verify master counts and unresolved references after large generated patches.
5. A strongly typed library can still encode incorrect patch semantics; type safety is not gameplay-intent validation.
6. Use winning-override/context APIs rather than scanning isolated plugins when a patch intends to reconcile a full load order.
7. Treat plugin identity/FormKey changes as consequential.
8. Include generated patch output as its own mod-manager layer with known priority.
9. For failures, save patcher logs, exact load order, settings and tool/framework versions.
10. Prefer round-trip/semantic validation when introducing text-based plugin version-control workflows.

## Sources

- Mutagen: https://github.com/Mutagen-Modding/Mutagen
- Synthesis: https://github.com/Mutagen-Modding/Synthesis
- Spriggit: https://github.com/Mutagen-Modding/Spriggit
- Mutagen Bootcamp examples: https://github.com/Mutagen-Modding/MutagenBootcamp
- Tome of xEdit scripting/documentation: https://tes5edit.github.io/docs/
