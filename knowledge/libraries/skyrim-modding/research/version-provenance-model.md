# Skyrim Modding Version and Provenance Model

Updated: 2026-09-24
Status: canonical evidence policy

## Purpose

Skyrim modding advice becomes unsafe when facts from different runtimes/tool generations are flattened into one timeless rule. Every durable technical claim should carry enough provenance to answer: **true for what version, observed where, and how strongly validated?**

## Version dimensions

Record independently:

### Game executable
Examples:
- 1.5.97;
- 1.6.640;
- 1.6.659;
- 1.6.1130;
- 1.6.1170;
- 1.7.x;
- Skyrim VR 1.4.15.

### Distribution
- Steam;
- GOG;
- Microsoft/Xbox PC where applicable;
- VR.

### SKSE
Exact SKSE/SKSEVR build.

### Address Library
Exact database package/version.

### Creation Kit
Exact CK executable/update generation.

### xEdit
Exact SSEEdit/xEdit build.

### Native framework
Exact DLL release and fork.

### Config grammar
Version of SPID/KID/OAR/SkyPatcher/etc. whose syntax is being described.

### Source mod
Exact mod/file version.

### Save
New game vs migrated established save and source version history.

## Evidence source classes

### Upstream source code
Highest authority for implementation at that commit.

### Official documentation
High authority for intended/supported behavior, but can lag implementation.

### Tool-generated schema/log
Direct evidence of current tool behavior.

### Reproducible test
Strong empirical evidence when environment is recorded.

### Maintainer issue/comment
Useful scoped evidence; preserve date/version.

### Community technical guide
Secondary evidence; corroborate important claims.

### Forum/Reddit anecdote
Lead/hypothesis unless independently verified.

### Legacy guide
Historical evidence only until applicability to current runtime is shown.

## Claim status

### CURRENT
Validated on current target version.

### VERSION-SCOPED
True for specified versions.

### HISTORICAL
Useful old behavior no longer assumed current.

### EXPERIMENTAL
Supported by limited tests/source branch.

### CONTESTED
Credible evidence disagrees.

### UNVERIFIED
Lead awaiting validation.

### SUPERSEDED
Newer evidence replaces prior claim for same version/scope.

## Confidence

### High
Upstream/official + reproducible behavior agree.

### Medium
Good source or repeatable observations but incomplete edge coverage.

### Low
Community claim or weak/ambiguous evidence.

## Fact record fields

Each durable technical fact should support:
- id;
- statement;
- domain;
- status;
- confidence;
- game runtime(s);
- tool/framework version(s);
- source URL/repository/path;
- source commit/tag/date;
- observed/tested date;
- test environment;
- contradictory evidence;
- supersedes/superseded-by;
- related concepts;
- notes.

## Runtime-support claim

Never store only:
> supports AE

Store:
- exact executable versions tested/declared;
- Steam/GOG/VR;
- SKSE requirement;
- Address Library requirement;
- universal vs runtime-specific DLL;
- source of support claim;
- observation date.

## Tool-behavior claim

Example:
> OAR higher priority wins.

Also record:
- OAR version family;
- config/submod context;
- whether user.json overrides are relevant;
- source docs/commit.

## Historical forum claims

Preserve:
- original URL/archive;
- author/maintainer identity if relevant;
- date;
- target Skyrim edition;
- tool versions from era;
- whether reproduced on SE/AE/current tools.

Do not silently promote LE-era advice into SE/AE.

## Contradictions

When two sources disagree:
1. do not overwrite either;
2. compare version/runtime/config;
3. classify whether disagreement is actually scope difference;
4. reproduce if practical;
5. mark unresolved if not.

## Update ingestion

When a tool/framework releases:
- snapshot release notes;
- detect breaking config/API changes;
- mark prior facts version-scoped;
- update compatibility matrix;
- queue regression tests for important integrations.

## Canonical vs high-frequency data

Git should store:
- schemas;
- validated rules;
- release snapshots;
- compatibility matrices;
- decisions.

Local database/index should store:
- high-frequency scrape results;
- raw issue/comment snapshots;
- logs;
- per-run observations.

## Why dates matter

A 2019 answer can still be correct for 1.5.97 while wrong for 1.7.x.
A 2026 Nexus page can describe current DLL support while its old comments describe superseded builds.
A current config syntax can be accepted by old runtime-neutral parser even when its DLL cannot load on that runtime.

Version is part of the fact.
