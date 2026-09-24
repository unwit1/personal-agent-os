# Skyrim Modding Terminology — Globals, FormLists, Keywords, Default Objects, and Core Data Primitives

Imported: 2026-09-24
Status: sourced deep-ingestion pass 24

## GlobalVariable

### GlobalVariable / GLOB
Named numeric value stored in plugin/game state and readable by conditions/Papyrus.

### Global value
Floating-point value underlying GLOB.

### Short global
Global configured/displayed as integer-like short value.

### Long global
Global configured/displayed as larger integer-like value.

### Float global
Ordinary floating-point global.

### Constant global
Global intended not to be changed through normal gameplay/scripts.

### GetValue
Papyrus function reading global as Float.

### GetValueInt
SKSE/helper reading integer representation where supported.

### SetValue
Changes runtime/save value.

### Mod
Adds delta.

### GameHour
Vanilla global representing current hour, engine-managed.

### Quest global
Global used as shared progression/state variable across conditions/scripts.

### Settings global
Global used as user/gameplay configuration value.

### Saved global state
Runtime changes to GlobalVariable can be persisted in save, so plugin default may not overwrite established-save value.

### Reset global
Explicit script/debug action returning global to desired default; plugin update alone may not.

## FormList

### FormList / FLST
Ordered collection of forms.

### AddForm
Adds form at runtime.

### RemoveAddedForm
Removes runtime-added form supported by SKSE/runtime.

### Revert
Restores list toward plugin-defined state where API supports it.

### GetAt
Returns form at index.

### GetSize
Returns number of entries.

### HasForm
Tests membership.

### Static entry
Form stored in plugin record.

### Runtime-added entry
Form inserted after load by script/FLM/native framework.

### List order
Index order can matter when scripts pair two FormLists by corresponding positions.

### Parallel FormLists
Two lists whose indices are semantically paired; inserting one entry without matching other list breaks mapping.

### Nested list
FormList containing another FormList as form; ordinary APIs/conditions may or may not recursively expand it.

### FormList mutation conflict
Multiple scripts/runtime frameworks add/remove values; xEdit only shows initial static list.

### FLM
FormList Manipulator runtime framework declaratively adding/removing forms from lists.

## Keyword

### Keyword / KYWD
Semantic tag form assigned to many record types.

### Keyworded form
Form containing keyword array.

### HasKeyword
Tests presence.

### Keyword Item Distributor
KID adds/removes keywords at runtime according to configs.

### Runtime keyword
Keyword assignment exists only after KID/SkyPatcher/etc. processing.

### Semantic keyword
Tag meant to describe gameplay category, e.g. ActorTypeUndead.

### Framework keyword
Tag invented by compatibility framework to provide standardized classification.

### UI keyword
Tag primarily consumed by interface categories/icons.

### Behavior keyword
Tag consumed by conditions/perks/scripts/gameplay.

### Keyword collision
Different mods reuse similarly named/conceptual keyword with incompatible semantics.

### Keyword namespace
Author prefix/convention reducing EditorID collision.

## Default Objects

### Default Object
Engine-defined slot/key pointing to a form used by hard-coded systems.

### DefaultObjectManager
Form/script interface exposing default-object slots.

### Key
Four-character identifier such as GOLD, LKPK, PFAC, DFTS, DFMS.

### GetForm
Returns form currently assigned to default-object key.

### SetForm
Changes default-object mapping at runtime.

### Hard-coded slot
Engine knows semantic meaning of the slot; authors cannot create arbitrary new native Default Object categories.

### Remappable target
Form assigned to a known slot can be changed, altering hard-coded system behavior.

### Default keyword
Default Object slot points to a KYWD used by hard-coded category/system.

### Default faction
Slot points to Player/Guard/etc. faction.

### Default music
Slots point to battle/death/level-up music types.

### Default footstep set
DFTS default slot.

### Crafting default object
Slots mapping material/category keywords to hard-coded crafting menu category labels.

## Game Settings

### Game Setting / GMST
Named engine-config value stored as plugin data.

### String GMST
Text value.

### Float GMST
Numeric float value.

### Integer GMST
Integer-like numeric value.

### Boolean GMST
Boolean-like setting.

### s-prefix
Convention for string Game Settings.

### f-prefix
Float setting convention.

### i-prefix
Integer convention.

### b-prefix
Boolean convention.

### Hard-coded Game Setting name
Engine references known GMST keys; adding a random new GMST doesn't automatically create new engine behavior.

### GMST override
Plugin edits one setting; last static override wins unless runtime code later changes behavior.

## Message

### Message / MESG
UI/text record used for notification/message boxes/buttons.

### Message box
Modal choice UI from MESG.

### Notification
Short HUD text.

### Button
Choice entry in message box.

### Show
Papyrus call displaying Message and returning selected option where applicable.

### Dynamic substitution
Message text can use configured format/substitution tokens according to engine/Papyrus behavior.

## Form

### Form
Base Papyrus/native abstraction for any game data form.

### FormType
Engine enum identifying record/class family.

### IsPlayable
Property for forms eligible for ordinary player use where applicable.

### RegisterForModEvent
Form-based Papyrus registration to SKSE mod event.

### RegisterForMenu
Registration for UI menu open/close events.

### RegisterForAnimationEvent
Registration for actor/reference animation events.

## Default data-pattern rules

1. Globals are shared numeric state, not a substitute for complex structured save data.
2. FormLists are ordered mutable collections; index-based pairing is fragile.
3. Runtime KID/FLM/SkyPatcher changes make static xEdit view incomplete.
4. Default Objects are hard-coded semantic slots; their targets can change, but arbitrary slots cannot be invented through CK.
5. Game Settings are hard-coded by key; creating new keys does not extend engine code.
6. Preserve keyword namespace/meaning when designing interoperability frameworks.
7. Established saves can preserve changed Globals and runtime-driven state differently from plugin defaults.

## Sources

- DefaultObjectManager Script: https://ck.uesp.net/wiki/DefaultObjectManager_Script
- Customizing Crafting Categories: https://ck.uesp.net/wiki/Customizing_Crafting_Categories
- Creation Kit Wiki scripting type/API index: https://ck.uesp.net/wiki/Category:Scripting
- FormList Manipulator: https://github.com/MaskedRPGFan/FormList-Manipulator
