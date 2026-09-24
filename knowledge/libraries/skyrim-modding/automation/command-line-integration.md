# Skyrim Mod Factory — Command-Line Integration Registry

Snapshot: 2026-09-24

The preferred automation boundary is a documented CLI/library interface. GUI automation is a fallback only when no supported deterministic interface exists.

## Mod Organizer 2

Current MO2 source exposes global options including:
- `--instance` / `-i`;
- `--profile` / `-p`;
- a `run` command for launching a program/file/configured executable;
- `--executable` / `-e` for configured executable names;
- argument and working-directory overrides.

Automation pattern:

```text
ModOrganizer.exe --instance "<instance>" --profile "<profile>" run -e "<configured executable>" -a "<arguments>"
```

Use MO2 as the VFS/profile launcher. Do not spawn multiple MO2 processes against the same game instance.

Source:
https://github.com/ModOrganizer2/modorganizer/blob/master/src/commandline.cpp

## Synthesis patcher contract

Synthesis supports external programs as patchers when they implement its patcher CLI.

Important arguments documented by Synthesis include:
- `--SourcePath`;
- `--OutputPath`;
- `--GameRelease`;
- `--DataFolderPath`;
- `--LoadOrderFilePath`;
- optional split behavior when master limits are exceeded.

Automation use:
- generated Agent OS patchers should implement this contract;
- build report should capture load-order file and output path;
- output plugin must still pass xEdit/Mutagen validation.

Source:
https://mutagen-modding.github.io/Synthesis/devs/Patcher-CLI/

## LOOT

Current LOOT docs expose:
- `--game`;
- `--game-path`;
- `--loot-data-path`;
- `--auto-sort`.

When `--auto-sort` is supplied with a game, LOOT sorts, applies the load order, and exits unless an error interrupts the process.

Use:
- isolated LOOT data directory for automated fixtures where practical;
- capture metadata/masterlist versions;
- parse warnings/cycles after sort.

Source:
https://github.com/loot/loot/blob/master/docs/app/usage/initialisation.rst

## Pandora Behaviour Engine+

Current upstream startup arguments include:
- `--auto_run`;
- `--auto_close`;
- `--skyrim_debug64`;
- `--output` / `-o`;
- `--tesv` for explicit game root.

Automation pattern:
- maintain a dedicated Pandora output mod;
- pin active patch cache/priority;
- run autorun + autoclose;
- parse `Engine.log`;
- fail build on configured fatal/error classes;
- optionally enable debug XML for behavior-authoring diagnostics.

Source:
https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus

## DynDOLOD / TexGen / xLODGen

DynDOLOD documentation states TexGen/DynDOLOD inherit relevant xEdit command-line switches.

High-value switches:
- game mode such as `-sse` / `-tes5vr`;
- `-o:"<output>"`;
- `-m:"<INI path>"`;
- `-p:"<plugins.txt>"`;
- `-d:"<Data path>"`;
- `-t:"<temp>"`.

xLODGen similarly supports explicit INI/plugins/Data paths.

Automation policy:
- output to dedicated staging directories outside Data, MO2 Overwrite, or VFS-managed source mods;
- verify log lines reporting selected paths;
- hash settings + input load order;
- install output as a separate generated mod;
- rebuild only when relevant world/assets/load order changed.

Sources:
https://dyndolod.info/Help/Command-Line-Argument
https://github.com/sheson/xLODGen

## xEdit / xDump

Already captured in:
- `research/xedit-native-schema-extraction.md`;
- `tools/knowledge/capture_xedit_schema.py`;
- `tools/knowledge/capture_skyrim_master_records.py`.

Use xEdit-native definitions as the schema oracle.

## Papyrus compilers

### Caprica
Current command line supports Skyrim plus imports, flags, output, optimization, release mode, parallel compile and recursion.

Recommended:
- fast CI compiler;
- optionally cross-check release scripts against official compiler.

Source:
https://github.com/Orvid/Caprica

### Official compiler
Keep as release-reference compiler when available in the authorized CK installation.

## FOMOD validation

Use the maintained FOMOD schema/validator ecosystem rather than hand-validating XML.

Automated checks should additionally verify referenced source files and simulate project-supported option combinations.

Source:
https://github.com/dh-nunes/fomod-docs

## PyNifly

PyNifly documents a Python layer capable of reading/writing/manipulating NIF files and standalone scripting without requiring Blender UI for every operation.

Use it as the preferred programmatic NIF validator/transformer where its feature coverage matches the asset.

Source:
https://github.com/BadDogSkyrim/PyNifly

## Adapter execution rules

1. Resolve tool version before launch.
2. Use dedicated generated-output directories.
3. Never overwrite source input in place by default.
4. Capture command, cwd, environment, exit code and logs.
5. Hash inputs/outputs.
6. Parse tool-specific errors.
7. Apply only tool-specific safe retries.
8. Promote outputs only after their validation gates pass.
