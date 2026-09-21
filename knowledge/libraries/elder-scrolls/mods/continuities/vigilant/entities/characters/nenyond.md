# Nenyond

- Continuity: `tes.mod.vigilant`
- Role: eastern Cyrodiilic lord and Marukhati Selective in *The Eight Saints of Cyrod*
- Associated locations:
  - `CELL 0210EBFD` / **Nenyond's Underground Priory**
  - `CELL 021114AF` / **Funeral Temple**
- Associated item: `KEYM 0212D026` / **Nenyond's Key**
- Direct NPC form: none found in the current 1,233-NPC VIGILANT inventory

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Nenyond as a feudal lord ruling eastern Cyrodiil and a member of the Marukhati Selectives.

Unlike many of the Order's extremists, the text calls him comparatively moderate. It says he spent his entire fortune constructing an underground priory on his lands.

During construction, ruins from the **Dawn Era** were discovered. Nenyond and his friend **Manthar** entered/explored those ruins and disappeared.

The same book says that after Nenyond vanished, **Varla** took over the seat of the eastern lords on Emperor Belharza's recommendation.

## Relationship to Manthar and Silorn

The saint text presents Nenyond, Manthar, and Silorn as one connected disappearance chain:

- Manthar was the architect/sorcerer involved in the priory's construction.
- Nenyond and Manthar disappeared together while exploring the excavated ruins.
- Silorn later entered the ruins to search for them.
- only Silorn's skin returned, after which the priory and ruins were sealed.

VIGILANT independently contains a boss/summon identity for **Sorcerer Manthar**, so the Manthar name continues beyond the saint biography. No equivalent Nenyond NPC form has yet been found.

## Spatial implementation

The ESM implements **Nenyond's Underground Priory** as a real Coldharbour location, not merely a book reference.

The door graph gives a direct configured traversal pair:

- **Nenyond's Underground Priory** ↔ **Funeral Temple**

Nenyond's priory is also one of the many interiors attached to the main Coldharbour exterior hub.

This proves VIGILANT treats Nenyond's foundation as part of the explorable Act 4 world. It does not prove that the Coldharbour version is historically unchanged from the First Era site.

## Disappearance complex

The deeper reconstruction is tracked in:

`analysis/nenyond-priory-complex.md`

The key structural result is that **Nenyond himself remains absent**, while the two figures who followed his disappearance trail are both physically represented in the connected **Funeral Temple**:

- **Sorcerer Manthar** — `ACHR 021146DA`
- **Abbot Silorn** — `ACHR 0243A499`

This makes the Funeral Temple read as an environmental aftermath of the expedition beneath Nenyond's priory rather than as a simple Nenyond boss arena.

The saint text says Nenyond and Manthar vanished first, Silorn followed to search for them, and only Silorn's skin returned. VIGILANT preserves those consequences asymmetrically:

- Manthar survives as a boss/summon identity;
- Silorn survives as an actor plus the **Hide of Abbot Silorn** relic;
- Nenyond survives only through the priory, key, historical account, and his unresolved absence.

The claim that the excavated ruins are genuinely from the **Dawn Era** still comes from *The Eight Saints of Cyrod*. The implemented cells corroborate the site and relationships, not that dating.

## Current evidence limits

Nenyond currently has:
- no identified speaking INFO;
- no identified NPC base form;
- no independent journal or note in the extracted 179 BOOK records;
- no direct first-person testimony.

For that reason, this dossier stays deliberately narrow. Most biographical detail currently comes from *The Eight Saints of Cyrod*, while the ESM independently corroborates the existence and importance of his priory through cells, keys, and traversal structure.

## Canon boundary

Nenyond's biography, membership in the Selectives, moderation, disappearance with Manthar, and succession by Varla are recorded as VIGILANT-specific historical tradition pending comparison with licensed Elder Scrolls sources.
