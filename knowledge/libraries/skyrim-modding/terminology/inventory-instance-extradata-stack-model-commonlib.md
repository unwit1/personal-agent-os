# Skyrim Inventory Instance and ExtraData Stack Model — CommonLibSSE-NG

Imported: 2026-09-24
Status: reverse-engineered source-derived architecture reference

## Sources

- `ExtraDataList.h` blob `4153db7b5510ce5f8033ad3ff9783e02e1306e5d`
- `InventoryEntryData.h` blob `f12a4f3ead03a08dbdafa1e2701e16c9169958c7`
- `InventoryChanges.h` blob `558d888b96a386b30ac49f2a2cf968082ab02d10`
- `ExtraContainerChanges.h` blob `ad28685d4ec1165d9afcc4afc30c50f4317c80b2`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## Three-layer inventory model

### Base object
`TESBoundObject*` — the shared WEAP, ARMO, BOOK, MISC, SLGM, etc. base form.

### InventoryEntryData
One inventory-entry record for a base object in a container. Current CommonLib stores:

- `object` — the base object;
- `extraLists` — a list of `ExtraDataList*` representing non-default/non-stackable instance groups;
- `countDelta` — runtime/container delta against base container contents.

### ExtraDataList
One per-stack/per-instance list of ExtraData nodes.

This is the level where two swords with the same base WEAP can differ because one is:
- tempered;
- enchanted;
- poisoned;
- favorited;
- worn;
- renamed;
- owned;
- uniquely identified.

## Container base inventory vs changes

### TESContainer base contents
A container/NPC base record can define initial inventory.

### InventoryChanges
Runtime structure overlays additions/removals/instance state on top of that base inventory.

Current `InventoryChanges::GetCount` demonstrates the model directly:

1. get the base container count;
2. find matching `InventoryEntryData`;
3. add its `countDelta`.

The live count is therefore not simply the count stored in the base container record.

## ExtraContainerChanges

`ExtraContainerChanges` is ExtraData type `kContainerChanges` and holds an `InventoryChanges*`.

A reference's inventory changes can therefore live as ExtraData attached to the container/reference.

## InventoryEntryData capabilities

Current CommonLib exposes methods to query:

- display name;
- enchantment;
- enchantment charge;
- favorite stack;
- owner;
- soul level;
- value;
- weight;
- enchanted state;
- favorited state;
- leveled-item state;
- poisoned state;
- worn state;
- left-hand worn state;
- ownership;
- quest-object state.

It also supports:
- adding ExtraDataLists;
- poisoning an item;
- setting worn state;
- normalizing/counting non-stackable lists;
- deep copying instance data.

## ExtraDataList capabilities

Current source exposes:

- `GetByType`;
- `HasType`;
- `Remove` / `RemoveByType`;
- `Add`;
- `GetCount`;
- `GetDisplayName`;
- `GetEncounterZone`;
- `GetLinkedRef`;
- `GetObjectHealth`;
- `GetOwner`;
- `GetSoulLevel`;
- `GetTeleportLinkedDoor`;
- `GetWorn`;
- `HasQuestObjectAlias`;
- `IsInventoryStackable`;
- setters for count, enchantment, extra flags, linked refs, names, owners and starting position.

## Stackability

### Stackable copy
Two copies can share one ordinary inventory count when they do not have differentiating ExtraData that requires separate instance treatment.

### Non-stackable ExtraDataList
An individual or subgroup carries ExtraData requiring separate handling.

Examples commonly include:
- different temper/health;
- different custom enchantment;
- different poison;
- worn vs unworn;
- custom name;
- unique ID;
- soul state.

### NormalizeAndCountNonStackableExtraLists
CommonLib exposes an InventoryEntryData method specifically for normalizing/counting those per-instance lists, reinforcing that one base object entry can contain multiple differentiated stacks.

## Count semantics

### Base count
Count on the actor/container's base TESContainer.

### countDelta
Net runtime change in `InventoryEntryData`.

### ExtraCount
Count stored on a particular ExtraDataList when an instance subgroup represents more than one identical copy.

These are three different layers. A debugging tool that reads only one can report the wrong live inventory count.

## Ownership

Ownership can be determined from:
- container/reference ownership;
- item ExtraData ownership;
- faction/actor ownership context.

`InventoryEntryData::IsOwnedBy` can evaluate ownership using both the test actor and explicit item owner context.

## Worn state

### ExtraWorn
Marks a stack as worn/equipped.

### ExtraWornLeft
Marks left-side worn/equipped state.

`InventoryEntryData::IsWorn(bool left)` and `SetWorn` operate at instance/list level.

This is separate from:
- base ARMO Biped slots;
- EQUP equip slot;
- Actor's currently selected/equipped form pointer.

## Enchantments

### Base enchantment
WEAP/ARMO form can point to a base ENCH.

### ExtraEnchantment
One item instance can carry a custom instance enchantment.

### ExtraCharge
Current charge is also per-instance data.

Therefore:
- `IsEnchanted()` must consider both base and instance state;
- comparing only WEAP/ARMO's EITM/ENCH field can miss a custom enchanted copy.

## Poison

`InventoryEntryData::PoisonObject` applies poison through instance state. Two otherwise identical weapons can therefore differ because only one stack has `ExtraPoison`.

