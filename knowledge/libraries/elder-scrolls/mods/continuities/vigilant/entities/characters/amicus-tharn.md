# Amicus Tharn

- Continuity: `tes.mod.vigilant`
- Role: senior Alessian/Marukhati ideologue; later boss in Belharza's Hidden Charnel
- Boss form: `NPC_ 0251D68A` / `zzzCHBossAmicusTharn` — **Amicus Tharn**
- Boss reference: `ACHR 0251D68F`
- Boss location: `CELL 0251C043` / **Belharza's Hidden Charnel**
- Quest ownership: `QUST 0251ADBF` / **Broken Horns**, alias `Boss`
- Outfit: `OTFT 0251D68B` / `zzzCHOutfitHrBattlemageAmicus`
- Death list: `LVLI 0251D68C` / `zzzCHDeathItemAmicusTharn`
- Major documentary sources:
  - `BOOK 0251D5CB` / *Petition to House Tharn, Vol. 11*
  - `BOOK 0251D5CC` / *Petition to House Tharn, Vol. 23*
  - `BOOK 0251D5CD` / *Petition to House Tharn, Vol. 68*
  - `BOOK 0251D5CE` / *Petition to House Tharn, Vol. 77*

## Identity

The four *Petition to House Tharn* books contain extended dialogues between **Pelan** and **Amicus**.

The later NPC is explicitly named **Amicus Tharn**, and the surrounding record cluster uses `Tharn` consistently:

- `zzzCHBossAmicusTharn`
- `zzzCHDeathItemAmicusTharn`
- `zzzCHCorpseTharn01`
- `zzzCHCorpseTharn02`
- `zzzCHCorpseTharn03`

Current classification: **high-confidence documentary Amicus = later Amicus Tharn boss identity cluster**.

The petitions themselves list their author as **Unknown**, so they are best treated as transcripts/records of conversations rather than texts authored by Amicus.

## House Tharn connection

A focused continuity comparison is preserved at:

`analysis/amicus-tharn-house-tharn.md`

The ESM gives Amicus a strong House Tharn association:
- his boss is explicitly named **Amicus Tharn**;
- all boss/corpse/death EditorIDs use the Tharn name;
- his documentary sequence is titled *Petition to House Tharn*.

VIGILANT also embeds writings by **Fervidius Tharn**, the historically established Marukhati Arch-Prelate, including:
- *On the Detachment of the Sheath from the Integument*;
- *Vindication for the Dragon Break*.

This makes the Amicus surname a deliberate fit with the setting's older Tharn/Marukhati tradition rather than an isolated reuse of the name.

However, no ESM record gives a parent/child/ancestor relationship between Amicus and Fervidius or any later Tharn.

Current classification:

**Amicus Tharn → House Tharn association: high confidence.**  
**Amicus ↔ Fervidius exact kinship: unresolved.**  
**Amicus as ancestor of Abnur/Jagar/Clivia: unsupported.**

## Petition ideology

Across the four surviving petitions, Amicus articulates a progressively more explicit Alessian program.

### Vol. 11 — Belharza and manufactured history

Amicus rejects Belharza's claim to be Alessia's son and supports replacing him with a fabricated human Belharza.

He argues that:
- belief determines divine form;
- memories and history can therefore be deliberately fabricated;
- Morihaus can be reshaped by belief;
- Ayleids who remember Alessia, Morihaus, and Pelinal in inconvenient forms can be eliminated;
- the Order can create its own god.

This makes Amicus a direct spokesman for VIGILANT's theme that history, memory, and divine identity can be intentionally rewritten.

### Vol. 23 — human-only heaven

Amicus supports stripping citizenship from elves, giants, minotaurs, and other non-human peoples.

He proposes:
- separating Auriel from Akatosh;
- erasing elven history;
- exterminating non-human peoples;
- reforging the Heart of Shezarr;
- remaking the Aurbis with artificial Flowers;
- constructing a human-only heaven outside the gods' control.

These are Amicus's in-universe ideological claims, not neutral cosmological facts.

### Vol. 68 — rejection of the Prisoner

Amicus argues for executing anomalous “Prisoner” figures because their freedom could destroy the Order's constructed reality.

He says:
- Prisoners can create the future they want;
- the Order rejects that salvation because it threatens what it has built;
- law and morality are forms of verbal violence;
- Alessian rule is illuminated by the **Stone of Fire**.

