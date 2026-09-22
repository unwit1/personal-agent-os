# VIGILANT book provenance — verified seed set

Continuity: `tes.mod.vigilant`

VIGILANT's `BOOK` records include a mixture of mod-specific documents, spell/conjuration books, and texts originating in official Elder Scrolls releases. A book's presence in `Vigilant.esm` therefore does **not** automatically make its prose VIGILANT-authored lore.

## Verified official TES/ESO texts embedded in VIGILANT

The following records match published *The Elder Scrolls Online* books and should be dual-tagged as **official-source reprint embedded in VIGILANT**, not as original VIGILANT claims:

- `02054ED2` — **The Remnant of Light** by Beredalmo the Signifier — official *The Elder Scrolls Online* Rivenspire lorebook; VIGILANT embeds the published Ayleid tract rather than originating Filestis/Anumaril's Remnant narrative.
- `0212905B` — **The Archimonk's Dream** — first chant within ESO's *Proper-Life: Three Chants*.
- `0212905C` — **The Song-Never-Sung-at-Twilight** — second chant within ESO's *Proper-Life: Three Chants*.
- `0212905D` — **The Forty-Third Praise-Song of Alessia** — third chant within ESO's *Proper-Life: Three Chants*.
- `0212905E` — **The Exclusionary Mandates** — ESO lorebook on Marukhite/Alessian doctrine.
- `0212905F` — **The Illusion of Death** — ESO fragment concerning Marukh's penance and the shade of Al-Esh.
- `02054ED3` — **On the Detachment of the Sheath from the Integument** by Arch-Prelate Fervidius Tharn — official ESO Marukhati/Middle Dawn text; exact VIGILANT transcription preserved separately.
- `024A8AF7` — **Vindication for the Dragon Break** by Fervidius Tharn — official ESO Marukhati Dragon Break text; exact VIGILANT transcription preserved separately.
- `024A8AFD` — **Aurbic Enigma 4: The Elden Tree** by Beredalmo the Signifier — official ESO Tower/Staff-of-Towers text; VIGILANT references it through general book leveled lists rather than a fixed narrative placement.
- `024A8B07` — **On the Nature of Coldharbour** by Phrastus of Elinhir — ESO lorebook on Molag Bal's realm and soul-shriven.

## Ingestion rule

For a verified reprint, store two provenance relationships:

1. `appears_in: tes.mod.vigilant` — because the object is physically present in the VIGILANT plugin and can be encountered/used by the mod;
2. `text_origin: tes.official.<game/source>` — because the actual prose originated in an official Elder Scrolls publication.

VIGILANT-specific placement, context, editing, omissions, additions, or juxtaposition remain valid mod-continuity evidence even when the underlying text is official.

## Pending classification

The remaining 169 BOOK records need title/text comparison against the official corpus. Priority should go to Coldharbour/Alessian/Ayleid/history books before spell tomes and `Fragment of the Stone` conjuration objects.


## Verification note — The Remnant of Light

The exact VIGILANT transcription of `BOOK 02054ED2` matches the published ESO lorebook **The Remnant of Light**, credited to Beredalmo the Signifier and classified as Rivenspire lore.

Therefore:
- Filestis and Anumaril's Remnant-of-Light episode is licensed-source substrate;
- VIGILANT-specific placement/juxtaposition remains valid mod evidence;
- the prose itself should not be treated as a Vicn-authored historical claim.
