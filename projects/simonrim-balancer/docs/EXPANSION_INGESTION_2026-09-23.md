# Simonrim Expansion Ingestion — 2026-09-23

This append-only ingestion extends the Simonrim Balancer beyond the original Adamant / Hand to Hand / Blade and Blunt / Mysticism snapshot without rewriting that immutable source snapshot.

## Supplied mods

Adamant - Bard Addon 1.1.0; Aetherius 2.15.1; Apothecary 1.3.9; Apprentice 1.1.0; Arena 1.2.0; Artificer 1.0.11; Candlehearth 1.1.1; Crusader 0.6; Gourmet 1.2.0; Manbeast 2.1.1; Mercantile 1.0.0; Pilgrim 1.3.1; Power Attack Speed Perks 1; Scion 2.2.2; Sorcerer 1.1.0; Starfrost 2.0.0; Stormcrown 1.1.17.

## Raw-ingestion checkpoint

- 17 mods
- 53 plugin source occurrences
- 51 unique plugin binaries by SHA-256
- 9,769 plugin records
- 289,053 subrecords
- 68 record types
- 0 parser-error files
- 12 BSAs / 898 BSA members
- 239 PSC source occurrences, 202 unique by hash
- 2,046 decoded configuration values
- 55 FOMOD options

The two duplicate plugin occurrences are retained as installer provenance. They are not double-counted as unique binaries.

## New mechanic coverage introduced

This batch adds substantial evidence for encounter zones (Arena), races (Aetherius), alchemy/ingredients (Apothecary), classes (Apprentice), artifacts/equipment (Artificer), inns/dialogue/world edits (Candlehearth), cooking/economy/distribution (Gourmet), werewolves (Manbeast), religion/shrines (Pilgrim), vampires (Scion), staves/scrolls/crafting (Sorcerer), survival (Starfrost), and shouts (Stormcrown), plus several small Simonrim integration/add-on plugins.

## Source behavior

BSA extraction recovered author/source PSC files for Aetherius, Apothecary, Apprentice, Artificer, Candlehearth, Gourmet, Pilgrim, Sorcerer, Starfrost and Stormcrown. Loose PSC sources were also supplied by Apprentice, Manbeast, Pilgrim and Scion. Duplicate source copies are hash-deduplicated for analysis while source occurrence provenance remains intact.

## Status

Raw/source ingestion is complete for this supplied expansion batch. Mechanic-specific semantic decoding, canonical Form resolution, override/delta analysis, observed-pattern generation, and integration into the candidate-family layer are the next stages.

No newly observed behavior is an approved Simonrim rule.
