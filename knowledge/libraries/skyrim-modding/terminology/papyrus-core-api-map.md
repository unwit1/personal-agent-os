# Skyrim Modding Terminology — Core Vanilla Papyrus API Map

Imported: 2026-09-24
Status: sourced frontier-deepening pass

This is a type-oriented retrieval map. The canonical Papyrus Index contains the full function/event signatures; this module explains where to look first.

## Global utility scripts

### Game
Global access to player, forms, quest/system operations, fast travel, camera/world functions and broad game state.

Representative functions:
- GetPlayer
- GetForm
- GetFormFromFile
- FindClosestReferenceOfType
- FindRandomReferenceOfType
- FastTravel
- EnableFastTravel
- GetCurrentCrosshairRef (SKSE extension in relevant source)
- GetModByName / GetLightModByName (SKSE)
- GetModCount
- GetRealHoursPassed
- IncrementStat / QueryStat

### Utility
Timing/random/system helpers.

Representative functions:
- Wait
- WaitMenuMode
- WaitGameTime
- RandomInt
- RandomFloat
- GetCurrentRealTime
- GetCurrentGameTime
- GetINIString/Int/Float/Bool where exposed by runtime source.

### Debug
Developer-facing logging/UI helper.

Representative functions:
- Trace
- TraceStack
- Notification
- MessageBox
- CenterOnCell / COC-style helpers where available
- StartScriptProfiling / StopScriptProfiling

### Math
Math helpers such as floor/ceil/trig/power where available in vanilla/SKSE source.

## Form

### Form
Base class for game forms.

Core operations:
- GetFormID
- GetName
- HasKeyword
- GetGoldValue
- GetWeight
- GetType
- RegisterForMenu
- RegisterForModEvent
- RegisterForAnimationEvent in appropriate derived contexts
- Unregister variants

Use Form when operation does not require a placed world reference.

## ObjectReference

### ObjectReference
World/runtime reference API.

Core categories:
- activation: Activate, BlockActivation;
- movement: MoveTo, TranslateTo, SplineTranslateTo;
- state: Enable, Disable, Delete, DeleteWhenAble;
- ownership: SetActorOwner, SetFactionOwner;
- locks: Lock, Unlock, IsLocked;
- inventory: AddItem, RemoveItem, RemoveAllItems, GetItemCount;
- linked refs: GetLinkedRef, SetLinkedRef;
- 3D/model: SetScale, GetScale, Is3DLoaded, PlayAnimation;
- position: GetPositionX/Y/Z, SetPosition, SetAngle;
- events: OnActivate, OnHit, OnLoad, OnUnload, OnTriggerEnter/Leave.

## Actor

### Actor
ObjectReference + combat/AI/equipment/magic/ActorValue behavior.

Core categories:
- ActorValues: GetActorValue, GetBaseActorValue, DamageActorValue, RestoreActorValue, ModActorValue, ForceActorValue, SetActorValue;
- AI: EvaluatePackage, StopCombat, StartCombat;
- equipment: EquipItem, UnequipItem, EquipSpell, UnequipSpell;
- spells/perks: AddSpell, RemoveSpell, HasSpell, AddPerk, RemovePerk, HasPerk;
- factions: AddToFaction, RemoveFromFaction, GetFactionRank;
- relationships: GetRelationshipRank, SetRelationshipRank;
- life state: Kill, Resurrect, IsDead, IsBleedingOut;
- race: GetRace, SetRace;
- teammate: SetPlayerTeammate;
- movement: SetPosition/MoveTo inherited, PathToReference helpers via frameworks.

## ActorBase

### ActorBase
NPC_/actor-base data rather than one placed actor.

Typical use:
- GetSex
- GetRace
- IsUnique
- essential/protected/AI/stat getters through vanilla/SKSE extensions;
- template/base identity queries.

Do not confuse changing ActorBase with modifying one existing Actor reference/save state.

## Quest

### Quest
Runtime quest state.

Core operations:
- Start
- Stop
- Reset
- IsRunning
- IsCompleted
- SetStage
- GetStage
- IsStageDone
- SetObjectiveDisplayed
- SetObjectiveCompleted
- SetObjectiveFailed
- GetNthAlias / GetAliasByName / GetAliases (current API source)
- SetCurrentStageID through extensions where present.

## Alias / ReferenceAlias / LocationAlias

### Alias
Base quest alias.

### ReferenceAlias
Holds one ObjectReference/Actor.

