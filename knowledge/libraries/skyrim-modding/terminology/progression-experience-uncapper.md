# Skyrim Modding Terminology — Experience, Leveling, Skill Caps, and Uncapper Systems

Imported: 2026-09-24
Status: sourced deep-ingestion pass 16

## Vanilla character progression

### Character XP
Progress toward next player level.

### Skill XP
Progress toward next level in one individual skill.

### Vanilla level contribution
In unmodified Skyrim, skill advancement contributes character-level XP according to engine formula.

### Level XP threshold
Experience required to advance player level.

### Level-up attribute
Health/Magicka/Stamina choice applied on level-up.

### Perk point
Point awarded/spent on perk trees.

### Skill cap
Maximum skill value allowed to advance normally.

### Formula cap
Maximum skill value used by game calculations even if displayed/actual skill can exceed it.

### Legendary skill
Vanilla mechanic resetting a maxed skill and refunding perk points to permit continued character progression.

## Experience mod

### Experience
SKSE plugin by zax changing character-level progression so XP is awarded for quests, exploration and optional kills instead of directly from ordinary skill increases.

### Native XP
Experience uses Skyrim's own character-level XP/progression rather than maintaining a completely separate secondary player-level system.

### Quest XP
Character XP awarded when qualifying quest objectives/quests complete.

### Exploration XP
Character XP awarded for discovering locations.

### Kill XP
Optional XP source from defeated enemies.

### Skill cap by player level
Experience can constrain skill progression relative to player level so removing skill->level XP does not let skills run arbitrarily ahead.

### Experience.ini
Configuration controlling XP awards/caps/multipliers/features.

### XP event
Framework-detected gameplay action resulting in character XP.

### Experience bar integration
Framework hooks vanilla/UI XP presentation so progression remains visible through standard/compatible HUDs.

### Quest classification
Rules determining XP value based on quest type/category/metadata.

### Location discovery classification
Rules assigning XP according to location type/importance.

### Experience addon
Mod supplying an additional XP source while using Experience's underlying character-XP system.

## Skyrim Skill Uncapper

### Skill Uncapper
Native SKSE framework changing engine skill caps, formula caps, XP gain multipliers, level contribution, perk gain, attributes and legendary-skill behavior.

### SkillCaps
INI section setting maximum actual level per skill.

### SkillFormulaCaps
INI section setting maximum skill value used by calculations.

### SkillExpGainMults
Multiplier applied to XP gained inside individual skills.

### PCLevelSkillExpMults
Multiplier controlling how skill increases contribute to player-level XP.

### PerksAtLevelUp
Configuration controlling perk points awarded by player level.

### AttributesAtLevelUp
Configuration controlling Health/Magicka/Stamina/carry weight gain.

### LegendarySettings
Configuration changing legendary-skill reset behavior.

### True skill level
Actual uncapped skill value.

### Effective skill level
Value formula is allowed to use after SkillFormulaCap.

### Display true skill
Uncapper patch ensuring UI can show values beyond vanilla cap.

### Enchanter cap
Special handling for enchantment calculations when Enchanting exceeds vanilla-supported assumptions.

### Uncapper preset
INI distribution configuring caps/curves for a particular gameplay overhaul.

### Uncapper version 2.x
Modern SE/AE continuation by Kasplat with current runtime fixes/features.

## Experience + Uncapper interaction

### Decoupled leveling
Experience removes/reduces skill gain as primary player-level source while Uncapper can still adjust skill progression/caps.

### Double XP modification
Both frameworks/addons alter same character XP or skill contribution values, causing unexpected leveling pace.

### Skill cap coordination
Experience level-based caps and Uncapper absolute/formula caps can both constrain one skill.

### Perk gain ownership
Only one intended system should define perk-points-per-level unless additive behavior is designed.

### Progression overhaul stack
Combination of Experience, Uncapper, custom skills, perk overhaul, leveling settings and add-ons; each must have clearly assigned responsibility.

## Modern alternatives

### Character Progression Control
2026 mod exposing many vanilla progression Game Settings/caps/formulas through MCM rather than requiring manual INI/native Uncapper configuration for every use case.

### Skill Caps and Presets
2026 MCM-oriented mod exposing skill and formula caps with presets.

### Gold-to-XP addon
Experience addon granting character XP according to gold earned.

### Custom Skills Framework
Separate framework creating entirely new progression trees rather than only altering vanilla 18 skills.

## Diagnostic rules

1. Distinguish character XP from skill XP.
2. Skill cap and formula cap are deliberately separate values.
3. When Experience is installed, do not assume skill gain directly levels character.
4. Audit which mod owns perk-point gain, attribute gain, skill XP, character XP and legendary reset.
5. Existing saves preserve current skill/player values; changing formulas does not retroactively reconstruct progression history.
6. UI displaying >100 does not prove downstream formulas use >100 if formula cap remains lower.
7. Exact native Uncapper/runtime version matters; old 2017 DLL guidance is not current compatibility guidance.

## Sources

- Experience current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/17751
- Skyrim Skill Uncapper for SE and AE: https://www.nexusmods.com/skyrimspecialedition/mods/82558
- Original SE Uncapper lineage: https://www.nexusmods.com/skyrimspecialedition/mods/8889
- Custom Skills Framework: https://github.com/Exit-9B/CustomSkills

## Dated snapshot

Experience 3.7.4 was current on Nexus as of 2026-09-24 (updated 2026-09-06). Skyrim Skill Uncapper for SE and AE 2.2.4 was current (updated 2026-09-07) with 1.7.x compatibility.
