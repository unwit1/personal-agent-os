# Base-TES continuity boundaries and crosslinks

Continuity: `tes.mod.wheels-of-lull`

Wheels of Lull deliberately attaches itself to major Elder Scrolls characters and concepts. Retrieval must distinguish **reference** from **promotion into Bethesda continuity**.

## Sotha Sil / Clockwork City

Continuity claims include Memory as Sotha Sil's final creation, the deepest mechanism as Sotha Sil's central mainframe, Trademarks as his guardians, and Chronographer origin stories.

Base-library routing:
- `knowledge/libraries/elder-scrolls/topics/characters/sotha-sil.md`
- `knowledge/libraries/elder-scrolls/topics/characters/sotha-sil-clockwork.md`
- related Sotha Sil dossiers under `topics/characters/`

**Boundary:** these specific Wheels of Lull constructions remain mod-continuity claims unless independently supported there.

## Divayth Fyr and Yagrum Bagarn

The plugin uses named versions of canonical figures. The apparent Fyr actor is later revealed as Archeron's disguise; Yagrum receives new continuity-specific dialogue.

**Boundary:** do not back-propagate apparent-Fyr dialogue into the canonical Fyr dossier. Yagrum's Wheels of Lull statements require independent base-source corroboration before promotion.

## Numidium and the Dwemer

Hammar's confident theory that the Dwemer merged into Numidium is continuity testimony. Relevant base routing includes:
- `knowledge/libraries/elder-scrolls/topics/characters/kagrenac.md`
- `knowledge/libraries/elder-scrolls/topics/characters/tiber-septim.md`
- `knowledge/libraries/elder-scrolls/topics/characters/zurint-arctus.md`
- `knowledge/libraries/elder-scrolls/topics/characters/wulfharth.md`

Yagrum's own Wheels of Lull line explicitly preserves uncertainty.

**Boundary:** Hammar's explanation is not a solved base-canon Dwemer disappearance.

## Towers, Stones, and Snow-Throat

Numinar and Hammar use Tower/Stone terminology and give a specific active/inactive model.

The library also contains apocryphal/developer-text source material such as *Nu-Mantia Intercept* and *Aurbic Enigma* in the central apocryphal source collection.

**Boundary:** source classes must remain distinct. Developer/apocryphal texts are not silently equivalent to Bethesda-published game evidence, and Wheels of Lull's exact Tower state list is its own claim.

## Landfall and c0da

Other mod continuities, including VICN material, also reference Landfall/c0da.

**Boundary:** vocabulary overlap creates a crosslink, not a shared canonical event. Keep Wheels of Lull, VICN, and apocryphal/developer sources independently scoped.

## Sybandis, Wailways, memodermis, and Memory

These concepts, histories, and entities are continuity-local unless a separately sourced base record exists.

## KINMUNE, Tatterdemalion, and imported external texts

Book-provenance pass 01 now verifies three external-source relationships:

- `0537158E KINMUNE` is developer/apocryphal KINMUNE reuse and routes to the existing central source `sources/apocryphal-library/books/040008F1-anon-anu-anui-el.txt`.
- `0537158F Tatterdemalion` reuses Michael Kirkbride's out-of-game *Tatterdemalion: The Lunar Province of Secunda*; a dedicated central source record is still needed.
- `05371590 The Cacophany` is an excerpt from *The Xal-Gosleigh Letters* (Day of the Power/Knowledge material); a dedicated central work/source record is still needed.

The remaining 30 Wheels BOOK records are still pending provenance review. No-match or lack of a known earlier source is not proof of original authorship.

**Boundary:** embedding an external text establishes its presence and adoption **inside the Wheels of Lull continuity**. It does not upgrade the authority/canon class of the underlying work. Central work/source records own source-history and edition provenance; the Wheels BOOK records own local placement, excerpt boundaries, and continuity adoption.

See `book-provenance-pass-01.md` and `book-provenance-pass-01.json` for the current provenance ledger.

## Retrieval rule

When asked whether a Wheels of Lull claim is "canon":

1. state what the mod/source says;
2. label the claim `tes.mod.wheels-of-lull`;
3. identify the source class (dialogue, journal, book, implementation, literary/forged);
4. crosslink a base or apocryphal dossier if available;
5. report corroboration or conflict separately;
6. never infer canonical confirmation merely from absence of contradiction.
