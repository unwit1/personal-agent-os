# Skyrim Modding Terminology — Custom Skills and Progression Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 14

## Vanilla progression

### Actor skill
ActorValue representing a skill such as OneHanded, Destruction or Smithing.

### Skill level
Current value of a skill ActorValue.

### Skill XP
Progress toward next skill level maintained by player progression system.

### AdvanceSkill
Game/Papyrus function adding usage XP to a skill.

### IncrementSkill
Function incrementing skill progress/value through engine progression.

### Player level
Overall level derived through character leveling/progression.

### Legendary skill
Vanilla reset/progression mechanism allowing maxed skill to be reset and perks refunded.

### Perk tree
Graph of PERK records displayed in Skills Menu and unlocked with perk points.

### Perk point
Player currency spent to acquire eligible perks.

### Skill governing attribute
ActorValue/skill associated with a perk tree.

## Custom Skills Framework / CSF

### Custom Skills Framework
SKSE framework allowing mod authors to create additional custom skills with their own perk trees without replacing vanilla skills.

### Custom skill
Framework-defined progression domain with XP/level, perk points/tree and custom UI presentation.

### Custom skill menu
Framework-rendered constellation/perk-tree interface.

### Custom skill config
JSON file under `Data/SKSE/Plugins/CustomSkills/` defining one or more skill trees/menu behavior.

### Skill identifier
Unique config/menu ID used to namespace one custom skill setup.

### JSON schema
Machine-readable definition validating Custom Skills configuration.

### skydome
Config section controlling background/model/camera presentation of custom skill menu.

### perkPoints
Form/global/config source representing points available to spend.

### skillLevel
Form/global/source representing current level.

### skillRatio
Progress value representing fraction toward next level.

### legendary
Configuration enabling/resetting custom skill's legendary behavior where supported.

### Perk tree node
Configured PERK/Form relationship and UI position/prerequisite.

### Perk graph
Connections among perk nodes determining visible tree edges/prerequisites.

### Camera point
Config values controlling menu camera positioning around skydome/perk constellation.

### Custom skill API
Papyrus/native interfaces allowing scripts/mods to open skill menu, add XP/change levels or query custom skill state depending on version.

### CustomSkills Papyrus scripts
Framework script classes such as CustomSkills and extensions available to Papyrus consumers.

### ActiveMagicEffect extension
CSF script/API extension enabling custom-skill operations from ActiveMagicEffect contexts.

### Alias extension
CSF script/API extension operating through aliases.

### Form extension
CSF script/API extension associated with Form hosts.

## Runtime compatibility

### CSF v1
Original framework generation with different plugin/source/permission lineage.

### CSF v2+
Modern framework generation with rewritten/native implementation and permissive licensing as documented by current project.

### CSF v3
Current modern generation adding newer JSON/runtime/UI features.

### 1.5.97 port
Community port targeting older SE runtime separately from modern builds.

### Universal CSF
Multi-runtime build/fork targeting VR/SE/AE where available.

### Runtime-specific CSF
DLL compiled only for one executable family.

## Custom skill authoring

### Skill global
GlobalVariable backing custom level/XP/perk points in some implementations.

### XP source
Gameplay action/script event that awards custom skill progress.

### Award XP
Script/native call increasing custom skill progress.

### Custom perk
PERK record used only/primarily by custom skill tree.

### Perk conditions
Ordinary perk conditions still control perk behavior after purchase.

### Menu-only state
Custom skill UI/progression metadata distinct from actual gameplay effects supplied by perks/spells/scripts.

### Skill reset
Framework operation clearing level/progress/perks according to design.

### Legendary reset
Return custom skill level to configured baseline and refund/adjust perk points.

### Skill cap
Maximum custom level.

### Curve
Formula/table determining XP required per custom skill level.

### Skill icon/art
UI assets/material used to render constellation/perk visuals.

## Compatibility patterns

### Shared custom skill
Multiple mods contribute XP/perks to one skill identifier.

### Skill namespace collision
Two mods accidentally use same config identifier/global/forms and interfere.

### Perk conflict
Custom perk edits conflict like ordinary PERK records.

### Save-persisted custom progression
Globals/quests/native serialization preserve custom skill state on established saves.

### Config migration
Changing skill IDs/form references/tree layout can invalidate old save/config assumptions.

### UI conflict
Custom Skills native menu/rendering can interact with UI/graphics frameworks.

## Diagnostic rules

1. Separate custom-skill UI/progression state from actual effects granted by perks.
2. Preserve stable skill IDs and form references across updates.
3. Existing saves can contain old custom skill globals/perks even after config changes.
4. Verify exact CSF runtime build; older 1.5.97 and modern/VR builds may be separate.
5. A perk appearing/purchasing correctly does not prove its gameplay Entry Point conditions work.
6. Validate JSON against current framework schema when menu fails to load.
7. Do not assume arbitrary vanilla skill ActorValue can be invented; CSF supplies its own abstraction rather than extending engine ActorValue enum directly.

## Sources

- Current Custom Skills Framework Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/41780
- Modern source: https://github.com/Exit-9B/CustomSkills
- Custom Skills wiki/schema documentation: https://github.com/Exit-9B/CustomSkills/wiki
- Papyrus API index for CSF: https://papyrus.bellcube.dev/skyrimse/source/custom-skills/
- 1.5.97 port lineage: https://github.com/Fuzzlesz/CustomSkills-1.5

## Dated snapshot

Custom Skills Framework Nexus version 3.2.0 was observed on 2026-09-24, updated 2026-09-03. Upstream GitHub release listings may lag Nexus; use installed file/version and source tag when debugging.
