# Skyrim Modding Terminology — Nexus Mods Metadata, Files, Dependencies, and Collections

Imported: 2026-09-24
Status: sourced deep-ingestion pass 10

## Mod identity

### Nexus game domain
Slug identifying a Nexus game site, e.g. `skyrimspecialedition`.

### Nexus mod ID
Game-scoped numeric identity appearing in URLs such as `/mods/12345`.

### Composite/global mod ID
Newer Nexus API identity that can combine game identity and mod identity into a platform-global identifier.

### Mod page
Metadata/documentation surface for one mod project.

### Mod author
Nexus account credited with publishing the mod.

### Summary
Short description used in metadata/search.

### Description
Long-form mod documentation authored on the mod page.

### Category
Nexus classification used for discovery; not a reliable technical compatibility ontology by itself.

### Tag
Additional searchable metadata.

### Endorsement
User appreciation signal. Nexus explicitly warns endorsement count is subjective and does not necessarily measure quality or current relevance.

### Trending mod
Time-window ranking influenced by endorsements/download behavior according to Nexus platform rules.

## Files and versions

### Mod file
Download channel/group belonging to a mod, such as Main, Optional or Miscellaneous.

### File ID
Identity for a mod file/version in Nexus APIs/URLs.

### File category
Main, Optional, Miscellaneous or other platform-defined categories.

### Primary mod-manager download
File marked as preferred/default for manager workflow.

### File version
Version string attached to uploaded mod file version.

### Update chain
Versions associated with the same logical mod file.

### Archived file
Older version hidden from ordinary current-file presentation but retained according to Nexus archival policy.

### Removed file
File/version no longer available.

### File hash
MD5/content hash used by mod managers/Wabbajack/API matching to identify exact archive bytes.

### File size
Archive byte size; useful for identity validation but not sufficient alone.

### Uploaded timestamp
Time one file version was published.

### Changelog
Version-associated list of changes.

### Requirements popup
Download-time prompt showing declared requirements where enabled.

## Dependencies/requirements

### Mod-level requirement
Legacy dependency relationship declared at the whole-mod level.

### File-to-file requirement
Newer dependency model linking a specific source file version to specific candidate file/version dependencies.

### Dependency definition
One requirement relationship attached to a mod-file version.

### Dependency candidate
A concrete visible file version that can satisfy a dependency definition.

### OR dependency alternatives
Multiple candidate versions/files where any one valid candidate satisfies one dependency definition.

### Materialized dependency
Resolved dependency candidates based on currently visible/published file versions.

### Required mod
Declared upstream mod/file that must be installed.

### Optional requirement
Dependency/integration recommended for optional functionality rather than strict runtime necessity.

### Requirement drift
Mod page says dependency is required but file-level metadata or current release has changed; capture both documentation and file-specific requirement state.

### Hidden/removed dependency
Dependency points to file no longer publicly available, affecting reproducibility.

## Permissions/provenance

### Asset permission
Author's permission for reuse/modification/redistribution of their work.

### Upload permission
Whether another user may reupload files.

### Modification permission
Whether assets/code may be modified.

### Conversion permission
Permission to port content to another game/platform/version.

### Donation Points permission
Whether derivative use is allowed in DP-earning mods.

### Third-party asset
Content whose copyright/permission comes from another creator; mod page permission field may not cover every included asset.

### Provenance record
Agent OS record of source URL, mod ID, file ID, file version, archive hash, author, permissions, retrieval date and exact role in a project.

## Collections

### Nexus Collection
Metadata/list describing a reproducible Vortex-managed set of referenced mods plus optional allowed bundled generated assets.

### Curator
Author/maintainer of a collection.

### Collection revision
Versioned snapshot of collection metadata/instructions.

### Collection manifest
Machine-readable list of included mod/file references, rules and instructions.

### Bundled asset
Collection-provided generated/support asset permitted by Nexus rules; collections do not simply redistribute referenced mods.

### External resource
Required/recommended file hosted outside Nexus and referenced by collection.

### Collection install
Vortex-driven resolution/download/deployment of collection contents.

### Collection dependency pin
Specific mod file/version reference chosen by curator.

### Collection update
New revision changing mod versions/rules/instructions.

### Collection support boundary
Nexus guidelines place responsibility for collection-specific troubleshooting on the curator rather than automatically on each mod author.

## Nexus API v3

### Nexus API
Official integration interface for mod metadata, files, dependencies, collections, uploads and platform actions.

### Stable endpoint
API operation promised production stability with long deprecation notice.

### Beta endpoint
Feature-complete but subject to shorter-notice change.

### Experimental endpoint
May change significantly; not appropriate for assumptions requiring long-term API stability.

### Upload session
API workflow creating temporary upload target before finalizing into a mod file version.

### Presigned upload URL
Storage URL used to upload archive bytes for an upload session.

### MD5 upload binding
Integrity mechanism tying upload URL/body to expected file digest. Nexus API documentation states MD5 becomes required for create-upload on 2026-12-01.

### API deprecation
Endpoint/field marked for removal with documented migration period.

### OAuth/JWT/API key
Authorization mechanisms supported by Nexus API depending on endpoint/application context.

## Agent OS ingestion rules

For every captured Nexus mod, store:
- game domain;
- mod ID;
- canonical URL;
- author;
- title/summary;
- current page/version snapshot;
- selected file ID/version/hash;
- file category;
- dependencies/requirements;
- installation/config notes;
- compatibility/runtime claims;
- permissions/provenance;
- changelog/release date;
- source retrieval date;
- project relationship;
- confidence and whether claims were independently validated.

Do not treat:
- endorsement count as technical quality;
- “works with AE” as exact runtime compatibility;
- old main-file version as equivalent to current file;
- mod-page requirement as automatically applying to every historical file version;
- Nexus category/tags as authoritative technical metadata.

## Sources

- Nexus Mods API v3: https://api-docs.nexusmods.com/
- Nexus API OpenAPI schema in Vortex: https://github.com/Nexus-Mods/Vortex/blob/master/packages/nexus-api-v3/schema/openapi.yaml
- Nexus Collections guidelines: https://help.nexusmods.com/article/115-guidelines-for-collections
- Nexus endorsement explanation: https://help.nexusmods.com/article/45-what-are-file-endorsements
- Nexus submission guidelines: https://help.nexusmods.com/article/28-file-submission-guidelines

## Dated API note

Nexus API v3.0.0 documentation observed 2026-09-24 marks many mod-file/dependency operations Experimental and announces that MD5 becomes required on create-upload beginning 2026-12-01. Agent integrations should read endpoint stability metadata and avoid hard-coding experimental schemas as permanent.
