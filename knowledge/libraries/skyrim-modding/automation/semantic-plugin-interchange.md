# Skyrim Mod Factory — Semantic Plugin Interchange and Diff Contract

Created: 2026-09-24
Status: schema + comparator implemented; producer adapters pending

## Purpose

Raw ESP/ESM binary diffs are not suitable as the primary review surface.

The Mod Factory needs xEdit, Mutagen, Spriggit/xEditLib and future parsers to emit a common semantic representation so the system can ask:

- did this FormKey appear/disappear?
- did one field change?
- was a record deleted?
- did flags change in the correct record context?
- did VMAD or an asset path change?
- did a round-trip preserve intended semantics?

Implemented:
- `schemas/skyrim-semantic-plugin-v1.schema.json`;
- `tools/skyrim_mod_factory/compare_semantic_plugins.py`.

## Record identity

Canonical record key:
`<SIGNATURE>:<FormKey>`

FormKey should preserve:
- source plugin identity;
- local form identity after the producer's load-order-aware normalization.

Do not key solely by EditorID:
- EditorID can be absent;
- duplicates/collisions are possible;
- renaming an EditorID should appear as a field change, not a new form.

## Fields

`fields` is a hierarchical normalized object using stable semantic field names/paths.

Producer requirements:
- preserve order where engine semantics are ordered;
- represent FormLinks as stable FormKeys;
- normalize localized strings to an explicit representation;
- normalize flags with record-context names;
- do not hide unknown bytes/fields when they are material to round-trip safety;
- state omissions in producer provenance/coverage.

## Array policy

The comparator preserves array order by default.

This is intentional:
- CTDA ordering/OR flags can matter;
- leveled-list ordering can be relevant to reproducibility;
- quest stages/actions/response arrays can be semantically ordered;
- arbitrary sorting can conceal a real change.

A producer may explicitly normalize a known unordered set into deterministic sorted order before emission.

## VMAD

Keep VMAD separate enough to support checks for:
- script names;
- property types/values;
- fragment metadata;
- aliases;
- property FormKeys.

Do not compare PEX bytecode as a substitute for VMAD/plugin attachment semantics.

## Asset paths

A producer should extract paths referenced by the record where feasible.

Those paths feed:
- asset closure;
- VFS winner resolution;
- package/FOMOD checks;
- NIF/texture/voice/UI downstream validators.

## Multi-oracle workflow

### Generated with Mutagen
1. emit semantic representation directly from in-memory model;
2. write plugin;
3. reload plugin through Mutagen binary overlay;
4. emit second representation;
5. run xEdit validation/export;
6. convert xEdit output to same semantic schema;
7. compare.

### Authored in CK/xEdit
1. snapshot plugin through producer A;
2. make editor change;
3. snapshot through producer A;
4. inspect semantic diff;
5. reopen through producer B;
6. compare producer interpretations for changed records.

### Spriggit
Use Spriggit YAML/JSON as an excellent Git source surface, but convert/compare through the semantic contract when validating across tools because Spriggit representation is optimized for serialization/version control, not necessarily the Mod Factory's cross-tool diagnostic model.

## Difference classes

- record added;
- record removed;
- record changed;
- plugin header/master changed;
- scalar field changed;
- field added/removed;
- list changed;
- field type changed.

Future classifiers should add:
- intentional manifest-owned change;
- unrelated field regression;
- schema-oracle disagreement;
- generated noise;
- save-breaking identity change;
- compatibility-impacting master change.

## Producer provenance

Every semantic document records:
- producer;
- producer version;
- source plugin hash;
- load-order hash where applicable;
- schema source;
- timestamp.

A semantic diff without producer/version provenance is diagnostic evidence, not canonical proof.

## Next producer adapters

Priority:
1. Mutagen emitter;
2. xEdit/xDump emitter;
3. Spriggit bridge;
4. xEditLib/houseCARL bridge.

Two independent producers are required before this becomes a release-blocking cross-oracle gate.
