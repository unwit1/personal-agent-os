# a123999 — VIGILANT Characters and Backgrounds (supplementary source)

- Continuity: `tes.mod.vigilant`
- Source type: supplementary translator/contributor background commentary
- Host: Nexus Mods article, *Vigilant Characters and Backgrounds (WIP)*
- Article author: a123999
- Article text credits translation by homosaikou and references UESP/FANDOM/TIL for general TES background
- Added: 2019-08-24
- Edited: 2023-02-15
- URL: https://www.nexusmods.com/skyrim/articles/52354

## Provenance rule

This source is **not equivalent to direct ESM evidence**.

Use it as a separate evidence layer:

- `ESM structural/dialogue evidence` = highest implementation provenance for what the shipped plugin directly contains.
- `licensed TES sources embedded or independently cited` = base-canon substrate.
- `a123999 supplementary commentary` = valuable authoring/translation/background interpretation that can resolve intent or identity where the ESM-only extraction is incomplete.
- `community comments/guides` = lower-confidence unless independently corroborated.

The article itself explicitly marks entries with an asterisk as **VIGILANT original**, while also mixing in general TES background.

## High-value VIGILANT-original claims

The article identifies or clarifies several relationships that the current ESM-only ingestion had left unresolved.

### Jacob and Rahel

The article says:
- Jacob and his fellows died during the Windhelm/Lamae incident;
- Jacob later sacrificed his wife's soul to Molag Bal;
- he obtained a new body and continued as a Vigilant;
- Rahel bore a grudge over the bargain and became a servant of Molag Bal.

This is highly useful supplementary context for:
- the official Windhelm report versus Aredhel's “Jacob was killed” testimony;
- Jacob's later survival;
- Rahel's subsequent corruption.

It should be cited as commentary, not silently substituted for the conflicting in-plugin accounts.

### Lamae

The article says:
- Lamae/Blood Matron is the first pure-blood vampire/Mother of vampires;
- VIGILANT's added backstory makes her a Nedic Arkay priestess;
- the Bard, while dominated by Molag Bal, violated her;
- she later revived through the Blood Curse;
- the Bard pierced her heart and she fell into sleep.

The direct quest/dialogue corpus remains the preferred evidence for exact scene reconstruction.

### Laza / Jhunal / Owls

The article says:
- Laza is the only survivor of the nomads slain by Lamae;
- Jhunal the Owl is the **Gray Owl**;
- Jhunal is one of multiple “Jhunals” associated with Atmora;
- Jhunal deceived Laza into attacking Kyne's Garden and catching dragons.

This supplements the ESM evidence in which Jhunal admits manipulating Laza for dragon harvesting.

### Black Worm

The article explicitly states:
- **The Black Worm is a scattered part of the spirit of Mannimarco**;
- sufficient parts can form the King of Worms, Mannimarco.

This resolves the identity at the supplementary-commentary layer even though the currently persisted ESM extraction does not contain a direct “Black Worm = Mannimarco” line.

Lorekeeper should therefore answer with source separation:

**ESM-only:** Black Worm identity was unresolved beyond Jhunal's testimony and the quest title.

**Supplementary a123999 commentary:** Black Worm is a fragment/scattered portion of Mannimarco's spirit.

### Knights of the Nine

The article says each of the named Knights had part of their souls stolen by Molag Bal and lists:
- Sir Amiel Lannus
- Sir Berich
- Sir Caius
- Sir Casimir
- Sir Gregory
- Sir Henrik
- Sir Juncan
- Sir Ralvas
- Sir Torolf

This is a strong guide for future knight-cluster ingestion but should be checked against ESM quests, NPC records, relics, and dialogue before each biography is promoted.

### Black Hand

The article describes the Black Hand as:
- the five young children of the Night Mother;
- guides for dead/cursed mortals toward Sithis.

This upgrades Black Hand from a thin ESM name into a candidate institutional/concept dossier, but exact implementation still requires source-record mapping.