## Display names

`ExtraDataList::GetDisplayName` and `SetOverrideName` expose the instance naming layer, typically involving `ExtraTextDisplayData`.

A renamed item is not a new base Form.

## Soul gems

`GetSoulLevel` reads instance soul state. Filled and empty copies can share the same base SLGM depending on design while differing in ExtraData.

## Quest items and aliases

`HasQuestObjectAlias` / `IsQuestObject` show that quest-item status can be affected by alias/runtime data, not only a simple base-form flag.

## Favorites/hotkeys

Favorite state is associated with a specific ExtraDataList/instance. `InventoryChanges::SetFavorite` and `RemoveFavorite` operate on an entry plus item ExtraData list.

## Unique IDs

`InventoryChanges::GetNextUniqueID` and `SetUniqueID` support tracking one inventory instance through operations.

Frameworks that need durable per-item identity should prefer proper unique/instance mechanisms rather than assuming base FormID uniquely identifies the physical item.

## Runtime layout boundary: AE 1.6.629+

Current CommonLib notes a binary-layout change:

- SE/VR `BaseExtraList` is non-virtual and stores data/presence directly;
- AE 1.6.629+ promoted its destructor to virtual, adding a vtable pointer and shifting members by 8 bytes.

Consequences:
- old native code using hard-coded offsets can corrupt memory on newer runtimes;
- CommonLib's runtime-aware accessors are necessary in multi-runtime code;
- "same class name" does not mean same ABI layout across all Skyrim versions.

## Presence bitfield

`BaseExtraList::PresenceBitfield` is 0x18 bytes and tracks whether ExtraData types are present.

A native implementation can therefore test type presence without walking the linked ExtraData chain every time.

## Inventory mutation functions

Current `InventoryChanges` supports:
- enchant object;
- generate leveled-list changes;
- get armor in slot;
- get item by inventory index;
- compute inventory/armor weight;
- get item count;
- obtain next unique ID;
- get worn mask;
- initialize base/leveled/outfit/script data;
- remove favorite;
- remove one item;
- remove all items;
- send container-changed events;
- set favorite;
- set unique ID;
- visit inventory/worn items.

## Common failure patterns

### Freshly spawned item works, old carried copy does not
Suspect instance ExtraData/save state before base-form conflict.

### Two identical-looking weapons have different damage/value
Compare temper/health, custom enchantment, poison and other instance data.

### Item won't stack
One or more ExtraDataLists differ in a way that makes the items non-stackable.

### Item won't equip
Inspect CannotWear, Worn/left state, equip-slot rules, quest/alias state and framework overrides.

### Item name keeps returning
External/runtime naming state or saved TextDisplayData may survive base-form changes.

### Inventory count disagrees between tools
One tool may be reading base container count while another reads countDelta/ExtraCount.

### Ownership/theft behavior differs for one copy
Inspect per-instance owner ExtraData and container ownership.

## Diagnostic rules

1. Always distinguish **base form**, **InventoryEntryData**, and **ExtraDataList**.
2. Base FormID is not enough to identify one physical inventory item.
3. Count comes from base container + runtime delta + per-stack ExtraCount semantics.
4. Instance enchantment/charge/poison/temper/name/soul/worn state can survive independently of later base-form edits.
5. Established-save bugs that affect only old copies strongly implicate instance/save data.
6. Native plugins must respect the runtime-specific ExtraDataList ABI.
7. When designing AI/automation around inventory, expose whether an action targets the base form, all matching stacks, or one unique instance.
8. Consequential operations such as removing/equipping/renaming an item should resolve the exact ExtraDataList when instance specificity matters.

## Related modules

- `extradata-type-catalog-commonlib.md`
- `ess-changeforms-savegame-internals.md`
- `plugin-record-schema-items-magic.md`
- `native-magic-equip-actorvalue-enums-commonlib.md`
## Native item-removal and soul-level enums

Sources:
- `include/RE/I/ItemRemoveReason.h` blob `b6fa5a9fbc76dbb162cfb7cd5b1b3e261965b840`
- `include/RE/S/SoulLevels.h` blob `b05abd11c7fda2d1f73c964a6c2a3776b90a7bbc`

### ITEM_REMOVE_REASON

| ID | Reason |
|---:|---|
| 0 | Remove |
| 1 | Steal |
| 2 | Selling |
| 3 | Dropping |
| 4 | Store In Container |
| 5 | Store In Teammate |

The removal reason is semantically meaningful: theft, selling, dropping and storage can trigger different crime, event, ownership, destination and UI behavior even when the same base item/count is removed.

### SOUL_LEVEL

| ID | Soul level |
|---:|---|
| 0 | None |
| 1 | Petty |
| 2 | Lesser |
| 3 | Common |
| 4 | Greater |
| 5 | Grand |

Soul level is instance-sensitive where `ExtraSoul` is present. A soul gem's base SLGM capacity/form and the soul actually stored in a particular inventory instance are separate pieces of state.

### Automation implications

When an agent or native framework manipulates inventory:
1. preserve the intended `ITEM_REMOVE_REASON` rather than treating every transfer as generic removal;
2. resolve the exact ExtraDataList when instance-specific state matters;
3. keep container destination and ownership semantics explicit;
4. never infer a filled soul gem's actual stored soul from the base form alone.

