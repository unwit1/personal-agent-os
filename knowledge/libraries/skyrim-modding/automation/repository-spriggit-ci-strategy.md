# Skyrim Mod Factory — Repository, Spriggit, and CI Strategy

Created: 2026-09-24

## Goal

Make Skyrim mod development behave like software engineering:
- source-controlled;
- diffable;
- reviewable;
- reproducible;
- testable;
- revertible.

## Canonical project layout

```text
mod-root/
  mod.project.json
  README.md
  docs/
  src/
    plugin/
    papyrus/
    native/
    tools/
  configs/
  assets/
    source/
    generated/
  spriggit/
  tests/
    fixtures/
    reports/
  generated/
  dist/
```

### Source of truth

Track:
- design/docs;
- PSC;
- C++/C#/Python;
- config source;
- editable assets;
- Spriggit text representation when adopted;
- fixtures/expected outputs;
- build metadata.

Do not treat:
- MO2 Overwrite;
- generated PEX;
- generated behavior;
- LOD;
- temporary plugin copies;
- release ZIP
as canonical source unless a project has a specific reason.

## Spriggit

Spriggit converts Bethesda plugins to YAML/JSON text suitable for Git and can deserialize that text back into plugins.

Use it when:
- CK/xEdit editing is part of authoring;
- binary ESP diffs would otherwise hide record changes;
- collaboration/review matters;
- Agent OS needs to inspect plugin changes in ordinary Git commits.

### Recommended workflow

1. edit/generate plugin;
2. validate plugin;
3. Spriggit serialize;
4. review text diff;
5. commit source + Spriggit change together;
6. CI deserializes to candidate plugin;
7. xEdit/Mutagen validate candidate;
8. semantic compare to expected.

### Pin translation package

Spriggit records the package/version used to serialize. Pin it in `.spriggit`.

Do not mix:
- Spriggit translation-package upgrade;
- actual mod changes
in one commit. Review the serializer-format churn separately.

### Round-trip gate

CI should:
- deserialize tracked text;
- serialize/deserialize as supported;
- load output through Mutagen;
- run xEdit Check for Errors;
- compare normalized semantic representation.

## Mutagen + Synthesis

Use Mutagen for:
- typed plugin generation;
- read-only binary overlay;
- FormKey linking;
- load-order contexts.

Use Synthesis for:
- patches derived from actual user load order.

Current Mutagen release observed on 2026-09-24: 0.54.4. Treat this as a dated snapshot.

## Antigen / Mutagen.Bethesda.Analyzers

Antigen is explicitly aimed at turning known Bethesda bug patterns into reusable programmatic analyzers/CLI findings.

Agent OS should:
1. ingest its Skyrim analyzer catalog;
2. map analyzer concepts to Mod Factory gate codes;
3. run available analyzers on source/output/load-order fixtures;
4. contribute equivalent local checks for known bugs not yet implemented upstream;
5. preserve upstream issue/source provenance.

Do not assume every open Antigen research issue is a proven bug rule. Classify:
- implemented analyzer;
- researched/validated;
- proposed;
- unresolved.

## CI stages

### Stage A — source lint
- JSON/XML;
- C#/C++/Python format/static checks;
- PSC syntax/compile;
- config grammar.

### Stage B — generate
- plugin;
- scripts;
- native binaries;
- runtime configs;
- assets.

### Stage C — schema validation
- Mutagen reopen;
- xEdit error check;
- FormLink resolution;
- Spriggit round trip if used.

### Stage D — integration generation
- Synthesis;
- Pandora;
- BodySlide;
- LOD generators as applicable.

### Stage E — package
- clean staging tree;
- FOMOD validation;
- archive manifest.

### Stage F — runtime smoke
Usually performed on a Windows runner/machine with authorized local game assets rather than a public hosted runner.

Collect results into build report.

## Local runner boundary

Official game masters, Creation Kit files, and other proprietary game data should remain on authorized local/self-hosted runners.

GitHub can store:
- source;
- schemas;
- normalized non-copyrighted technical metadata;
- tests that do not redistribute Bethesda assets;
- reports/hashes.

## Pull-request review

Every change should make clear:
- which records/assets/frameworks changed;
- generated artifact impact;
- gates rerun;
- save compatibility;
- runtime support;
- expected screenshots/game tests.

## Branch strategy

Recommended:
- `main` = releasable/validated;
- feature branches = experiments;
- tags = releases.

Generated release artifacts are built from a tag/commit, not manually assembled from an uncommitted Data folder.

## Reproducibility target

Given:
- Git commit;
- manifest;
- locked tools;
- authorized game data hashes;
- dependency versions;

the pipeline should reproduce semantically identical plugin/config/asset/package output.
