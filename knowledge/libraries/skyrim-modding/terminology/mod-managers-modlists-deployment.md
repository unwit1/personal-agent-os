# Skyrim Modding Terminology — Mod Managers, Deployment, Profiles, and Modlists

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module distinguishes installed-mod organization, deployed game files, virtual filesystems, plugin load order, generated outputs, and reproducible modlist tooling.

## General mod-management concepts

### Mod manager
Software that tracks mod packages, installed files, conflicts, profiles, enabled/disabled state, and often plugin load order.

### Download archive
Original ZIP/7z/RAR or other package downloaded from a mod host. Keeping the archive is distinct from keeping an installed mod directory.

### Installed mod
Manager-controlled representation of extracted files and metadata. It may not be physically located in the game's Data folder.

### Mod root
Top directory treated by the mod manager as the package's effective Data-relative content root.

### Data directory
The game's conventional asset/plugin root. Modern managers may expose files virtually or deploy links rather than copying everything permanently.

### File conflict
Two installed mods provide the same effective relative path.

### Conflict winner
The file version that is visible to the game after manager priority/deployment rules.

### Conflict loser
An installed file hidden/replaced by another file at the same effective path.

### Mod priority
Manager-specific ordering used to resolve asset/file conflicts. This is separate from plugin load order.

### Plugin load order
Order in which ESP/ESM/ESL plugins are loaded. It resolves record overrides, not arbitrary mesh/texture/script file conflicts.

### Generated output
Files produced by external tools such as BodySlide, Pandora, Nemesis, DynDOLOD, xLODGen, Synthesis, or Creation Kit. Generated output should be treated as a managed mod layer with provenance.

### Tool working directory
Current/process path used by an external tool. Incorrect working directories can make tools read or write outside the intended virtualized environment.

### Root-game file
File that belongs beside SkyrimSE.exe rather than under Data, such as some preloaders, DLL proxies, ENB files, or launcher/runtime components.

### Data-root file
File that belongs under Data or a subdirectory exposed as Data-relative content.

### Profile
Saved mod-manager configuration representing enabled mods and often associated INI/plugin/save state.

### Profile-local INI
Game configuration file isolated per mod-manager profile rather than shared globally.

### Profile-local saves
Save-game isolation option where a profile uses a dedicated save set.

### Portable instance
Mod-manager installation/configuration intended to keep settings, mods, profiles, and metadata alongside a self-contained manager instance.

### Global instance
Manager configuration where application data and managed game instances are stored in shared user/system locations.

### Staging directory
Manager-controlled directory where installed mod files are stored before or independent of deployment into the game's effective filesystem.

### Purge
Manager operation that removes deployed links/files from the game while retaining the manager's installed-mod state.

### Deploy
Manager operation that makes managed mod files visible at the game's expected filesystem paths.

### Redeploy
Recalculate/reapply deployed file state after mod changes.

## Mod Organizer 2

### MO2
**Expansion:** Mod Organizer 2.  
Mod manager using USVFS to present an overlay filesystem to launched processes.

### USVFS
MO2 virtual filesystem layer that combines source directories into a process-visible view without requiring the entire mod set to be physically copied into Data.

### Virtual Data directory
Effective filesystem view seen by a process launched through MO2.

### Left pane
MO2's installed-mod/file-priority ordering surface. It primarily controls which files win when multiple mods provide the same path.

### Right pane
MO2 surface containing plugin load order and related game/plugin tabs. It does not mirror the left-pane meaning.

### Overwrite
MO2 directory that collects files written by virtualized processes when they are not redirected into a named mod.

### Create mod from Overwrite
Workflow that converts generated files in Overwrite into a named mod, preserving provenance and controllable priority.

### Executable registration
MO2 configuration defining an external tool's executable, arguments, working directory, and related launch options.

### Run through MO2
Launching a tool under USVFS so it sees the profile's virtualized mod state.

### MO2 conflict icon
UI indication that a mod contains files that overwrite or are overwritten by files from another mod.

### Hidden file
MO2 mechanism to suppress a particular conflicting file from a mod without deleting the entire mod.

### Mod separator
Organizational pseudo-entry used to group mods visually; it does not itself contribute files.

### Instance
MO2 manager context tied to a game/location and configuration.

### Profile-specific load order
Plugin order stored for one MO2 profile.

### Profile-specific modlist
Enabled/order state of left-pane mods stored per profile.

### MO2 meta.ini
Per-mod metadata file used by MO2 for information such as Nexus identifiers, versioning, installation state, and categories.

## Vortex

### Vortex
Nexus Mods' general-purpose mod manager. It manages downloads, installed mods, profiles, plugin sorting, and deployment.

### Deployment
Vortex process of materializing managed mod state into the game's filesystem through supported link/copy mechanisms.

### Hardlink deployment
Deployment strategy using filesystem hard links so a staged file and game-visible path refer to the same underlying file data. It requires compatible filesystem/volume constraints.

### Symlink/junction-style deployment
Deployment approach using filesystem links supported by the relevant game/extension and environment. Exact method availability is game/platform specific.

### Staging folder
Vortex-managed location containing installed mod files before deployment.

### Deployment conflict
Situation where multiple staged mods target the same game path and Vortex must choose the winning source according to rules.

### File conflict rule
Vortex rule specifying that one mod's conflicting files load/deploy before or after another mod.

