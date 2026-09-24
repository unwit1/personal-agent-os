# Skyrim Modding Terminology — Mod Managers, Deployment, Wabbajack, Mutagen, and Synthesis

Imported: 2026-09-24
Status: sourced deep-ingestion pass 3

## Mod management models

### Mod manager
Tool that installs, enables, disables, orders, deploys, and tracks mods/assets/plugins.

### Mod staging directory
Manager-controlled storage containing installed mod files before/independent of their effective game-data presentation.

### Deployment
Making managed files visible to the game through physical files, links, or virtualization.

### Virtualization
Presenting a merged/overlaid filesystem view to selected processes without copying every enabled mod into the physical Data directory.

### USVFS
Mod Organizer 2 User Space Virtual File System. It uses API hooking to make process-local virtual file/directory links and overlay multiple sources onto one destination.

### Process-local VFS
Filesystem changes visible to selected launched processes rather than globally to Windows.

### Virtual overwrite
When multiple MO2 mods expose the same path, priority determines which file appears in the effective virtual filesystem.

### Mod priority
MO2 ordering controlling file/asset overwrite winners. This is not plugin load order.

### Left pane
Common MO2 shorthand for mod/asset priority order.

### Right pane
Common MO2 shorthand for plugin/load-order view.

### Overwrite
MO2 special destination for generated files that are not routed into a named mod.

### Profile
Mod-manager configuration grouping enabled mods/plugins/INI/save settings according to manager capabilities.

### Portable instance
MO2 installation mode where instance configuration/data are kept with the MO2 installation rather than in shared application-data locations.

### Global instance
MO2 instance managed outside a fully self-contained portable folder.

### Executable/tool entry
Configured program launched through MO2 so it receives the virtual filesystem view.

### VFS injection
Process of intercepting filesystem APIs in a launched process so USVFS paths become visible.

### VFS blind spot
Tool/subprocess not launched/injected in the expected way and therefore not seeing the same virtualized files.

## Vortex

### Vortex
Nexus Mods' mod manager. Uses a staging/deployment model rather than MO2's process-local USVFS model.

### Hardlink deployment
Vortex default Skyrim deployment model where files in game directories are hard links to files in the staging area. They appear as normal files without duplicating file data on the same filesystem.

### Hard link
Filesystem directory entry pointing to the same underlying file data as another path. Editing either hard-linked path changes the same underlying file.

### Purge
Vortex operation removing deployed links/files from the game location while retaining managed/staged mod data.

### Deploy
Vortex operation recreating effective game-folder files according to enabled mods and conflict rules.

### File conflict rule
Vortex rule controlling which mod wins when multiple mods supply the same asset path.

### Before/after rule
Vortex relationship describing conflict/deployment precedence between mods or plugins depending on context.

### Move deployment
Alternative/experimental Vortex deployment mode that physically moves managed files instead of using default hardlinks.

### Staging folder
Vortex managed mod storage location from which deployment occurs.

### Deployment method constraint
Hardlink deployment generally requires staging and game locations compatible with same-filesystem hardlink semantics; other deployment methods have different constraints.

## FOMOD and installers

### FOMOD
XML-driven mod installer format commonly used to present options, dependencies, and conditional file installation.

### ModuleConfig.xml
Core FOMOD installer configuration file defining pages/options/files/conditions.

### Installer option
Selectable component affecting which files or configurations are installed.

### Conditional install
Installer behavior that selects files based on plugin presence, game version, user choices, or other supported conditions.

### BAIN
Archive/install structure convention historically associated with Wrye Bash, using subpackages/directories for selectable components.

### Manual install
Directly copying files into game directories without a manager's provenance/conflict tracking. Harder to reverse/audit reliably.

## Wabbajack

### Wabbajack
Automated modlist installer capable of reproducing an entire modding setup on another machine without bundling/re-distributing the source mods themselves.

### Modlist
Curated installation specification defining archives, transformations, installed outputs, manager configuration, generated files, and instructions.

### .wabbajack file
Compiled Wabbajack modlist installation file/specification used by the installer.

### Compilation
Wabbajack list-author process that analyzes the configured installation and produces installation instructions/hash-based archive relationships rather than redistributing original mod assets.

### Installation location
Destination containing the installed list environment. Wabbajack documentation requires it to be separate from the game location and from other list installs.

### Download location
Archive cache holding downloaded source mod files. Can often be reused to avoid re-downloading unchanged archives.

### Archive
Original downloadable mod/package input used to reconstruct an installation.

### Archive hash
Content identity used to ensure the expected archive/file version is available.

### Binary patch
Transformation allowing Wabbajack to reconstruct a target file from permitted source material rather than distribute the target wholesale.

