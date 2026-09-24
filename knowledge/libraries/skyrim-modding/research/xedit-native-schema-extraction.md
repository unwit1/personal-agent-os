# xEdit-Native Schema Extraction Plan

Updated: 2026-09-24
Status: preferred strategy for the exhaustive record-schema frontier

## Discovery

Current xEdit source includes `xDump.dpr`, which can run in **Export** mode and dump the tool's own plugin definition. Its built-in help documents:

- `<Game>Dump [options] inputfile`;
- `<Game>Export [options] format`;
- Export dumps the plugin definition;
- supported definition formats include `RAW` and `UESPWIKI` (the latter described upstream as very WIP).

Tool mode and game mode can be selected either from executable name or command-line switches. Current source explicitly detects switches corresponding to the `TwbToolMode` and `TwbGameMode` enums, making a command form such as `xDump -Export -SSE RAW` the preferred automated capture pattern when using a compatible built executable.

## Why this replaces regex-first extraction

The repository originally added `extract_xedit_schema.py` as a conservative lexical inventory of `wbRecord` definitions. That remains useful as a fallback/source-audit tool, but it cannot faithfully reconstruct:

- shared/common definitions;
- nested subrecords;
- conditional definitions;
- enums/flags;
- count paths;
- version/form-version-dependent layouts;
- after-load/after-set behavior;
- dynamically composed structures.

xEdit itself already resolves those definitions internally. Capturing xDump Export output preserves far more semantic structure and reduces extractor assumptions.

## Preferred pipeline

1. Pin exact xEdit release/tag/commit.
2. Build/use the matching xDump/xExport executable.
3. Run `tools/knowledge/capture_xedit_schema.py`.
4. Store raw output and metadata in local high-volume knowledge storage.
5. Parse raw export into normalized record → subrecord → field structures.
6. Diff against prior snapshot.
7. Flag new/removed/changed fields.
8. Review semantic changes.
9. Promote durable field knowledge into the repository.
10. Trigger patch-rule regression checks for changed Skyrim definitions.

## Provenance

Every capture must retain:

- xEdit upstream URL;
- tag/commit;
- executable SHA-256;
- game mode;
- export format;
- command line;
- timestamp;
- parser version used downstream.

## Current upstream evidence

xEdit `xDump.dpr` on the current development branch contains:
- `TExportFormat = (efUESPWiki, efRaw)`;
- explicit parsing of RAW and UESPWIKI;
- tool/source/game-mode detection from command-line switches;
- help text stating Export dumps the plugin definition.

Source:
https://github.com/TES5Edit/TES5Edit/blob/dev-4.1.6/xDump.dpr

## Next parser layer

The normalized parser should preserve, at minimum:

- record signature;
- record display name;
- subrecord signature/name;
- nested field path;
- scalar/container/array type;
- FormID target restrictions;
- flags/enums;
- version/form-version conditions;
- count relationships;
- required/optional/repeating semantics;
- xEdit source/profile/version;
- known after-load/validation rules.

Do not auto-generate patch recommendations from structure alone. Conflict semantics still require engine/domain intent.
