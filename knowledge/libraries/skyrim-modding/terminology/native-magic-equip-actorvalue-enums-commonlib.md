# Skyrim Native Magic, Equip, and ActorValue Modifier Enums — CommonLibSSE-NG

Imported: 2026-09-24
Status: finite reverse-engineered source catalog

## Sources

- `MagicSystem.h` blob `393296ad6d27c4598fc110740d8da4f481127d2e`
- `ActorValues.h` blob `52a148f31093afb031deb9b52909af631c127a3b`
- `BGSEquipSlot.h` blob `74f01f2e733fac891cd56a7195da85f598622d82`
- `BGSEquipType.h` blob `a7f51223b3fc3369fd2fafe53c0ba8c0f075694a`

Upstream: https://github.com/alandtse/CommonLibSSE-NG

## CannotCastReason

| Enum | Value |
|---|---:|
| `kOK` | `0` |
| `kMagicka` | `1` |
| `kPowerUsed` | `2` |
| `kRangedUnderWater` | `3` |
| `kMultipleCast` | `4` |
| `kItemCharge` | `5` |
| `kCastWhileShouting` | `6` |
| `kShoutWhileCasting` | `7` |
| `kShoutWhileRecovering` | `8` |
| `kCustomReasonNoStart` | `100` |

`CustomReasonNoStart = 100` is deliberately outside the contiguous low values.

## CastingSource

| Enum | Value |
|---|---:|
| `kLeftHand` | `0` |
| `kRightHand` | `1` |
| `kOther` | `2` |
| `kInstant` | `3` |
| `kNone` | `4` |

### Source naming caveat

CommonLib uses `kOther = 2`, while xEdit's condition-oriented casting-source display labels the corresponding slot as **Voice**. Preserve source context instead of assuming every API names the same numeric slot identically.

## CastingType

| Enum | Value |
|---|---:|
| `kConstantEffect` | `0` |
| `kFireAndForget` | `1` |
| `kConcentration` | `2` |
| `kScroll` | `3` |

## Delivery

| Enum | Value |
|---|---:|
| `kSelf` | `0` |
| `kTouch` | `1` |
| `kAimed` | `2` |
| `kTargetActor` | `3` |
| `kTargetLocation` | `4` |
| `kNone` | `5` |

## Magic sound IDs

| Enum | Value |
|---|---:|
| `kDrawSheatheLPM` | `0` |
| `kCharge` | `1` |
| `kReadyLoop` | `2` |
| `kRelease` | `3` |
| `kCastLoop` | `4` |
| `kHit` | `5` |

These identify magic-system sound phases such as charge, ready-loop, release, cast-loop and hit.

## SpellType

| Enum | Value |
|---|---:|
| `kSpell` | `0` |
| `kDisease` | `1` |
| `kPower` | `2` |
| `kLesserPower` | `3` |
| `kAbility` | `4` |
| `kPoison` | `5` |
| `kEnchantment` | `6` |
| `kPotion` | `7` |
| `kAlchemy` | `static_cast<std::underlying_type_t<SpellType>>(kPotion)` |
| `kWortCraft` | `8` |
| `kIngredient` | `static_cast<std::underlying_type_t<SpellType>>(kWortCraft)` |
| `kLeveledSpell` | `9` |
| `kAddiction` | `10` |
| `kVoicePower` | `11` |
| `kStaffEnchantment` | `12` |
| `kScroll` | `13` |

### Aliased spell types

Current source aliases:
- `Alchemy` to the same value as `Potion`;
- `Ingredient` to the same value as `WortCraft`.

Do not count aliased names as separate raw numeric spell types.

## WardState

| Enum | Value |
|---|---:|
| `kNone` | `0` |
| `kAbsorb` | `1` |
| `kBreak` | `2` |

## ActorValue modifier layers

| Modifier | ID |
|---|---:|
| `kPermanent` | `0` |
| `kTemporary` | `1` |
| `kDamage` | `2` |
| `kTotal` | `3` |

The engine tracks at least three modifier channels in CommonLib's ActorValue storage:

- **Permanent** — durable modifier layer;
- **Temporary** — transient modifier layer;
- **Damage** — damage/depletion layer.

### Base vs modifiers

An ActorValue's effective value is not just one float. Native code can have:
- base value;
- permanent modifier;
- temporary modifier;
- damage modifier;
- additional calculation/perk effects depending on the ActorValue.

This matters when a Papyrus/API function appears to “set” or “damage” the same stat through different channels.

## EquipSlot flags

| Flag | Bit |
|---|---|
| `kNone` | `0` |
| `kUseAllParents` | `1 << 0` |
| `kParentsOptional` | `1 << 1` |
| `kItemSlot` | `1 << 2` |

### Parent slots

`BGSEquipSlot` can contain parent slots plus flags controlling whether:
- all parents are used;
- parents are optional;
- the slot is an item slot.

An EQUP is therefore a graph of slot relationships, not only a string name.

## Equipped item type identifiers

| Type | ID |
|---|---:|
| `kSpell` | `24` |
| `kShield` | `25` |
| `kTorch` | `26` |

These values are native equipped-item categories and should not be confused with Biped Object slots or EQUP FormIDs.

## Compatibility rules

1. Keep CastingSource, CastingType, Delivery and SpellType separate.
2. Do not flatten aliased enum names into distinct numeric states.
3. ActorValue base/permanent/temporary/damage layers can produce different save/runtime behavior.
4. EQUP parent relationships can affect equip compatibility even if two items appear to share the same visible slot.
5. Biped Object slots, EQUP slots, equipped-item type IDs and Actor equipment hand slots are separate systems.
6. Compare current runtime/API names with plugin-schema display names before assuming a semantic mismatch.