Core operations:
- GetReference / GetActorReference
- ForceRefTo
- Clear
- GetOwningQuest
- AddInventoryEventFilter
- RemoveInventoryEventFilter
- TryToEvaluatePackage / TryToMoveTo / related convenience functions where defined.

### LocationAlias
Holds one Location.

Core operations:
- GetLocation
- ForceLocationTo
- Clear

## Location

### Location
Semantic location hierarchy.

Operations:
- HasKeyword
- IsChild
- GetParent
- IsCleared
- SetCleared
- GetRefTypeAliveCount
- GetRefTypeDeadCount
- GetKeywordData / special extensions where available.

## Cell / WorldSpace

### Cell
Loaded/interior/exterior cell data.

Operations include:
- IsInterior
- GetWorldSpace
- IsAttached
- Reset
- ownership/location-related access via extensions.

### WorldSpace
Worldspace form for exterior world and map data.

## Faction

### Faction
Membership, crime and reaction state.

Core operations:
- GetReaction
- SetAlly
- SetEnemy
- GetCrimeGold
- ModCrimeGold
- PlayerPayCrimeGold
- GetStolenItemValueCrime
- GetStolenItemValueNoCrime.

## Magic forms

### Spell
Spell/ability/shout-like magic item form.

### MagicEffect
Effect definition.

### ActiveMagicEffect
One runtime application instance.

ActiveMagicEffect lifecycle:
- OnEffectStart
- OnEffectFinish
- GetCasterActor
- GetTargetActor
- Dispel
- RegisterForUpdate/event systems.

### Enchantment
Magic effect container applied to items.

### Potion
ALCH consumable.

### Ingredient
INGR.

## Equipment/items

### Weapon
WEAP form.

### Armor
ARMO.

### Ammo
AMMO.

### Book
BOOK.

### SoulGem
SLGM.

### Scroll
SCRL.

### Outfit
OTFT.

### ConstructibleObject
COBJ.

These are base-form APIs; runtime instance-specific data like temper/enchantment/poison lives on inventory ExtraData and often requires SKSE/native extensions.

## Lists and leveled forms

### FormList
FLST mutable list:
- AddForm
- GetAt
- GetSize
- HasForm
- Revert
- SKSE remove helpers.

### LeveledItem
LVLI.

### LeveledActor
LVLN.

### LeveledSpell
LVSP.

Vanilla APIs expose limited runtime list manipulation; xEdit/Synthesis/runtime distributor frameworks are often better for bulk authoring.

## UI/message/audio

### Message
Show message box/choices.

### MusicType
Add/Remove/Play/Stop-like music controls where available.

### Sound
Play sound and obtain instance IDs where supported.

### SoundCategory
Volume/pause/mute controls where exposed.

### ImageSpaceModifier
Apply/Remove/CrossFade.

### EffectShader
Play/Stop visual shader.

### VisualEffect
Play/Stop effect.

## World data

### Weather
GetClassification and weather transition-related operations.

### Race
Race flags/spells/body data querying.

### Keyword
Semantic tag form.

### EncounterZone
Encounter-level/reset metadata.

### Package
AI package form.

### Scene
Start/Stop/Pause/IsPlaying.

### Topic / TopicInfo
Dialogue form types with relatively limited direct Papyrus control compared with Quest/Scene.

## SKSE-added API families

Common SKSE script extensions add:
- form name/description/EditorID helpers;
- array utilities;
- menu registration;
- key/control registration;
- ModEvents;
- animation events;
- camera state events;
- node/NiNode updates;
- plugin/load-order queries;
- additional Actor/ObjectReference/Form methods.

Keep vanilla, SKSE, po3 Papyrus Extender, PapyrusUtil and JContainers sources distinct in documentation.

## API selection rules

1. Use base Form methods when no world reference is required.
2. Use ObjectReference for one placed instance.
3. Use ActorBase for NPC_ template/base data; Actor for runtime individual.
4. Use Quest/Alias rather than hard-coded reference lookups when quest architecture already provides identity.
5. Use ActiveMagicEffect for one effect instance; MagicEffect for definition.
6. Avoid script polling when engine exposes registration/event.
7. Inventory-instance ExtraData often requires SKSE/native API beyond vanilla base-form methods.
8. Always record source family for non-vanilla functions.

## Sources

- Papyrus Index vanilla source catalog: https://papyrus.bellcube.dev/skyrimse/source/vanilla/
- Creation Kit Wiki Papyrus: https://ck.uesp.net/wiki/Category:Scripting
- SKSE64 script/API source: https://github.com/ianpatt/skse64
