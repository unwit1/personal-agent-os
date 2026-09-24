# Skyrim Modding Terminology — SkyPatcher and General Runtime Record Patching

Imported: 2026-09-24
Status: sourced encyclopedia pass 3
Version snapshot: SkyPatcher 7.0.3 observed on Nexus on 2026-09-24

SkyPatcher is broader than specialist distributors such as SPID, KID, BOS, and FLM. This module records its general runtime-patching model separately so Agent OS can reason about config conflicts and choose the narrowest appropriate framework.

## SkyPatcher fundamentals

### SkyPatcher
SKSE framework by Zzyxzz that modifies many categories of loaded Skyrim forms/references at runtime from declarative INI configuration instead of requiring equivalent static plugin overrides.

### Runtime record patching
Changing loaded form data in memory after plugin loading rather than writing that change into an ESP/ESL.

### SkyPatcher INI
Text configuration containing filters and patch actions.

### SkyPatcher root
Current source scans `Data/SKSE/Plugins/SkyPatcher/` recursively for INI files.

### Recursive config loading
SkyPatcher can discover INI files in nested directories under its configuration root, enabling mod-specific organization.

### Filter key
Left-side rule term selecting which records/references should be affected.

### Identifier
Record selector expressed through supported EditorID or plugin/FormID notation.

### EditorID identifier
Human-readable EditorID used for lookup where supported.

### Plugin|FormID identifier
SkyPatcher notation combining plugin filename and hexadecimal local/full FormID representation.

### Action key
Rule segment describing the mutation to perform on matched records.

### Filter-action line
General declarative structure combining a target filter with one or more patch operations.

### Mass edit
Rule potentially affecting many records based on category/filter rather than one explicit form.

### Copy visual style
SkyPatcher capability/pattern copying supported NPC visual/appearance fields from another actor source.

### Leveled-list addition
Runtime addition to leveled-list records without requiring the same static LVLI/LVLN override pattern.

### Stat refresh
SkyPatcher feature/code path for refreshing affected NPC/reference state after runtime modifications where supported.

### NPC patching
SkyPatcher record category modifying actor-base characteristics.

### Reference patching
Runtime changes aimed at placed/runtime references rather than only base forms.

### Category patcher
Internal/source organization where weapons, armor, NPCs, spells, magic effects, races, references and other categories have specialized patch logic.

### Merge Mapper API integration
SkyPatcher source includes MergeMapper API support so configuration referencing original plugins/forms can potentially interoperate with merged-plugin identity mapping.

### INI precedence
When multiple SkyPatcher configs affect the same target/property, load/config processing order can determine the final runtime value.

### Alphabetical path order
Community tooling such as SkyScope documents practical SkyPatcher conflict resolution based on alphabetical full-path config order for relevant NPC patch conflicts. Verify against current source/version for any critical workflow.

### Runtime patch conflict
Two config rules mutate the same record/property incompatibly. Avoiding ESP conflicts does not eliminate semantic conflicts.

### Blanket patch
Unintended broad rule caused by missing/unsupported filters, potentially affecting far more records than intended.

### Unsupported filter
Config condition not understood by the active SkyPatcher version/category. Validators should fail/skip rather than silently turning it into an unrestricted patch.

### SkyPatcher log
Primary runtime evidence for INI discovery/parsing, patch application and failures.

## Framework selection

### SkyPatcher vs SPID
Use SPID when the semantic task is specifically distribution of supported forms/data to NPCs and its filter model fits. Use SkyPatcher when broader actor/base-record fields need runtime mutation.

### SkyPatcher vs KID
KID specializes in adding keywords to supported form types. SkyPatcher is broader; use KID when classification alone is the problem because narrower semantics are often easier to inspect.

### SkyPatcher vs BOS
BOS specializes in replacing base objects of placed references and related transform/property behaviors. Use BOS when that exact world-object swap model fits.

### SkyPatcher vs FLM
FLM specializes in runtime FormList mutation and provides collections/groups/events. Use FLM when list composition is the primary behavior.

### SkyPatcher vs static plugin patch
Use static plugin output when downstream tools/game systems must see the final record data before runtime patch application, or when provenance/reproducibility is better served by an ordinary plugin.

### SkyPatcher vs Synthesis
SkyPatcher mutates loaded runtime data from INIs. Synthesis generates plugin output before the game launches. Both can automate compatibility but operate at different stages.

## Validation and design rules

1. Prefer explicit filters for mass edits.
2. Validate record identifiers against the actual load order.
3. Record config processing order when multiple files touch the same target/property.
4. Inspect SkyPatcher logs before concluding a runtime rule failed semantically.
5. A runtime-patched field may not be visible as the winning xEdit record because the mutation happens after plugin loading.
6. If another mod reads the field before/after SkyPatcher's mutation at a different lifecycle stage, initialization order may matter.
7. Runtime patching does not remove the need to understand save persistence for fields later serialized into references/quests/scripts.
8. EditorIDs are readable but can be absent/nonunique in edge cases; FormID+plugin targeting is more explicit.
9. Treat general runtime patching as code/config infrastructure with versioned grammar.
10. For modlists, pin SkyPatcher and preserve exact INI files/order as part of the generated environment.

## Sources

- SkyPatcher Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/106659
- SkyPatcher source: https://github.com/Zzyxz/SkyPatcher
- SkyPatcher source `main.cpp`: https://github.com/Zzyxz/SkyPatcher/blob/main/main.cpp
- SkyPatcher Studio source-traced syntax notes: https://github.com/Jrollsons/skypatcher-studio/blob/master/SKILL.md
- SkyScope conflict analyzer: https://github.com/Kussie/Skyscope