This volume gives Amicus one of the clearest meta-level statements in VIGILANT about the conflict between imposed history and Prisoner freedom.

### Vol. 77 — memory collapse and the Stone

Amicus admits that he no longer remembers the Seventy-Seven Doctrines.

He and Pelan conclude that:
- the doctrines may have originated as interpretations of blood stains around the dead Marukh;
- records can remain while memory of them disappears;
- the Stone “chose” them;
- domination is a form of kindness for those unable to bear freedom.

This is the point where Amicus's ideology and the Stone become structurally inseparable.

## Environmental petition trail

The ESM distributes the four petitions through a deliberate sequence of Amicus-linked remains and the final boss.

### Vol. 11

`CONT 0251D67F` / `zzzCHCorpseTharn01`:
- display name: **Denounced One**
- model: `Clutter\VigCgt\statue\AmicusDead.nif`
- contains `BOOK 0251D5CB` / Vol. 11
- placed as `REFR 0251D682`
- location: `CELL 0221AFA1` / **First Inquisition Court**

### Vol. 23

`CONT 0251D680` / `zzzCHCorpseTharn02`:
- display name: **Denounced One**
- same `AmicusDead.nif` model
- contains Vol. 23
- placed as `REFR 0251D687`
- location: **Belharza's Hidden Charnel**

### Vol. 68

`CONT 0251D681` / `zzzCHCorpseTharn03`:
- display name: **Denounced One**
- same `AmicusDead.nif` model
- contains Vol. 68
- placed as `REFR 0251D688`
- location: **Belharza's Hidden Charnel**

### Vol. 77

The living/boss Amicus uses death list `0251D68C`, which includes:
- `BOOK 0251D5CE` / **Petition to House Tharn, Vol. 77**

This produces a strong environmental sequence:

**dead Amicus image + Vol. 11 → dead Amicus images + Vols. 23/68 → living/boss Amicus Tharn + Vol. 77**

The ESM does not explain whether the three “Denounced One” corpses are literal earlier bodies of Amicus, symbolic memorials, reconstructed Coldharbour echoes, or repeated representations. Their shared `AmicusDead.nif` model and Tharn EditorIDs nevertheless make the association intentional.

## Broken Horns

`QUST 0251ADBF` / **Broken Horns** owns the Amicus boss through alias `Boss`.

The alias points directly to:
- `NPC_ 0251D68A` / **Amicus Tharn**

The placed boss reference:
- `ACHR 0251D68F`

is inside:
- **Belharza's Hidden Charnel**

This is especially significant because Vol. 11 presents Amicus arguing that Belharza should be rewritten/replaced, while the later boss appears inside Belharza's own hidden charnel during the final Belharza/Morihaus side-quest complex.

## Boss presentation

Amicus Tharn uses:
- a normal master-game Imperial race;
- **Marukhati Selective Armor**
- **Marukhati Selective Gauntlets**
- **Marukhati Selective Mask**
- **Marukhati Selective Hood**
- `WEAP 025056E7` / **Heretic's Staff**

His VMAD contains a generic `CHModKarmaOnDeath` script.

No unique INFO dialogue currently resolves to the boss, so his ideological voice remains preserved primarily through the petitions.

## Interpretation

Amicus is not merely Pelan's debate partner in four books.

The ESM turns him into a repeated environmental motif and later encounter:

1. petitions preserve his ideology;
2. corpse-statue containers modeled specifically as **AmicusDead** carry the first three volumes;
3. the final volume is carried by Amicus Tharn himself;
4. his boss appears in Belharza's Hidden Charnel, directly tying his later encounter to one of his earliest ideological targets.

Current classification: **high-confidence documentary → corpse-image trail → Broken Horns boss identity network**.

## Evidence limits

The ESM does not yet establish:
- the exact genealogical relationship between Amicus and other Tharns;
- whether he belongs to a recoverable branch of the later famous Tharn family;
- whether the three corpse containers represent actual deaths, symbolic denouncements, or Coldharbour memory echoes;
- how Amicus survives/reappears as the later boss after the documentary periods;
- whether external Papyrus gives the boss additional narrative logic.

## Canon boundary

Amicus Tharn, his ideology, the House Tharn petition sequence, the repeated corpse-image trail, and his Broken Horns boss manifestation are `tes.mod.vigilant` material unless independently corroborated by licensed Elder Scrolls sources.
