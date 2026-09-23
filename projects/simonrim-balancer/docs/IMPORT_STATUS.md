# Import Status — 2026-09-23

## Imported versions

- Adamant 6.0.4
- Hand to Hand 2.0.2
- Blade and Blunt 4.0.3
- Mysticism 2.5.0

## Parsed counts

- Source files: 73
- Plugins: 21
- Records: 6,009
- Subrecords: 81,523
- Deterministic relations: 11,676
- BSA members: 476
- Papyrus source files: 115
- Papyrus properties: 279
- Config values: 129
- FOMOD options: 20
- Spells: 953
- Magic effects: 1,648
- Perks: 625
- Effect instances: 3,951

## Deterministic decoding implemented

- Bethesda record/group structure
- compressed plugin records
- subrecord structure including XXXX extended sizes
- EDID and textual FULL/DESC
- SPEL/SPIT
- EFID / EFIT
- GMST and GLOB values
- basic PERK/DATA
- basic WEAP/DATA
- basic ARMO/DATA
- BSA v105 inventory for these packages
- uncompressed BSA text extraction
- Papyrus script/property/member inventory
- INI/TOML/JSON key/value extraction
- FOMOD option extraction
- FormID relationships for keywords, effects, leveled lists, form lists, and crafting

## Preserved but not fully semantically decoded yet

The raw snapshot retains bytes needed for later exact decoders for:
- complete MGEF/DATA
- conditions (CTDA)
- complete perk entry-point structures
- weapon DNAM
- enchantment structures
- combat styles
- movement types
- quests/story manager data
- VMAD property values and attachments
- additional record-specific structures

Uncertain fields remain raw evidence instead of being promoted into incorrect balance facts.
