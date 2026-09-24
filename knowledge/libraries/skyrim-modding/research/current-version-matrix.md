# Skyrim Modding Current Version Matrix

Snapshot date: 2026-09-24
Status: dated observation — never treat this file as timeless

## Purpose

This file records versions that were directly verified from authoritative upstream release surfaces on the snapshot date. It is intentionally conservative: an unverified tool is omitted rather than guessed.

| Component | Verified current release | Upstream | Snapshot notes |
|---|---|---|---|
| xEdit / SSEEdit | 4.1.5f | https://github.com/TES5Edit/TES5Edit/releases | Latest GitHub release observed. Release includes TES5VR Backported ESL-range fix and TES5/SSE definition updates. |
| LOOT | 0.29.1 | https://github.com/loot/loot/releases | Latest GitHub release observed. Windows build requires 64-bit Windows 10 1809+ and MSVC 2022 x64 redistributable. |
| Mod Organizer 2 | 2.5.2 | https://github.com/ModOrganizer2/modorganizer/releases | Latest GitHub release observed. Release lists libloot 0.23.0, Qt/PyQt 6.7.1 and Python 3.12.3 among bundled dependencies. |
| Community Shaders | 1.9.1 | https://github.com/community-shaders/skyrim-community-shaders/releases | Released 2026-09-24. Upstream release commit shown as 265c28f. |

## Compatibility dimensions to track separately

A single version string is not enough for Skyrim compatibility. For every native/tool entry, preserve where relevant:

- Skyrim executable version;
- Steam/GOG/VR distribution;
- SKSE/SKSEVR version;
- Address Library version;
- BEES requirement;
- Creation Kit generation;
- configuration grammar version;
- source commit/tag;
- observed release date;
- whether the entry is upstream, fork, port, or backport.

## Update policy

1. Refresh from upstream release pages/repositories.
2. Never infer a release from a Nexus “updated” date alone.
3. Keep old snapshots when they explain historical compatibility.
4. Mark prerelease/experimental builds explicitly.
5. If GitHub/Nexus disagree, record both and determine whether one is a mirror, prerelease, hotfix, or delayed tag.
6. Do not overwrite a version-scoped compatibility fact merely because a newer release exists.
7. Link release notes/change logs when a change affects runtime support, record schemas, config grammar, or generated outputs.

## Automation target

A future updater should:
- query configured upstream providers;
- compare semantic/tag versions;
- record release timestamp and source commit;
- detect compatibility-impacting release-note terms;
- create a candidate update rather than silently changing canonical support claims;
- run relevant regression/ingestion jobs after approval or high-confidence policy rules.

See `version-provenance-model.md` for evidence semantics.
