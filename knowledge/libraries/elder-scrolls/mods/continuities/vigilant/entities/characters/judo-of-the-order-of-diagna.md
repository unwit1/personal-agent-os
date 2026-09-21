# Judo of the Order of Diagna — VIGILANT continuity

- Continuity: `tes.mod.vigilant`
- NPC: `NPC_ 0251653B` / `zzzCHRqShrivenDiagna` — **Judo of the Order of Diagna**
- Race: master-game Redguard race
- Template: `NPC_ 025177A1` / `zzzCHRqShriven00Template` — **Soul-Shriven**
- Faction: `FACT 025738DF` / **Soul-Shriven**
- Ability: `SPEL 0251651F` / **Soul Shriven abilities**
- Death list: `LVLI 025177A2` / `zzzCHDeathItemRqShriven`
- Outfit: `OTFT 0204F0A8` / `zzzCHOutfitRenald`
- Weapons: two `WEAP 02052F59` / **Akaviri Black Katana**
- Encounter system: `QUST 0251532C` / **Feral Soul-Shriven**
- Trigger reference: `REFR 0251778B`
- Trigger cell: `CELL 0206DD87` / `CHCityColosseum03`
- Location: `LCTN 02385D96` / **Arena District**

## Role

Judo is not implemented as a standalone story NPC with unique dialogue.

He is one of the named actor variants used by VIGILANT's radiant/randomized **Feral Soul-Shriven** encounter system.

The quest:
- `QUST 0251532C` / **Feral Soul-Shriven**

has the objective:

- **Defeat <Alias=Enemy>**

and owns generic Soul-Shriven encounter scripts.

The Arena District trigger:
- `REFR 0251778B`

uses:
- `CHRqSoulShrivenTRGScript`

with its `SvBase` property set directly to:

- `NPC_ 0251653B` / **Judo of the Order of Diagna**.

This is strong structural evidence that Judo is spawned/managed as a named Soul-Shriven combat encounter.

## Soul-Shriven identity

Judo templates from:

- `NPC_ 025177A1` / **Soul-Shriven**

and carries:
- `SPEL 0251651F` / **Soul Shriven abilities**
- `FACT 025738DF` / **Soul-Shriven**

His death list is the same generic:
- `zzzCHDeathItemRqShriven`

used by the radiant encounter system.

Current classification:

**Judo is a Diagna-themed named Soul-Shriven combatant, not a separate companion/quest-giver comparable to Gaiden Shinji.**

## Arena District placement

Judo's trigger is inside:

- `CELL 0206DD87` / `CHCityColosseum03`

whose location is:

- `LCTN 02385D96` / **Arena District**

inside the Coldharbour worldspace.

This places him near the same broad Arena/Colosseum complex in which Gaiden Shinji appears, but the two are implemented through different systems:

- **Gaiden** — persistent special NPC / dialogue / follower machinery
- **Judo** — radiant Feral Soul-Shriven enemy variant

No direct dialogue, quest alias, or script property currently links Gaiden and Judo to one another.

## Knight of Diagna equipment

Judo's outfit is:

- `OTFT 0204F0A8` / `zzzCHOutfitRenald`

Despite the legacy `Renald` EditorID, the player-facing pieces are:

- `ARMO 0204F0A3` — **Knight of Diagna Boots**
- `ARMO 0204F0A4` — **Knight of Diagna Armor**
- `ARMO 0204F0A5` — **Knight of Diagna Gauntlets**
- `ARMO 0204F0A6` — **Knight of Diagna Helmet**

Judo therefore provides the clearest direct wearer of the **Knight of Diagna** set.

This corrects an earlier attribution that assigned this exact set to Aredhel.

## Weapons

Judo carries:

- two `WEAP 02052F59` / **Akaviri Black Katana**

The weapon's internal EditorID is:

- `zzzCHRenaldSwordPlayable`

This again shows that the old Renald asset family was reused beyond Aredhel.

It does **not** establish that the Akaviri Black Katana is Gaiden's lost Yokudan/Diagna sword.

Gaiden's missing sword remains unidentified.

## Crafting unlock connection

Four Knight of Diagna armor recipes are:

- `COBJ 021A4BB3` — boots
- `COBJ 021A4BB4` — cuirass
- `COBJ 021A4BB5` — gauntlets
- `COBJ 021A4BB6` — helmet

Each contains an OR-condition chain whose first check is:

- `GetDeadCount(NPC_ 0251653B / Judo) > 0`

and whose second check is:

- `GetQuestCompleted(QUST 02052F4A / Pitier) == 1`.

So the Knight of Diagna crafting path can be unlocked through either:
- defeating Judo;
- or completing Aredhel's **Pitier** quest.

This is a strong gameplay-system link between Judo and the Aredhel/Renald equipment family.

It is **not** evidence that Judo and Aredhel are the same person.

## Blade of Diagna distinction

Aredhel's actual later outfit is:

- `OTFT 024FC4B1` / `zzzCHOutfitAredhel`

and contains the separate **Blade of Diagna** set:

- `024FC4A5` — Blade of Diagna Boots
- `024FC4A6` — Blade of Diagna Armor
- `024FC4A7` — Blade of Diagna Gauntlets
- `024FC4A8` — Blade of Diagna Helmet

Those recipes are gated by:

- `GetQuestCompleted(Pitier) == 1`

without a Judo-death condition.

Thus VIGILANT implements at least two distinct Diagna armor traditions:

1. **Knight of Diagna** — Judo / legacy Renald equipment family
2. **Blade of Diagna** — Aredhel's later outfit

## Relation to Gaiden Shinji

Gaiden says:
- he is searching for a lost sword from sunken Yokuda;
- it may be related to Diagna;
- he gave Aredhel a sword and armor.

Judo provides:
- a named Order of Diagna identity;
- a Diagna armor set;
- Akaviri Black Katanas;
- a Coldharbour Arena-area encounter.

But no record says:
- Judo knows Gaiden;
- Judo guards Gaiden's lost sword;
- Judo's katana is the lost Yokudan sword;
- Gaiden gave Judo his equipment.

Current classification:

**Judo broadens the Diagna presence in Coldharbour but does not resolve Gaiden's lost-sword thread.**

## Canon boundary

The Order of Diagna is established Elder Scrolls lore.

**Judo of the Order of Diagna**, his Soul-Shriven status, Arena District encounter, Knight of Diagna equipment, and crafting-unlock role are VIGILANT-specific.
