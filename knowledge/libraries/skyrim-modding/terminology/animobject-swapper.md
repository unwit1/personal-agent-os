# Skyrim Modding Terminology — AnimObject Swapper

Imported: 2026-09-24
Status: sourced deep-ingestion pass 19

## AnimObjects

### AnimObject / ANIO
Game record used by an idle/animation to attach/display a temporary visual object such as bread, tankard, instrument or grindstone weapon.

### Animation object
Visual prop associated with animation execution. It is distinct from the animation clip itself.

### Idle AnimObject
ANIO referenced by an IDLE/behavior interaction during a particular animation.

### AnimObject base
Original ANIO the game/idle requests.

### AnimObject replacement
Alternative ANIO returned at runtime by framework.

### Prop model
NIF shown by ANIO.

### Prop attachment
Bone/node/socket where animation object is attached during idle.

## AnimObject Swapper / AOS

### AnimObject Swapper
SKSE framework by powerofthree that swaps ANIO forms at runtime using config files rather than static plugin patches.

### AOS
Community shorthand for AnimObject Swapper in this repository context; disambiguate from Audio Overhaul for Skyrim when needed.

### _ANIO.ini
Configuration suffix recognized by AnimObject Swapper.

### Original ID
FormID or EditorID of ANIO being replaced.

### Swap ID
FormID or EditorID of replacement ANIO.

### Multiple originals
One config rule can target multiple original AnimObjects.

### Multiple swaps
One original can map to several replacement ANIO forms.

### Random swap
Framework randomly selects among multiple eligible replacements each time relevant idle plays.

### Chance
Per-rule probability controlling whether replacement occurs.

### Conditional swap
Rule evaluated against actor/context before replacing object.

### Normal swap
Unconditional/default mapping used if no higher-priority conditional swap applies.

### Conditional precedence
Conditional rules take precedence over ordinary/unconditional swap rules.

### Actor filter
Condition based on actor base/form identity.

### Faction filter
Condition based on faction membership.

### Race filter
Condition based on actor race.

### Keyword filter
Condition based on actor/inventory/context keywords.

### Location filter
Condition based on current cell/location.

### Spell filter
Condition based on actor spell state.

### FormList filter
Condition using membership in configured FormList.

### Inventory filter
Condition checking objects carried by actor.

### Pattern filter
String/model/EditorID style partial matching supported by current filter grammar.

### Trait filter
Compact actor traits such as gender/child status.

### Male trait
M or equivalent include/exclude syntax.

### Female trait
F or equivalent include/exclude syntax.

### Child trait
C/-C age trait.

### Failed lookup
Config references unknown EditorID/FormID; current AOS logs failed lookups for diagnosis.

### po3_AnimObjectSwapper.log
Framework runtime log.

## Relationship to animation frameworks

### AOS vs OAR
OAR chooses which animation clip plays; AnimObject Swapper chooses which animation prop ANIO appears during the animation.

### AOS vs Base Object Swapper
BOS swaps placed-reference base forms; AnimObject Swapper swaps ANIO props requested by animation.

### AOS vs IED
IED persistently displays equipment/custom items on skeleton nodes; ANIO is temporary prop attached for animation interaction.

### AOS vs Payload Interpreter
Payload Interpreter executes commands at animation annotations; AOS substitutes visual prop when engine requests AnimObject.

### AOS vs behavior patch
Swapping ANIO does not create new behavior states/events.

## Use patterns

### Drink variation
Random tankard/cup/wine/ale props for drinking animations.

### Food variation
Different bread/food props for eating animations.

### Inventory-aware prop
Show prop matching item actually held/carried.

### Actor-specific prop
Unique NPC/player uses customized object.

### Location-specific prop
Use alternate prop according to location.

### Race/gender-specific prop
Prop varies by actor traits.

### Weapon-on-workbench prop
Swap grindstone/forge animation weapon prop to better match actual actor/equipment context.

## Failure modes

### Missing replacement ANIO
Config points to nonexistent form; can produce failed lookup and depending on framework/version potentially severe behavior.

### Bad replacement model
ANIO resolves but its NIF/path is missing/malformed.

### Prop/animation mismatch
Prop attaches correctly but animation hand position/scale expects another object.

### Duplicate AOS rule
Multiple configs target same ANIO/context.

### Stale filter
Config depends on plugin/EditorID changed by mod update.

### Merge remap
Merged plugin changes form identity; use MergeMapper/current supported identity methods where framework build supports it.

### Runtime mismatch
Native DLL does not support current Skyrim runtime.

## Diagnostic rules

1. If body animation is correct but held prop is wrong, inspect AnimObject Swapper rather than OAR/Pandora first.
2. If no prop appears, separate ANIO lookup from prop NIF/asset loading.
3. Check conditional rule precedence before assuming random selection failure.
4. Random swap occurs at idle/request lifecycle; do not expect persistent prop identity unless config/framework explicitly guarantees it.
5. EditorIDs should be unique to avoid ambiguous lookup.
6. Exact current runtime compatibility matters: AOS 2.0.0 changed supported AE runtime set.

## Sources

- AnimObject Swapper current Nexus: https://www.nexusmods.com/skyrimspecialedition/mods/75167
- AnimObject Swapper VR: https://www.nexusmods.com/skyrimspecialedition/mods/75455

## Dated snapshot

AnimObject Swapper 2.0.0 was current on 2026-09-24, updated 2026-09-20. Its page states support for SE 1.5.97, AE 1.6.1170 and AE 1.7.104+, while dropping 1.6.353/1.6.640 in 2.0.0. Treat runtime support as version-specific.