### Alessia / Morihaus / Pelinal

The article says VIGILANT's original layer has Molag Bal collecting the bodies of Alessia, Morihaus, and Pelinal.

This aligns thematically with Aetherius dialogue about powerful corpses as vessels, but should remain commentary until each body's implementation is mapped.

### Varla / Mary / Umaril

The article states:
- Varla is the son of Mary and Umaril;
- Varla served as a lord in eastern Cyrodiil under the Alessian Empire;
- Varla hunted elves under Belharza's orders;
- learning his birth led to his madness;
- Mary is a healer blessed by Mara;
- Mary had been Umaril's slave/material for his artwork;
- Mary is Varla's mother;
- Mary was burned by the Alessian Order led by Pepe;
- Korn is Mara's wolf/avatar accompanying Mary.

This is valuable supplementary context for the already-existing Varla and Mary dossiers and should be layered beside, not over, memory testimony.

### Slave Trader

The article says the Slave Trader is the soul of the hero from Vicn's earlier *LST Bravil Underground* and that his life ended with writing a poem.

This may explain the cryptic note trail and final poetic note, but because it crosses into Vicn's older-work continuity it needs an explicit continuity/provenance boundary before being merged into the VIGILANT-only ontology.

### ??????? / Akatosh

The article identifies ??????? as an avatar of Akatosh whose memory was lost by people but retained by the Lizard.

This supplements the ESM's unresolved/obscured `???????` memory form.

### Additional organization notes

The article also identifies:
- **Holy Pipers** — extremist branch of the Templars of Stendarr, excommunicated and torture-obsessed;
- **Chick Traders** — Elsweyr slave-trading organization exploiting the Civil War;
- **Sacred Anatomancer** — a simulacrum/radiance-of-Life concept tied to the player and Holy Pipers.

These belong to later/epilogue organization ingestion, not the core ESM-only faction layer.

## Comment-thread Owl notes

In the article's comment thread, a123999 later gives additional Owl identifications:
- Black Owl = Orlando the Knowledgeable / a tentacle of Hermaeus Mora;
- Gray Owl = a boy who survived the Night of Tears;
- White Owl = a familiar of Julianos;
- Gray Egg = the Gray Owl.

A later reply adds that Vicn described the Gray Jhunal as a dummy/puppet reformed by Orlando and formerly a boy from Saarthal.

These are valuable but **lower-confidence than the article body** because they occur in comments and partly report later cross-mod/Vicn explanations.

Store them as:
`supplementary_commentary`
rather than direct VIGILANT ESM fact.

## Owl comment-thread correction from later direct ESM evidence

The article's comment thread included informal identifications such as:
- Black Owl = Orlando the Knowledgeable;
- White Owl = a familiar of Julianos.

Later direct GLENMORIL and UNSLAAD ESM-derived evidence is more precise and should outrank those shorthand comments:

- GLENMORIL: **White Owl → Jhunal the White**
- GLENMORIL: **Black Owl quest speaker → Jhunal the Black**
- GLENMORIL: Gray Owl actor uses an Orlando-family form
- UNSLAAD: **Jhunal the Gray explicitly calls himself the Gray Owl**

Therefore those older comment-thread identities are retained only as historical supplementary commentary, not as current Lorekeeper identity conclusions.

See:
- `analysis/vicn-owl-continuity-bridge.md`

## Lorekeeper usage rule

When this source resolves an ESM gap, phrase answers like:

> The shipped VIGILANT records currently preserved in Lorekeeper do not state this directly, but a123999's supplementary VIGILANT background article identifies ...

Do not erase ESM uncertainty just because supplementary commentary supplies an intended identity.

## Source boundary

This file is a provenance record for supplementary interpretation. It is not a replacement for:
- exact VIGILANT ESM dialogue;
- books;
- Papyrus;
- scene/alias structure;
- licensed TES canon sources.
