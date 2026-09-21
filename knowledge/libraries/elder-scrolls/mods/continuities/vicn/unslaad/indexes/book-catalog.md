# UNSLAAD book catalog

Continuity: tes.mod.vicn.unslaad  
Primary source: translated Unslaad.esm 3.0.6

The ESM contains **50 BOOK records**. This catalog distinguishes obviously gameplay-oriented spell/summon books from narrative/source-text candidates so later ingestion can prioritize lore-bearing text.

## High-priority narrative/source-text candidates

- 03376BED — **The 36 Lessons of Vivec: Sermon 37**
- 03376BEE — **The 36&9 Lessons of Vivec: Sermon 0**
- 0347A359 — **Ysmir the Forefather, Volume IV**
- 03376B98 — **Loveletter From the Fifth Era**
- 03376BF3 — **Vivec and Molag Bal**
- 0338362C — **Harakk Warrior's Final Note**
- 031FE3DA — **Note from Fluffy**
- 03376B91 through 03376B97 — **Letter Fragment No.1–No.7**

## Gameplay / summoning / spell books

The remaining records are predominantly spell tomes, dragon bones, beast bones, and Dreugh eggs that teach or represent summons and frost abilities, including Hoarfrost Guardians, Pot Boys, Draco-Nords, Dagonic Watchers, Sinak creatures, Dragon Pus forms, and Freezing Enbarr.

## Provenance rule

Presence inside Unslaad.esm does not mean the prose originated with UNSLAAD. Sermon 37, Sermon 0, Loveletter material, and other texts with prior Elder Scrolls/developer-text histories must be compared against the existing source library and tagged as reused, adapted, fragmented, or UNSLAAD-original rather than silently attributed to Vicn.

## Next pass

Extract all 50 DESC payloads into source-text files, hash the normalized text, and compare likely reused texts against the existing Elder Scrolls/apocryphal corpus before making lore claims from them.
