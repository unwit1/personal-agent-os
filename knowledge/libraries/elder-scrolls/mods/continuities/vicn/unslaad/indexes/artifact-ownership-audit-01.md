# Artifact ownership audit 01

Continuity: tes.mod.vicn.unslaad  
Primary source: translated Unslaad.esm 3.0.6

This pass distinguishes four acquisition/evidence classes:

1. **direct NPC inventory** — the actor actually carries/uses the item record;
2. **death-item list** — the item is configured as post-death loot;
3. **placed reward container** — the item is recovered from a chest/corpse/container;
4. **craft reconstruction** — a player-craftable form exists, sometimes separate from the NPC combat form.

These classes should not be collapsed into one generic "owned by" relationship.

## Austella

NPC 030188B1 / Austella:
- directly carries WEAP 030188B3 — **Hoarfrost Scythe**;
- death item 030188B4 yields:
  - ARMO 03009047 — **Austella's Dress**;
  - ARMO 0327EA63 — **Ring of Favor**;
  - WEAP 03003E26 — **Hoarfrost Scythe**.

The NPC scythe and recoverable scythe are separate records sharing the same Frost Blade enchantment family.

## Jhunal the Gray / Gray Owl

Several Jhunal-the-Gray forms share death list 0316417D / zzzCrbDeathItemGrayOwl.

That death list includes:
- WEAP 0315F23E — **Darkstalker's Staff**;
- ARMO 03219EF9 — **Darkspeaker Ring**;
- ARMO 0324237D — **Shield of Magnus**;
- several base-game records.

The Mq05 Jhunal form directly carries the boss/combat version of **Darkstalker's Staff** (0318C84F).

This is strong implementation evidence connecting Jhunal/Gray Owl to the Magnus shield and Darkstalker/Darkspeaker equipment set.

## Khev / Molag

**Khev the Dreugh King** directly carries combat-form **Muatra** (03407474).

His hologram/source forms also carry the same combat-form Muatra.

**Molag the Lord of Lies** directly carries two **Coldfire Swords**.

Molag's death list yields:
- Dreugh Wax;
- recoverable **Muatra** (03379436);
- one base-game record.

This creates a deliberate Khev/Molag/Muatra/Coldfire equipment graph without proving literal identity with Vivec or Molag Bal.

## Yngol

**Remnant of Yngol** in Ghostfire Forge directly carries:
- **Yngol's Shield**;
- **Yngol's War Axe**.

A separate chest in **Ysgrim's Seal** contains:
- **Yngol's Battleaxe**.

Thus the one-handed axe/shield are direct Remnant-of-Yngol equipment, while the battleaxe is a reward-container artifact.

## Magnar

**Idol of Magnar** in Frozen Tomb directly carries **Magnar's Warrior Spear**.

Its death list yields:
- a separate recoverable Magnar-spear form;
- **Magnar's Warrior Helmet**;
- base-game items.

A Dragon's Peak reward chest separately contains:
- Magnar's Warrior Spear;
- Magnar's Warrior Shield;
- Magnar's Warrior armor set.

The boss-carried spear and reward-set reconstruction are distinct implementation routes.

## Stuhn / Tsun

**Warrior of Stuhn** in Dragon's Throat directly carries:
- **Shield of Stuhn**;
- **Atmoran Champion Sword**.

**Warrior of Tsun** has a custom death list, but the currently decoded entries resolve only to Skyrim-master records in this pass; no custom named Tsun artifact is directly established here.

## Jhunal giant / priest

**Last Giant of Jhunal** in Ysgrim's Seal directly carries:
- **Giant of Jhunal Club**.

Its death list includes:
- **Priest of Jhunal Mask**;
- base-game materials/items.

This directly ties the mask reward to the Giant-of-Jhunal encounter, even though the mask title itself refers to a priest rather than the giant.

## Ysgrim / Ysgramor

**Hoary King Ysgrim** directly carries:
- **Saarthal's Sorrow**.

The later **Ysgramorsbelt** boss form directly carries two **Fists of Ysgramor**.

Its death list yields:
- two **Storm Fists**;
- a recoverable **Saarthal's Sorrow**;
- base-game records.

This supports a multi-phase Ysgrim/Ysgramor artifact progression rather than one static loadout.

## Harakk

The placed container/corpse **Unknown Harakk Warrior** in Old Hunter's Cabin contains:
- Harakk Warrior Armor;
- Harakk Warrior Gauntlets;
- Harakk Warrior Helmet;
- Magnar's Warrior Longspear;
- related Harakk equipment.

This is corpse/container provenance, not direct proof that every item belonged to one historically named Harakk individual.

## Snow Guardian Jokul

**Snow Guardian Jokul** directly carries NPC-form **Elder Wood Greatsword**.

A separate reward chest in Ysgrim's Seal contains the recoverable enchanted version.

## Aisha wounded form

The wounded/sabre Aisha form's death list includes:
- **Cat Ring**;
- base-game items.

The Cat Ring is enchanted with **Perfect Landing**.

## Evidence rule

An item name is not automatically a historical claim.

Prefer:
- direct inventory for "carried/used by";
- death list for "drops/yields";
- container placement for "recovered from";
- recipe for "craftable reconstruction."

Do not rewrite those into stronger ownership language without source support.
