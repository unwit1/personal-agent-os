# Import Status — 2026-09-23

Imported versions: Adamant 6.0.4; Hand to Hand 2.0.2; Blade and Blunt 4.0.3; Mysticism 2.5.0.

## Snapshot

- 21 plugins
- 6,009 records / 5,988 Forms
- 81,523 subrecords
- 11,676 original deterministic relations
- 3,951 effect instances
- 115 Papyrus source files
- 953 spells; 1,648 MGEFs; 625 perks; 216 weapons; 269 enchantments
- 62 combat styles; 12 movement types; 25 AVIF skill-tree records

## Resolution / deltas

- 5,988 Forms resolved with 0 slot-resolution failures
- 537 exact imported-master baselines; 1,619 external baselines
- 484 exact-baseline changed overrides; 53 identical forwards
- 311 typed field deltas currently emitted

## Completed decoders

- MGEF DATA: 1,648 / 1,648
- CTDA: 8,229 / 8,229
- PERK core: 625 headers, 1,006 effect entries, 4,035 conditions
- WEAP: 216 / 216
- ENCH: 269 / 269
- CSTY: 62 / 62
- MOVT: 12 / 12
- AVIF: 25 / 25; 297 nodes; 283 graphical edges; 7 exact add-on graph deltas
- MGEF generic VMAD: 395 / 395; 416 script attachments; 1,067 properties; 915 resolved object-property relations
- NPC_/ARMO/ACTI generic VMAD: 26 / 26; 26 attachments; 27 properties; 25 resolved object-property relations

## VMAD boundary status

- MGEF: generic VMAD fully decoded.
- NPC_: 20 / 20 generic VMAD fully decoded.
- ARMO: 4 / 4 generic VMAD fully decoded.
- ACTI: 2 / 2 generic VMAD fully decoded.
- PERK: 6 records have valid generic prefixes plus record-specific tails of 87, 89, 97, or 98 bytes. These are deliberately deferred.
- QUST: 7 records remain deferred for a specialized fragment/alias decoder.

## Exact VMAD comparisons

- MGEF: 31 imported-baseline comparisons; 30 modified, 1 identical forward.
- NPC_/ARMO/ACTI: 2 imported-baseline comparisons; both identical forwards.

## Guardrails

- AVIF graph edges are UI/tree topology, not PERK prerequisites.
- A VMAD record is called generically decoded only when the generic parser consumes the complete subrecord.
- A valid generic prefix does not justify decoding an unknown record-specific tail.
- Approved design rules: 0.
