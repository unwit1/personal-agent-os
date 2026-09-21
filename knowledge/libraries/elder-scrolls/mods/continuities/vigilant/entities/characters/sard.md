# Sard

- Continuity: `tes.mod.vigilant`
- Historical role: saint associated with Alessia, Belharza, and Marukh
- Direct NPC form: none found in the current 1,233-NPC VIGILANT inventory
- Direct dialogue: none identified
- Associated locations:
  - `CELL 02109458` / **Sard's Charnel**
  - `CELL 0210CDFD` / **Sard's Ossuary**
- Associated relics:
  - `ARMO 020EB827` / **Sard's Red Eye Ring**
  - `ARMO 020EB828` / **Sard's Blue Eye Ring**
  - `ALCH 020E2592` / **Ashes of St. Sard**
  - `KEYM 0210A8E5` / **Sard's Charnel Key**

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Sard as a woman who possessed one red eye and one blue eye and retained the appearance of youth for more than a century.

The text says she:
- served as a handmaiden to **St. Alessia**;
- served **Emperor Belharza** after Alessia's death;
- later served **Marukh** after the Alessian Order was founded;
- remained young because of Alessia's blessing;
- rapidly aged after Marukh's death;
- finally turned to ash, leaving only her jewel-like eyes.

These biographical claims remain the saint text's historical tradition rather than neutral narration.

## Environmental implementation

VIGILANT translates the final part of Sard's biography into explicit environmental objects.

The plugin contains:
- **Sard's Red Eye Ring**;
- **Sard's Blue Eye Ring**;
- **Ashes of St. Sard**;
- **Sard's Charnel**;
- **Sard's Ossuary**.

The door graph directly links:

**Sard's Charnel** ↔ **Sard's Ossuary**.

Most importantly, both eye rings are inventory objects inside the `Vena Petilius` treasure container (`CONT 0210DAD7`), and that container is physically placed as `REFR 0210DAD8` inside **Sard's Ossuary**.

This makes the saint book's claim that Sard left behind jewel-like eyes much more than thematic resemblance: the plugin deliberately places two ring-relics named for her red and blue eyes inside her own ossuary.

## Ashes

`ALCH 020E2592` / **Ashes of St. Sard** is another explicit Sard relic.

The ESM reuses this relic in multiple inventories, including:
- Hasaama;
- Vena Petilius;
- Martha;
- Emperor Gorieus.

Because the same base relic occurs in several inventories, those placements should not automatically be interpreted as four independent portions of Sard's historical remains. They are implementation evidence that the relic is collectible/reused across encounters.

The Vena Petilius treasure container inside Sard's Ossuary is the strongest contextually anchored Sard placement because it contains the ashes together with both eye rings.

## Identity profile

Sard currently differs from saints such as Pelan, Jhunal, or Caliburn:

- she has no identified speaking continuation;
- no Sard NPC base form has been found;
- her biography survives through *The Eight Saints of Cyrod*;
- her physical presence in Act 4 is represented through tomb architecture and relics.

Current classification: **high-confidence saint → charnel/ossuary/relic identity cluster**.

## Red-eye imagery elsewhere

VIGILANT contains other red-eye imagery, including an unresolved line in *Beyond the Shores of Madness* about red eyes looking into a speaker's heart.

There is currently no structural evidence tying that line specifically to Sard. It should remain separate unless later quest, scene, or script evidence establishes a connection.

## Canon boundary

Sard's service to Alessia, Belharza, and Marukh; supernatural youth; death after Marukh; and eye/ash relic tradition are recorded as `tes.mod.vigilant` material unless separately corroborated by licensed Elder Scrolls sources.
