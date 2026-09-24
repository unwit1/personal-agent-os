# Skyrim Biped, Weapon, and Magic Engine Enum Catalog — xEdit 4.1.5f

Imported: 2026-09-24
Source: `TES5Edit/TES5Edit` tag `xedit-4.1.5f`
Source file: `Core/wbDefinitionsTES5.pas`
Source blob SHA: `8455d8b86440712de6e280f1e113572ffefbd11d`
Status: finite source-derived catalog

## Biped Object slots

Skyrim's Biped Object mask has 32 bits corresponding to slots **30 through 61**.

| Slot | xEdit default label | Source line |
|---:|---|---:|
| 30 | Head | 4143 |
| 31 | Hair | 4144 |
| 32 | Body | 4145 |
| 33 | Hands | 4146 |
| 34 | Forearms | 4147 |
| 35 | Amulet | 4148 |
| 36 | Ring | 4149 |
| 37 | Feet | 4150 |
| 38 | Calves | 4151 |
| 39 | Shield | 4152 |
| 40 | Tail | 4153 |
| 41 | LongHair | 4154 |
| 42 | Circlet | 4155 |
| 43 | Ears | 4156 |
| 44 | Unnamed | 4157 |
| 45 | Unnamed | 4158 |
| 46 | Unnamed | 4159 |
| 47 | Unnamed | 4160 |
| 48 | Unnamed | 4161 |
| 49 | Unnamed | 4162 |
| 50 | DecapitateHead | 4163 |
| 51 | Decapitate | 4164 |
| 52 | Unnamed | 4165 |
| 53 | Unnamed | 4166 |
| 54 | Unnamed | 4167 |
| 55 | Unnamed | 4168 |
| 56 | Unnamed | 4169 |
| 57 | Unnamed | 4170 |
| 58 | Unnamed | 4171 |
| 59 | Unnamed | 4172 |
| 60 | Unnamed | 4173 |
| 61 | FX01 | 4174 |

### Biped slot caveat

xEdit explicitly comments: **"When NAME is user defined these will be incorrect."** RACE records can define custom Biped Object names. Therefore:

- slot **numbers/bit positions** are the stable identity;
- labels such as "Head", "Body", or "FX01" are xEdit's/default race-oriented labels;
- custom races can rename the displayed purpose of the same numeric slot;
- compatibility patches should compare actual slot masks, not only human-readable labels.

### First Person Flags

The same 32-slot mask is used by `First Person Flags` in Biped Body Template data. A bit set at position 0 corresponds to slot 30, through bit 31 for slot 61.

## Weapon animation type

| ID | Type | Source line |
|---:|---|---:|
| 0 | HandToHandMelee | 4643 |
| 1 | OneHandSword | 4644 |
| 2 | OneHandDagger | 4645 |
| 3 | OneHandAxe | 4646 |
| 4 | OneHandMace | 4647 |
| 5 | TwoHandSword | 4648 |
| 6 | TwoHandAxe | 4649 |
| 7 | Bow | 4650 |
| 8 | Staff | 4651 |
| 9 | Crossbow | 4652 |

This enum is used by WEAP animation data and by some condition/perk schemas. It describes the engine's weapon animation family, not a specific HKX/OAR animation file.

## Magic cast type

| ID | Cast type | Source line |
|---:|---|---:|
| 0 | Constant Effect | 5627 |
| 1 | Fire and Forget | 5628 |
| 2 | Concentration | 5629 |
| 3 | Scroll | 5630 |

## Magic delivery / target type

| ID | Delivery | Source line |
|---:|---|---:|
| 0 | Self | 5634 |
| 1 | Touch | 5635 |
| 2 | Aimed | 5636 |
| 3 | Target Actor | 5637 |
| 4 | Target Location | 5638 |

### Cast type vs delivery

These are orthogonal:
- **Cast type** describes how the magic item is cast/maintained.
- **Delivery** describes where/how the effect is applied.

A Fire-and-Forget spell can still use different delivery modes such as Self, Aimed, Target Actor, or Target Location.

## Casting source

| ID | Source |
|---:|---|
| 0 | Left |
| 1 | Right |
| 2 | Voice |
| 3 | Instant |

This source enum is used in condition/evaluation contexts and should not be conflated with MagicEffect casting type.

## Crime type

| ID | Crime |
|---:|---|

xEdit additionally exposes `-1 = None` for this enum.

## Compatibility rules

1. Armor compatibility should reason over numeric Biped masks plus ARMA/RACE applicability, not just slot names.
2. Custom races can redefine displayed Biped Object names without changing the underlying 32-bit mask.
3. Weapon animation type affects behavior/animation selection but does not identify one OAR submod or behavior graph path.
4. Cast type, casting source, and delivery are separate enums.
5. Conditions can compare these enums through CTDA parameter types; inspect the parent function schema before interpreting the number.
