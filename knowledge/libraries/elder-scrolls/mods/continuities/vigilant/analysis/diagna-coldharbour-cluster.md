# Order of Diagna cluster in VIGILANT

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

## Scope

This pass compares three distinct Diagna-linked implementations:

1. **Gaiden Shinji**
2. **Aredhel**
3. **Judo of the Order of Diagna**

The ESM supports a shared Coldharbour Diagna cluster, but not one linear questline.

## Gaiden Shinji

Gaiden is the narrative center of the cluster.

He is:
- a persistent named Redguard NPC in the Coldharbour Arena;
- given unique dialogue and follower-related machinery;
- searching for a sword lost when Yokuda sank;
- personally interested in Diagna;
- the person who says he gave Aredhel a sword and armor.

His lost sword remains unidentified.

## Aredhel

The later Aredhel:
- appears in St. Dulsa's Charnel;
- belongs to `QUST 02052F4A` / **Pitier**;
- carries `WEAP 0205049D` / **Aredhel's Sword**;
- wears `OTFT 024FC4B1` / `zzzCHOutfitAredhel`.

That outfit contains the **Blade of Diagna** set:

- `024FC4A5` — Blade of Diagna Boots
- `024FC4A6` — Blade of Diagna Armor
- `024FC4A7` — Blade of Diagna Gauntlets
- `024FC4A8` — Blade of Diagna Helmet

This corrects an earlier assumption that Aredhel wore the Knight of Diagna set.

Gaiden's statement that he gave Aredhel sword and armor is still strongly consistent with Aredhel's player-facing Diagna equipment.

## Judo of the Order of Diagna

`NPC_ 0251653B` / **Judo of the Order of Diagna** is structurally different.

He:
- templates from `NPC_ 025177A1` / **Soul-Shriven**;
- belongs to `FACT 025738DF` / **Soul-Shriven**;
- has `SPEL 0251651F` / **Soul Shriven abilities**;
- is instantiated through a Soul-Shriven trigger in the Arena District;
- participates in `QUST 0251532C` / **Feral Soul-Shriven**;
- has no unique INFO dialogue found in the ESM.

The trigger's `SvBase` property points directly to Judo's NPC base.

Judo is therefore a named Soul-Shriven enemy variant, not a second Gaiden-style story NPC.

## Feral Soul-Shriven context

Judo is part of a much larger `zzzCHRqShriven*` system containing more than thirty named variants.

The generic trigger base:
- `ACTI 0251532D` / **Soul-Shriven**

uses:
- `CHRqSoulShrivenTRGScript`

and references:
- `QUST 0251532C` / **Feral Soul-Shriven**.

Individual placed triggers supply a different `SvBase` NPC.

Judo's trigger:
- `REFR 0251778B`

is in:
- `CELL 0206DD87` / `CHCityColosseum03`
- `LCTN 02385D96` / **Arena District**

and supplies Judo as its Soul-Shriven base.

This makes his presence part of Coldharbour's radiant Soul-Shriven encounter ecology.

## Two separate Diagna armor sets

### Knight of Diagna

Judo uses:
- `OTFT 0204F0A8` / `zzzCHOutfitRenald`

containing:

- `0204F0A3` — Knight of Diagna Boots
- `0204F0A4` — Knight of Diagna Armor
- `0204F0A5` — Knight of Diagna Gauntlets
- `0204F0A6` — Knight of Diagna Helmet

These records retain the old internal `Renald` naming family.

### Blade of Diagna

Aredhel uses:
- `OTFT 024FC4B1` / `zzzCHOutfitAredhel`

containing the separate Blade of Diagna set.

Therefore:

**Judo = Knight of Diagna set**  
**Aredhel = Blade of Diagna set**

## Akaviri Black Katana

Judo carries two:

- `WEAP 02052F59` / **Akaviri Black Katana**

The weapon's internal EditorID is:

- `zzzCHRenaldSwordPlayable`

so the legacy Renald asset family was reused for Judo.

This does not make the weapon Gaiden's missing sword.

Gaiden says:
- his lost sword disappeared with Yokuda;
- it may be connected to Diagna;
- he has found no trace of it.

The Judo weapon is explicitly **Akaviri** and receives no dialogue connection to Gaiden's search.

## Crafting conditions

The four **Knight of Diagna** armor recipes:

- `021A4BB3`
- `021A4BB4`
- `021A4BB5`
- `021A4BB6`

contain an OR-condition chain:

1. `GetDeadCount(Judo) > 0`
2. OR `GetQuestCompleted(Pitier) == 1`

So the Knight set becomes craftable through either:
- defeating Judo;
- or completing Aredhel's Pitier quest.

The **Blade of Diagna** recipes:

- `024FC4AA`
- `024FC4AB`
- `024FC4AC`
- `024FC4AD`

use:
- `GetQuestCompleted(Pitier) == 1`

without a Judo-death condition.

The playable **Akaviri Black Katana** recipe `021A4BB7` is likewise gated by Pitier completion.

This creates a strong gameplay-system bridge among Judo, Aredhel, and the shared old Renald asset family.

It is not evidence that Judo and Aredhel are the same person.

## Relationship to Gaiden

No direct ESM relationship was found between:
- Gaiden and Judo;
- Judo and Gaiden's lost sword.

The strongest supported relations are:

- `Gaiden --gives sword/armor to--> Aredhel` — character testimony
- `Aredhel --wears--> Blade of Diagna` — structural
- `Judo --identified_as--> Order of Diagna` — structural display name
- `Judo --is--> Soul-Shriven variant` — structural
- `Judo --wears--> Knight of Diagna` — structural
- `Judo death --unlocks crafting of--> Knight of Diagna` — structural/gameplay
- `Pitier completion --unlocks--> both Diagna equipment families` — structural/gameplay
- `Gaiden lost sword == Akaviri Black Katana` — unsupported

## Interpretation

VIGILANT distributes the Order of Diagna tradition across several different narrative functions:

- **Gaiden** — historical hero acting in present Coldharbour
- **Aredhel** — outsider equipped by Gaiden and using Blade of Diagna gear
- **Judo** — named Order member reduced to a Soul-Shriven encounter
- **crafting system** — mechanically links Judo and Aredhel's encounters

That is enough to define a **Diagna Coldharbour cluster**, but not enough to claim that all three belonged to one historical unit or pursued the same mission.

## Open questions

Still unresolved:
- Gaiden's lost Yokudan sword;
- whether Judo represents a literal historical Order member or a Coldharbour-composed Soul-Shriven identity;
- why the old Renald asset family was split between Judo's Knight gear and Aredhel's separate Blade gear;
- whether external Papyrus supplies any unique Soul-Shriven behavior or lore for Judo.
