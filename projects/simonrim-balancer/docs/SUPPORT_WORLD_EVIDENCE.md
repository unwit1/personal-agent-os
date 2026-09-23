# Support / Economy / World-Placement Evidence — 2026-09-23

This checkpoint closes the remaining gameplay-relevant gaps among the small support record families.

## Deterministic coverage

- MISC: 8 / 8
- ACTI: 4 / 4
- FACT: 2 / 2
- REFR: 16 / 16
- CELL: 11 / 11
- WRLD: 2 / 2
- Support relationships emitted: 106
- Decode failures: 0
- Approved rules: 0

## Economy items

Adamant defines seven Treasure Hunter reward objects:

- Golden Bowl ×2
- Golden Goblet ×2
- Golden Jug
- Golden Plate
- Golden Platter

Every reward object is exactly:
- value: **1000**
- weight: **1.0**

Mysticism defines:
- Simonium Ore
  - value: **25**
  - weight: **1.0**
  - two Skyrim keyword relationships retained canonically

These are implementation values, not yet a generalized economy rule.

## Activators

Hand to Hand overrides two Dragonborn Apocrypha constellation activators:
- Lockpicking constellation becomes **Hand to Hand Perks**
- Pickpocket constellation becomes **Security Perks**

Both retain VMAD behavior evidence already decoded in the generic VMAD layer.

Mysticism defines two visual/runtime activators used by translimination/recall effects. Their interaction/model role is retained, while visual assets remain presentation evidence rather than balance evidence.

## Vendor factions

Mysticism modifies/defines two vendor factions:

- DLC1ServicesFeran
  - Vendor + Can Be Owner flags
  - vendor list resolves to Mysticism's vendor FormList
  - vendor chest resolves to Dawnguard's chest
  - one vendor condition

- MAG_ServicesDBFestus
  - Vendor + Can Be Owner flags
  - vendor list resolves to Skyrim's spell-vendor list
  - vendor chest resolves to a Mysticism placed chest

This connects Mysticism's spell distribution records to actual vendor infrastructure.

## World placement

All 16 REFR records are decoded with:
- base object
- canonical owning CELL
- canonical owning WRLD where applicable
- position and rotation
- location / leveled-item links where present

This includes:
- spell/vendor placements in Mzulft, Apocrypha, College Arch-Mage's Quarters, Potema's Sanctum, Bloodlet Throne, Movarth's Lair, Dark Brotherhood Sanctuary and Shrine of Azura exterior;
- Mysticism Beacon markers in Tamriel;
- Recall and Anchor markers in Windhelm Pit Worldspace.

The 11 CELL and 2 WRLD records preserve location, climate, water, encounter-zone, music, image-space and ownership relationships where present.

## Guardrails

- Placement evidence tells us where a feature is instantiated; it does not automatically imply a balance principle.
- Presentation-only model/lighting data remains source inventory unless a gameplay record explicitly depends on it.
- External Skyrim/DLC cell/world bodies are not reconstructed beyond the override fields supplied in these plugins.
- No support/world observation is an approved rule.
