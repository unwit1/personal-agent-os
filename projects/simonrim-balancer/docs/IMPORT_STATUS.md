# Import Status — 2026-09-23

Imported: Adamant 6.0.4, Hand to Hand 2.0.2, Blade and Blunt 4.0.3, Mysticism 2.5.0.

## Core snapshot

- 21 plugins
- 6,009 records / 5,988 Forms
- 81,523 subrecords
- 11,676 original deterministic relations
- 3,951 effect instances
- 476 BSA members
- 115 Papyrus source files
- 953 spells
- 1,648 magic effects
- 625 perks
- 216 weapons
- 269 enchantments
- 62 combat styles
- 12 movement types
- 25 actor-value / perk-tree records

## Resolution / exact deltas

- 5,988 Forms resolved; 0 slot-resolution failures
- 537 exact imported-master baselines; 1,619 external baselines
- 484 exact-baseline changed overrides; 53 identical forwards
- 311 typed field deltas currently emitted

## Completed high-value decoders

- MGEF DATA: 1,648 / 1,648
- CTDA: 8,229 / 8,229
- PERK: 625 headers, 1,006 effect entries, 4,035 conditions
- WEAP: 216 / 216; 21 groups; 18 recurring patterns; 18 exact deltas
- ENCH: 269 / 269; 870 effects; 36 groups; 27 recurring patterns; 58 exact deltas
- CSTY: 62 / 62; 12 groups; 7 recurring patterns
- MOVT: 12 / 12; 8 profiles; 3 recurring/complete-domain observations
- AVIF: 25 / 25; 297 nodes; 283 graphical edges; 7 exact add-on graph deltas; no missing targets, unreachable nodes, or cycles
- MGEF generic VMAD: 395 / 395; 416 script attachments; 1,067 properties; 915 object-property relations with 0 unresolved targets

## MGEF VMAD exact comparisons

- 31 exact imported-baseline VMAD comparisons
- 30 modified VMADs
- 1 identical VMAD forward
- 115 distinct attached script names
- 234 / 416 attachments match supplied PSC source
- 80 / 115 distinct attached script names have supplied PSC source
- property types: 915 Object, 83 Float, 33 Int32, 33 Bool, 3 String
- 4 Object properties preserve non--1 alias bindings

## Evidence / rule state

- Combined aggregated observed patterns: 234
- Approved design rules: 0
- AVIF graph edges remain distinct from actual PERK CTDA prerequisites.
- Script attachment frequency and property values remain implementation evidence, not automatically promoted rules.

## Deferred

- VMAD on PERK, NPC_, ARMO, ACTI
- QUST VMAD fragments / aliases
- quest/story-manager structures
- additional record-specific structures
