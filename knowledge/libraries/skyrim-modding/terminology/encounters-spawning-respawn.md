# Skyrim Modding Terminology — Encounters, Spawning, Respawn, and Leveled Actors

Imported: 2026-09-24
Status: sourced deep-ingestion pass 20

## Spawn definitions

### Placed actor
ACHR reference explicitly placed in CK.

### Leveled actor reference
Placed marker/reference whose base resolves through LVLN to select an ActorBase.

### LeveledActor / LVLN
List of ActorBase/nested LVLN entries selected according to level/chance/flags.

### Spawn marker
Placed reference or leveled actor position where selected actor appears.

### Encounter
One or more actors/references intended to populate a combat/world scenario.

### Encounter group
Collection of actors/markers logically belonging to one encounter.

### Respawn flag
Actor/reference/base/cell behavior indicating content can return after reset.

### Starts Dead
Actor flag/state causing spawned actor to begin dead.

### Initially Disabled
Spawn reference exists but does not activate until enable state changes.

### Enable parent encounter
Group of enemies activated/deactivated together by marker/quest/state.

## Encounter Zones

### EncounterZone / ECZN
Record attached to cells/locations controlling encounter-level minimum/maximum, reset and ownership-related behavior.

### Encounter zone level
Effective level locked/calculated when zone is first visited.

### Minimum level
Floor applied to encounter actors/content.

### Maximum level
Ceiling where configured.

### Match PC Below Minimum
Encounter-zone option controlling player-level relation below zone minimum.

### Never Resets
ECZN flag preventing cells/content in that zone from ordinary reset.

### Locked encounter level
CK documentation notes encounter-zone level does not reset once established.

### Initial encounter zone
Actor carries initial EncounterZone association even if it travels away/pursues player.

## Leveled actor selection

### Calculate from all levels <= player
LVLN selection includes all qualifying entries rather than closest appropriate level.

### Use All
List spawns/uses all entries instead of selecting one where list type supports it.

### Chance None
Probability that no actor is selected.

### Nested LVLN
Leveled actor list references another leveled actor list.

### Encounter level input
Player/zone/reference level context used to select LVLN entry.

### Leveled Actor Base
Runtime ActorBase actually selected from LVLN for one spawned reference.

### GetLeveledActorBase
Papyrus/API query returning resolved actor base.

### Template leveled actor
Selected NPC_ can itself inherit from templates.

## Respawn/reset

### Cell reset
Engine reinitialization occurring after reset interval and when player reenters eligible cell.

### Cleared location interval
Longer/alternate reset timing applied to cleared locations.

### Uncleared interval
Default reset interval for non-cleared cell/location.

### Respawned actor
New/reset actor state generated when cell resets.

### Unique actor
Unique persistent NPC generally should not be treated like disposable respawning encounter actor.

### Boss
Actor/reference tagged with Boss LocationRefType, contributing to location clear state.

### Location cleared
State set when all bosses die or script sets cleared.

### RefType alive count
Location API counting living references with given LocationRefType.

### RefType dead count
Location API counting dead references with LocationRefType.

### Dead-count gate
Quest/location logic waits for all required encounter actors to die.

### Cleanup
Dead temporary actors/references may be removed during reset/cleanup.

## Hold-position encounters

### Hold Position actor
Leveled/placed enemy with package constraining it to radius/marker until release.

### Hold Position marker
XMarker/XMarkerHeading center used by package.

### LinkCustom02
Common named linked-ref convention used by vanilla HoldPosition packages.

### UntilReleased
Package variant checking actor variable such as Variable06 to stop holding position after script/event.

### Release trigger
Script sets actor variable/quest state causing actor to pursue normally.

## Dynamic spawning

### PlaceAtMe spawn
Script creates actor/reference at runtime from base form.

### Leveled PlaceAtMe
Spawn using resolved LVLN/base combination.

### Spawn count
Number of created actors.

### Spawn radius
Distance/randomized placement around source.

### Spawn budget
Design/performance limit for simultaneously active spawned actors.

### Spawn persistence
Placed persistent vs temporary created actors have different save/cleanup behavior.

### Encounter manager
Quest/native system tracking created encounters and despawning/resetting them.

### Random encounter
Story Manager/world-interaction system dynamically selecting event/NPCs while player travels.

### World Interaction
Vanilla encounter/event quest family spawning/using actors according to Story Manager/location/travel context.

## Common failure modes

### Empty encounter
Chance None/filter/enable state/list target produces no actor.

### Underleveled encounter
Zone/list minimum/selection logic not as intended.

### Overleveled encounter
Minimum/zone/template/list interaction produces stronger actor than expected.

### Won't respawn
ECZN Never Resets, persistent/unique state, quest alias, player never stayed away long enough, or cell not reentered after interval.

### Duplicate spawn
Script spawn runs repeatedly without tracking created reference.

### Spawn leak
Created actors persist indefinitely and increase save/reference count.

### Encounter never clears
Boss LocRefType/dead-count condition wrong, actor escaped/disabled rather than killed, or location clear script never runs.

### Pursuit past encounter
Hold Position release/package condition or combat pursuit overrides intended radius.

## Diagnostic rules

1. Inspect ECZN and LVLN separately: zone sets level/reset context, list supplies candidate actors.
2. Cell reset only occurs when player returns after eligible interval.
3. Never Resets is an EncounterZone property.
4. Quest aliases protect some references from ordinary reset.
5. Dynamic PlaceAtMe spawns need explicit cleanup/persistence strategy.
6. Location clear depends on Boss RefTypes or scripts, not simply "all enemies in cell."
7. Unique/story NPCs should not be built as disposable leveled respawns.

## Sources

- Creation Kit Wiki Cell Reset: https://ck.uesp.net/wiki/Cell_Reset
- Creation Kit Wiki HoldPosition Package Template: https://ck.uesp.net/wiki/HoldPosition_%28Package_Template%29
- Creation Kit Wiki Location/Papyrus APIs: https://ck.uesp.net/wiki/Category:Scripting
- Tome of xEdit record definitions/reference for LVLN/ECZN
