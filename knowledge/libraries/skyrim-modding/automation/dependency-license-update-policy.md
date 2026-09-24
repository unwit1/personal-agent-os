# Skyrim Mod Factory — Dependency, License, Redistribution, and Update Policy

Created: 2026-09-24
Status: release-blocking policy

## Purpose

A mod can be technically correct and still be impossible or unsafe to release because of dependency licensing, asset permissions, runtime support, or generated-output provenance.

The Mod Factory therefore resolves these constraints **before architecture is locked**, not at packaging time.

## Dependency lock

Every external dependency should record:
- canonical project/source;
- exact version/tag/commit;
- runtime targets;
- binary vs source dependency;
- configuration grammar version;
- required user-side dependencies;
- license identifier/text source;
- redistribution policy;
- source-code publication obligation;
- update policy;
- evidence date.

Unknown license/redistribution fields are blockers for redistribution, not permission-by-silence.

## Native/static-link licensing

### CommonLibSSE-NG

As verified on 2026-09-24, current CommonLibSSE-NG documents:

`GPL-3.0-or-later WITH Modding Exception AND GPL-3.0 Linking Exception (with Corresponding Source)`.

Its current README explicitly describes this as a breaking change from the older MIT licensing model and states that a plugin statically linking the current CommonLibSSE-NG forms a combined work and must use GPL-3.0-or-later or a GPL-compatible license, subject to the exact exception terms.

Architecture consequence:
- a native plugin project must resolve its intended license **before** adopting the current CommonLib static dependency;
- Agent OS must not generate an MIT/proprietary license template by habit for a current CommonLib-linked plugin;
- pin the exact CommonLib version because older historical license assumptions are not safe proxies for current releases.

Source:
https://github.com/alandtse/CommonLibSSE-NG

### Open Animation Replacer source

Current OAR source likewise publishes a GPL-3.0-or-later + modding/linking exception license.

Using OAR as an end-user runtime dependency does not mean copying/linking its source into the user's plugin. If code is linked/copied, evaluate the actual license relationship rather than treating "framework dependency" and "source dependency" as identical.

Source:
https://github.com/ersh1/OpenAnimationReplacer

### Mutagen / Synthesis / Spriggit

Current public repositories expose GPL-3.0 licensing. The Mod Factory should distinguish:
- using the tool to generate artifacts;
- referencing a NuGet/library in source;
- redistributing tool binaries;
- copying source.

Those actions can have different obligations.

Sources:
- https://github.com/Mutagen-Modding/Mutagen
- https://github.com/Mutagen-Modding/Synthesis
- https://github.com/Mutagen-Modding/Spriggit

## Tool output vs tool source

Using a GPL tool to process a mod does not automatically make the produced data file GPL merely because the executable was GPL.

However:
- generated source/templates can contain licensed code;
- statically linked libraries affect distributed binaries;
- copied sample code can carry its own terms;
- bundled executables/libraries carry redistribution obligations.

Store the reason for the license decision rather than inferring it from the tool's license alone.

## Third-party mod assets

Before redistributing:
- meshes;
- textures;
- animation files;
- sound;
- voice;
- scripts;
- DLLs;
- FaceGen;
- BodySlide projects;
- config snippets;
- patches derived from third-party assets;

record explicit permission/license/source.

### Compatibility patch distinction

A plugin patch containing new overrides/references can often be authored without redistributing another mod's loose assets.

If an asset must be modified:
- prefer requiring the original and generating the derivative locally when permission is unclear;
- use patch/delta/transformation workflows where technically/legal-permission appropriate;
- do not copy the original asset into release staging merely because the development profile contains it.

## Generated output provenance

Every generated artifact records:
- generator;
- generator version;
- source files;
- source permissions;
- whether output embeds/copies third-party content;
- redistribution policy.

Examples:
- BodySlide output can incorporate source outfit meshes/textures;
- FaceGen derives from NPC/headpart assets;
- behavior generation can combine framework patches;
- LOD output derives from many source meshes/textures;
- voice/FUZ output may derive from voice audio.

"Generated" does not mean permission-free.

## Bethesda game data boundary

Do not redistribute:
- official master files;
- CK/game executables;
- extracted proprietary meshes/textures/audio;
- wholesale decoded game data.

Authorized local runners can inspect/hash/decode selected technical data for validation.

Git should store:
- schemas;
- hashes;
- concise technical facts;
- derived compatibility results;
- test metadata;
- user-authored source.

## AI-generated assets/code

Record:
- generator/provider/model when known;
- source prompts/inputs where project policy requires;
- whether third-party copyrighted source assets were transformed;
- user-approved license for released output.

Do not mark an asset "original" merely because an AI transformation step occurred.

## Dependency minimization

Before adding a framework dependency ask:
1. does vanilla/plugin data solve it?
2. does an already-required framework solve it?
3. is the dependency maintained on all target runtimes?
4. does it alter licensing?
5. does it increase save/runtime failure surface?
6. can the feature degrade gracefully when absent?

Prefer fewer, narrower dependencies when capabilities are equivalent.

## Runtime support claims

A release support claim must identify:
- executable version(s);
- Steam/GOG/VR;
- SKSE/SKSEVR;
- Address Library family if relevant;
- DLL/config variant;
- test evidence.

"SE/AE compatible" is not a sufficient native-plugin support declaration.

## Update policy

Dependencies are pinned for a release.

An update watcher should create a **candidate dependency update**, not silently alter the lock.

Candidate update procedure:
1. fetch upstream release/source metadata;
2. identify schema/API/config changes;
3. compare license;
4. update test matrix;
5. rebuild affected artifacts;
6. run regression fixtures;
7. promote only after gates pass.

## Breaking-change signals

Raise special review when release notes/source diff mention:
- record definitions;
- form/header versions;
- runtime support;
- relocation/address format;
- configuration syntax;
- serialization;
- API removal/rename;
- license;
- generated output format;
- Papyrus source signatures;
- behavior graph format.

## Security and provenance

Tool binaries should come from configured authoritative release sources where possible.

Record:
- download/source URL;
- version;
- checksum/signature when available;
- install location;
- whether binary is official/upstream or a mirror/fork.

Do not execute an arbitrary downloaded binary solely because a mod guide linked it.

## Release gate

A project cannot pass release audit while any shipped/bundled artifact has:
- unknown license when licensing is material;
- unknown source;
- unresolved third-party redistribution permission;
- unsupported runtime claim;
- dependency version missing from lock;
- generated output with unknown embedded-source provenance.

## Machine-readable future fields

Extend project/dependency manifests with:
- `license_spdx`;
- `license_source`;
- `linkage`;
- `redistribution`;
- `source_required`;
- `permission_evidence`;
- `update_policy`;
- `checksum`;
- `runtime_matrix`.

Legal interpretation can be nuanced; Agent OS should surface uncertainty instead of inventing permission.