### Modlist-specific README
Author-provided installation/run instructions that remain authoritative for list-specific prerequisites and post-install steps.

### Stock Game / game-root copy
List design pattern using a controlled copy or equivalent isolated game-root setup so the modlist can pin/contain game-root assets independent of the user's ordinary installation. Exact mechanism is list/tool-version-specific.

### Root Builder
MO2 extension/pattern used by some modlists to manage files that need to appear in the game root rather than Data.

## Mutagen

### Mutagen
.NET library/ecosystem for reading, querying, creating, and modifying Bethesda plugin records programmatically.

### ModKey
Mutagen identity object representing a plugin/module filename/key.

### FormKey
Stable combination of originating ModKey and form-local ID used to identify a record independently of current numeric load-order index.

### LoadOrder<T>
Mutagen ordered load-order abstraction. Later entries win when resolving ordinary override chains.

### WinningOverrides()
Mutagen query concept returning the effective winning records for a load order.

### LinkCache
Mutagen structure used to resolve FormLinks/FormKeys to records efficiently in the current load-order context.

### FormLink
Typed/untyped reference to another form identified through a stable FormKey-style relationship.

### Getter
Read-only Mutagen interface exposing record data without mutable copy semantics.

### Override copy
Mutable record created in a patch mod based on an existing winning record.

### Patch mod
Programmatically generated plugin containing selected overrides/new records.

## Synthesis

### Synthesis
Patcher pipeline framework/GUI designed to run one or many code-based patchers against the user's current load order and funnel their results into generated plugin output.

### Patcher
Program/code unit that reads the load order and writes calculated changes into a patch.

### Patcher pipeline
Ordered collection of patchers executed together.

### Synthesis.esp
Common default output plugin used by Synthesis pipelines.

### Rerun requirement
Synthesis documentation recommends rerunning the pipeline when mods are added/removed so generated output reflects the current load order.

### IPatcherState
Synthesis/Mutagen developer state exposing current load order, output patch mod, settings and environment.

### state.LoadOrder
Current input load-order view used by a patcher.

### state.PatchMod
Mutable output plugin written by a patcher.

### Git patcher
Synthesis patcher obtained/built from a source repository, enabling versioned code-based patching.

### Local patcher
Patcher developed/run from a local project/environment.

### External patcher
Synthesis can orchestrate patchers outside Mutagen as external executables, though Mutagen-based patchers are strongly facilitated.

## Generated-output management

### Generated mod
Named mod directory used to hold outputs from BodySlide, Nemesis/Pandora, DynDOLOD, Synthesis, xEdit scripts, etc.

### Reproducible generated output
Output that can be regenerated from pinned inputs/config/version state.

### Stale output
Generated files no longer matching the installed mod set or tool configuration.

### Output provenance
Record of tool/version/input/config used to create generated artifacts.

### Build order
Sequence in which generators/patchers are run when one generated output depends on another.

### Regeneration trigger
Change such as adding/removing/updating a mod that invalidates a generated patch/LOD/behavior/build and requires rerunning the relevant tool.

## Diagnostic rules

1. Ask which mod manager and deployment model is used before giving file-location advice.
2. MO2 mod priority and plugin load order are different; Vortex deployment conflicts and plugin sorting are also separate.
3. A tool must see the same effective files as the game. With MO2, launch context/VFS injection can matter.
4. With Vortex hardlinks, a deployed file is not an independent copy; edits can affect staging-linked content.
5. Generated outputs should live in named managed mods when possible so provenance/conflicts are visible.
6. Wabbajack lists are reproducibility systems, not simple zip archives.
7. Mutagen/Synthesis patch output must be regenerated when relevant load-order inputs change.
8. Automated patchers encode a defined transformation; they do not semantically solve every conflict outside their scope.

## Sources

- MO2 upstream: https://github.com/ModOrganizer2/modorganizer
- USVFS upstream: https://github.com/ModOrganizer2/usvfs
- Vortex Skyrim fundamentals: https://www.nexusmods.com/skyrimspecialedition/articles/11685
- Wabbajack upstream: https://github.com/wabbajack-tools/wabbajack
- Wabbajack wiki: https://github.com/wabbajack-tools/wabbajack/wiki
- Mutagen upstream: https://github.com/Mutagen-Modding/Mutagen
- Mutagen load-order documentation: https://github.com/Mutagen-Modding/Mutagen/blob/dev/docs/loadorder/index.md
- Synthesis upstream: https://github.com/Mutagen-Modding/Synthesis
- Synthesis documentation: https://mutagen-modding.github.io/Synthesis/
