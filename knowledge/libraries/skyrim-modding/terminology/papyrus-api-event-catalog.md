# Skyrim Modding Reference — Papyrus Script Objects, Events, and Native API Families

Imported: 2026-09-24
Status: broad reference catalog

The CK Wiki scripting corpus contains well over a thousand pages. This catalog organizes the major object/event families so Agent OS can retrieve the right API documentation on demand instead of trying to memorize every function signature.

## Core language/value types

### Bool
Boolean true/false value.

### Int
Signed integer Papyrus value.

### Float
Floating-point numeric value.

### String
Papyrus string.

### Var
Dynamically typed Papyrus value added/used by supported Skyrim Papyrus versions/extensions.

### None
Null/no-object value.

### Array
Fixed-length Papyrus collection of one element type after creation, with SKSE/framework extensions offering richer resizing/containers.

### Struct
Papyrus structured value available in newer Bethesda Papyrus dialects/tooling contexts; Skyrim-specific compiler/runtime support must be checked before assuming Fallout 4 examples apply.

## Base object classes

### Form
Base Papyrus object for game forms; exposes identity/keywords/events/update registration and common functionality.

### ObjectReference
Papyrus object for placed/runtime world references.

### Actor
ObjectReference subclass for living/actor references.

### ActorBase
NPC base-form script object.

### Quest
Quest form API: start/stop/stages/objectives/aliases.

### Alias
Base quest-alias script object.

### ReferenceAlias
Alias resolving one reference.

### LocationAlias
Alias resolving one Location.

### RefCollectionAlias
Alias holding a collection of references.

### ActiveMagicEffect
Runtime instance API for a magic effect applied to a target.

## Form script objects

### Ammo
Ammo base form.

### Armor
ARMO form API including biped slot-mask helpers through SKSE.

### ArmorAddon
ARMA form API through SKSE extensions.

### Book
Book form API.

### Cell
CELL API including reset/ownership/location queries.

### Class
Class form API.

### ColorForm
Color data form exposed by SKSE.

### CombatStyle
Combat-style form API.

### ConstructibleObject
COBJ recipe API through SKSE.

### Container
Container base form.

### Door
Door base/object API where exposed through generic/reference relationships.

### Enchantment
ENCH API.

### EncounterZone
ECZN form API.

### Explosion
Explosion form object.

### Faction
Faction API for rank, crime, relations and player state.

### Flora
Flora base-form API.

### FormList
List-form API AddForm/Find/GetAt/GetSize/Revert and SKSE extensions.

### Furniture
Furniture form API.

### GlobalVariable
Numeric global form GetValue/SetValue and related.

### Hazard
Hazard form object.

### HeadPart
Head-part API extended by SKSE.

### Idle
Idle animation form.

### ImageSpaceModifier
Apply/remove/crossfade post-processing modifier API.

### ImpactDataSet
Impact dataset form.

### Ingredient
Ingredient/alchemy form.

### Key
Key form.

### Keyword
Keyword form; SKSE exposes lookup/manipulation helpers.

### LeveledActor
Leveled-character list API including runtime AddForm/Revert.

### LeveledItem
Leveled-item list API.

### LeveledSpell
Leveled-spell list API.

### Light
Light form API.

### Location
Location hierarchy/ref-type API.

### LocationRefType
LCRT form.

### MagicEffect
Magic-effect base form.

### Message
Message/notification/menu form API.

### MiscObject
Misc inventory item.

### MovableStatic
MSTT form.

### MusicType
Music add/remove API.

### Outfit
Outfit form exposed by SKSE.

### Package
AI package form.

### Perk
Perk form.

### Potion
ALCH/injestible form API.

### Projectile
Projectile form object.

### Race
Race API and SKSE flag/head data extensions.

### Scene
Scene start/stop/state API.

### Scroll
Scroll cast API.

### Shout
Shout form.

### SoulGem
Soul-gem API through SKSE.

### Sound
Playable sound object/instance API.

### SoundCategory
Mixer category pause/unpause/volume API.

### SoundDescriptor
SKSE-accessible sound descriptor data.

### Spell
Spell cast/effect/cost API and SKSE extensions.

### Static
Static base form.

### TalkingActivator
Talking activator base.

### Topic
Dialogue topic API including Add/Say style behaviors.

### TopicInfo
Dialogue INFO form exposed through newer/SKSE APIs where available.

### TreeObject
Tree form name used by SKSE Papyrus object.

### VoiceType
Voice-type form.

### Weapon
WEAP API including SKSE data access.

### Weather
Weather forcing/release/current APIs.

### WordOfPower
Word form.

### WorldSpace
Worldspace form API.

## Utility namespaces

### Game
Global game functions: player/forms/settings/save/menu/world queries, skill advancement and more.

### Utility
Wait/random/time/array helpers.

### Debug
Trace, notification, message box, profiling and developer commands.

### Math
Numeric functions and SKSE extensions.

### Input
SKSE input key/control queries and simulation.

### UI
SKSE Scaleform/menu variable/invoke APIs.

### UICallback
SKSE callback object for batching/typed UI invocations.

### ModEvent
SKSE custom event creation/sending API.

### NetImmerse
SKSE node-transform/scene-graph access lineage.

### WornObject
SKSE functions operating on equipped object instances.

### StringUtil
SKSE string manipulation.

### ColorComponent
SKSE color-channel helpers.

### DefaultObjectManager
SKSE access to engine default-object slots.

## Major event families

### OnInit
Instance initialization.