### Rule cycle
Conflict-order constraints form a cycle that cannot be resolved consistently.

### Mod rule
User/automatic relationship controlling relative asset priority between mods.

### Plugin autosort
Vortex/LOOT-integrated ordering of plugin files. This is separate from file-deployment rules.

### Vortex profile
Saved enabled-mod/plugin/settings context for a game.

### Root deployment
Functionality or extension support for placing files outside Data into the game root when a mod genuinely requires root files.

## Load-order versus file-order diagnostics

### Asset priority
Order deciding meshes, textures, scripts, DLL data/configs, animations, UI files and other same-path file winners.

### Record priority
Plugin override ordering deciding which plugin record fields win.

### Script file conflict
Two mods provide the same PEX path. File priority determines which compiled script class loads, even when plugin load order is unchanged.

### DLL file conflict
Two packages provide the same SKSE plugin DLL path. The file winner decides which binary exists; load order cannot select between same-path DLLs.

### INI/config conflict
Two mods provide the same configuration file. File winner may silently replace settings expected by another package.

### Generated-file conflict
Generated behavior, BodySlide, LOD, or patch output is overwritten by another source at the same path.

### Root-file conflict
Two systems replace the same root DLL/proxy/preloader. Ordinary Data-level mod priority may not describe the actual winner.

## Wabbajack and reproducible modlists

### Wabbajack
Automated modlist installer/compiler designed to reproduce a complete modding setup from downloadable source archives and generated instructions without redistributing third-party mod assets as one bundled pack.

### Modlist
Curated collection of mods, configuration, patches, generated outputs, and installation instructions intended to produce a particular game setup.

### Wabbajack compiler
Tooling that analyzes a source modlist installation and produces an installer description/instructions for reconstructing it.

### Wabbajack installer
Tooling that consumes a compiled modlist and source archives to recreate the target setup.

### .wabbajack
Compiled modlist package/instruction artifact used by Wabbajack.

### Archive hash
Content hash used to identify an exact source download/archive.

### Hash-based reproducibility
Using content hashes so the compiler/installer can distinguish exact file versions rather than trusting filenames alone.

### Download source
Location/provider from which an archive can be retrieved during installation.

### Nexus API download
Wabbajack can use Nexus APIs for supported Nexus downloads rather than redistributing the mod itself.

### Manual download
Installer step requiring user interaction when a source cannot be automatically retrieved.

### Inline file
Small/generated/configuration file represented directly in modlist instructions rather than fetched as a third-party archive, subject to licensing/distribution rules.

### Remapped file
Compiled instruction that takes a file from a known source archive and places it at the target installation path.

### BSA creation/packing step
Modlist compilation/installation transformation that can build archive output rather than merely copying original files.

### Modlist manifest
Metadata describing included mods/sources, versions, authors and related information exposed to users.

### List healing
Wabbajack process/workflow for updating broken source references or repairing a modlist when downloadable source archives change/disappear, where supported.

### Reproducibility failure
Target file cannot be reconstructed because a source archive/version/hash is unavailable or instructions no longer resolve.

### Stock Game / game-file copy
Modlist pattern in which a controlled copy of required game files is used to isolate the list from live game updates and root-directory drift. Exact implementation is list/tool specific.

### Portable list
Modlist designed to minimize assumptions about the user's existing mod setup and reproduce its own controlled environment.

## FOMOD and installers

### FOMOD
Common mod-installer package convention using XML configuration to present installation options and select files/conditions.

### ModuleConfig.xml
Common FOMOD installer definition file.

### Conditional install
Installer branch that selects files based on user choices, plugin presence, game version, or other supported conditions.

### Installer option
User-selectable feature/variant in a FOMOD.

### Required install pattern
Files that install regardless of optional choices.

### Plugin condition
Installer condition based on whether a particular plugin is present/active.

### Version-dependent installer branch
Installer choice/condition selecting DLLs/configs for different Skyrim runtimes.

## Provenance and reproducibility rules encoded for Agent OS

1. Always distinguish plugin load order from asset/file priority.
2. Record whether the user uses MO2, Vortex, manual installation, or a modlist manager before prescribing filesystem steps.
3. External generators must be launched in the same effective environment that contains the mods they are meant to inspect.
4. Treat MO2 Overwrite/Vortex generated output as unclassified provenance until moved into a named output layer.
5. If a generated result is correct on disk but not in game, inspect whether another mod wins the same path.
6. Root files require separate inspection from Data files.
7. Reinstalling a mod can change selected FOMOD options even if the version number is identical.
8. A reproducible modlist requires exact source/version/hash tracking; filename similarity is insufficient.
9. Do not assume Wabbajack redistributes full mod archives; its stated architecture reconstructs installations from sources/instructions.
10. When debugging someone else's modlist, preserve list-specific generated patches/configs before applying generic recommendations.

## Sources

- Mod Organizer 2: https://github.com/ModOrganizer2/modorganizer
- USVFS: https://github.com/ModOrganizer2/usvfs
- Vortex: https://github.com/Nexus-Mods/Vortex
- Vortex documentation/wiki index: https://github.com/Nexus-Mods/Vortex/wiki
- Wabbajack: https://github.com/wabbajack-tools/wabbajack
- Wabbajack documentation: https://wiki.wabbajack.org/
