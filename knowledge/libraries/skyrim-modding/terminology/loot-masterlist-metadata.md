# Skyrim Modding Terminology — LOOT Masterlist, Metadata, and Sorting Rules

Imported: 2026-09-24
Status: sourced deep-ingestion pass 15

## LOOT sorting model

### LOOT
Load Order Optimisation Tool calculating plugin order from hard dependencies and metadata constraints and reporting known plugin issues.

### libloot
Library implementing metadata parsing/sorting functionality used by LOOT ecosystem.

### Masterlist
Community-maintained metadata database for one supported game.

### User metadata
Local metadata overrides/additions created by user, separate from upstream masterlist.

### Plugin metadata
Structured rules/messages/tags associated with a plugin filename/pattern.

### Hard sorting rule
Constraint that must hold, such as master dependency, explicit requirement or applicable load-after relationship.

### Soft sorting rule
Lower-priority relationship such as group ordering that may be ignored when conflicting with hard rules/cycles.

### Topological sort
Graph ordering algorithm producing linear plugin order satisfying dependency constraints.

### Cycle
Set of ordering relationships that cannot all be satisfied.

### Cyclic interaction
LOOT error where dependencies/groups/load-after metadata form loop.

## Metadata fields

### group
Name of plugin group.

### after / Load After
Plugins that, if present, current plugin should load after but does not strictly require for operation.

### req / Requirement
File/plugin that must be present; LOOT reports error if missing and orders plugin after plugin requirements.

### inc / Incompatibility
File/plugin whose presence is declared incompatible.

### msg / Message
Informational/warning/error text displayed in LOOT report. Messages do not themselves affect sorting.

### tag / Bash Tag
Suggested Wrye Bash tag additions/removals.

### dirty
Known dirty-plugin information keyed to CRC and expected ITM/deleted-reference/deleted-navmesh counts.

### clean
Known-clean CRC information and cleaning utility provenance.

### url/location
Source location metadata for parent mod/project.

### condition
Boolean expression deciding whether metadata entry applies.

### constraint
Additional condition governing file recognition in current LOOT metadata model.

### display name
Human-readable name used in requirement/error messages.

### detail
Additional localisable information appended to message/requirement.

## Groups

### Plugin group
Named collection whose relative position is described against other groups.

### default group
Fallback group for plugins without another assignment.

### Group edge
"Group B loads after Group A" relationship.

### Transitive group order
If C after B and B after A, C is effectively after A.

### Group cycle
Groups indirectly/directly require each other; invalid/ambiguous.

### Group membership ignored
LOOT may ignore a soft group relationship when applying it would conflict with stronger master/dependency ordering.

### Groups Editor
LOOT UI for visualizing/editing group graph.

## Conditions

### Metadata condition
Expression evaluating environment such as file/version/checksum presence before rule applies.

### File condition
Rule activated by presence/version/hash of file.

### Version condition
Metadata applies only to matching plugin/mod version.

### CRC condition
Dirty/clean metadata tied to exact file CRC so another version is not misidentified.

### Regex plugin match
Masterlist can target plugin filename patterns in contexts supported by metadata syntax; not every field permits regex.

## Cleaning metadata

### Dirty plugin CRC
Checksum identifying exact plugin build known to contain cleaning candidates.

### ITM count
Expected Identical To Master count.

### Deleted reference count
Expected hard-deleted REFR count.

### Deleted navmesh count
Expected deleted NAVM count.

### Cleaning utility
xEdit/SSEEdit version/tool named for cleanup verification.

### Clean CRC
Exact plugin build confirmed clean.

### Cleaning message
LOOT warning/instruction based on matching CRC.

### False dirty warning
Plugin version/hash differs or author intentionally uses edits; do not clean solely because another version was dirty.

## Bash Tags

### Bash Tag suggestion
Metadata advising Wrye Bash which categories should be imported into Bashed Patch.

### Tag addition
Recommended tag.

### Tag removal
Metadata saying tag should not apply.

### Plugin-embedded tag
Tag present in plugin metadata/description recognized separately from masterlist/user suggestions depending on tooling.

## Contributing/masterlist authoring

### Masterlist contribution
Pull request adding/updating metadata for community use.

### Minimal metadata
Add only ordering/compatibility rule proven necessary rather than cargo-culting arbitrary "load after" relationships.

### Reproducible reason
Metadata contribution should explain issue and how ordering fixes it.

### Conditional metadata
Scope rule to versions/configs where problem actually exists.

### Masterlist test
Run LOOT/libloot validation against edited metadata.

### Metadata conflict
Upstream/user/plugin metadata disagree; understand precedence/current effective rule.

## Diagnostic rules

1. LOOT order is graph-derived; do not describe it as a universal category list.
2. "Load after" means one whole plugin should win relevant conflicting data; it cannot merge two desired field sets.
3. Requirements are not a substitute for explicit plugin masters, and LOOT already sees masters.
4. Group ordering is soft and can be ignored to satisfy hard dependencies.
5. Dirty metadata is version/hash-specific.
6. LOOT messages can be advisory without affecting order.
7. Avoid user rules created only to silence a symptom; patch semantic conflicts when both changes are needed.
8. Record user metadata because it can make two otherwise identical modlists sort differently.

## Sources

- LOOT upstream: https://github.com/loot/loot
- LOOT plugin metadata editor docs: https://github.com/loot/loot/blob/master/docs/app/usage/plugin_editor.rst
- LOOT group documentation: https://loot.readthedocs.io/en/latest/app/usage/groups_editor.html
- libloot plugin metadata schema: https://loot-api.readthedocs.io/en/stable/metadata/data_structures/plugin.html
- LOOT documentation portal: https://loot.github.io/docs/