### OnLoad / OnUnload
Reference 3D/load lifecycle.

### OnCellAttach / OnCellDetach
Reference attaches/detaches from loaded cell.

### OnCellLoad
Cell/reference cell load event.

### OnActivate
Reference activated.

### OnTrigger / OnTriggerEnter / OnTriggerLeave
Trigger collision events.

### OnHit
Reference/actor hit event with attacker/source/projectile/attack flags.

### OnDeath / OnDying
Actor death lifecycle.

### OnCombatStateChanged
Actor combat-state transition.

### OnPackageStart / OnPackageChange / OnPackageEnd
AI package lifecycle.

### OnItemAdded / OnItemRemoved
Container/reference inventory changes.

### OnEquipped / OnUnequipped
Object reference/item equip lifecycle.

### OnObjectEquipped / OnObjectUnequipped
Actor-level equipment events.

### OnMagicEffectApply
Reference receives magic effect.

### OnEffectStart / OnEffectFinish
ActiveMagicEffect lifecycle.

### OnAnimationEvent
SKSE/vanilla animation event registration callback.

### OnUpdate
Real-time registered update.

### OnUpdateGameTime
Game-time registered update.

### OnLocationChange
Actor/reference location changed.

### OnMenuOpen / OnMenuClose
SKSE menu registration callbacks.

### OnKeyDown / OnKeyUp
SKSE input events.

### OnPlayerLoadGame
Player alias/script event used for update/migration logic.

### OnRaceSwitchComplete
Actor race-change completion.

### OnTranslationComplete / OnTranslationFailed / OnTranslationAlmostComplete
ObjectReference TranslateTo movement lifecycle.

### OnTrackedStatsEvent
Tracked stat change callback.

### OnSleepStart / OnSleepStop
Player sleep lifecycle.

### OnWardHit
Ward-related hit callback.

## Story events exposed to Papyrus

### OnStoryActivateActor
Story Manager actor activation event.

### OnStoryAddToPlayer
Item added to player story event.

### OnStoryArrest
Arrest event.

### OnStoryAssaultActor
Assault event.

### OnStoryBribeNPC
Bribe event.

### OnStoryCastMagic
Magic-casting event.

### OnStoryChangeLocation
Location-change Story Manager event.

### OnStoryCraftItem
Crafting event.

### OnStoryCrimeGold
Crime-gold event.

### OnStoryCure
Disease/cure story event.

### OnStoryDialogue
Dialogue event.

### OnStoryDiscoverDeadBody
Dead-body discovery.

### OnStoryEscapeJail
Escape-jail event.

### OnStoryFlatterNPC
Flattery event.

### OnStoryHello
Hello/greeting event.

### OnStoryIncreaseLevel
Level-up event.

### OnStoryIncreaseSkill
Skill-increase event.

### OnStoryInfection
Infection event.

### OnStoryIntimidateNPC
Intimidation event.

### OnStoryJail
Jail event.

### OnStoryKillActor
Kill-actor event.

### OnStoryNewVoicePower
Voice/shout acquisition event.

### OnStoryPayFine
Fine payment event.

### OnStoryPickLock
Lock-pick event.

### OnStoryPlayerGetsFavor
Favor event.

### OnStoryRelationshipChange
Relationship rank/state change event.

### OnStoryRemoveFromPlayer
Item removed from player event.

### OnStoryScript
Script-generated Story Manager event.

### OnStoryServedTime
Jail sentence served.

### OnStoryTrespass
Trespass event.

## High-risk API families

### Delete / DeleteWhenAble
Removes runtime references; misuse can create persistence/reference problems.

### PlaceAtMe
Creates runtime references that can contribute save state and lifecycle complexity.

### ForceActorValue
Persistent-feeling AV manipulation easily misused compared with effects/damage/restore semantics.

### Reset
Cell/reference/quest reset APIs have subsystem-specific effects and are not universal repair tools.

### SetRace
Major actor state/appearance change requiring lifecycle/FaceGen/skeleton consideration.

### SetMotionType
Changes Havok motion state and can affect saved reference physics.

### RegisterForUpdate
Persistent repeating work can cause script pressure if never unregistered.

### SendAnimationEvent
Drives graph events; event name must exist/mean what expected for active behavior graph.

### Game.SetINI*
Runtime INI modifications may not affect every cached setting and can persist outside mod intent.

## API retrieval rules

1. Resolve object type before suggesting functions.
2. Check vanilla CK Wiki signature first, then current SKSE/framework extensions.
3. Record whether function is native, latent, global, tasklet-safe or version-specific when relevant.
4. Do not infer Fallout 4/Starfield Papyrus features exist in Skyrim.
5. Event availability depends on host type and registration/lifecycle.
6. Prefer native events/conditions over polling where equivalent.
7. Treat object-creation/deletion/reset APIs as persistent-state operations.
8. Compile-time PSC availability and runtime native implementation are separate.
9. When documentation is ambiguous, inspect source/game behavior and save/load lifecycle.
10. Add newly validated APIs to focused subsystem modules rather than bloating this catalog with every function page.

## Sources
- Creation Kit Wiki scripting corpus: https://ck.uesp.net/wiki/Category:Scripting
- Creation Kit Wiki SKSE Script Objects: https://ck.uesp.net/wiki/Category:SKSE_Script_Objects
- SKSE source: https://github.com/ianpatt/skse64
- powerofthree Papyrus Extender: https://github.com/powerof3/PapyrusExtenderSSE
