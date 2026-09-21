# Pelan → Inquisitor Pepe transformation

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass asks two questions:

1. how firmly does VIGILANT identify **Pelan** with **Inquisitor Pepe**?
2. what does the ESM actually say about Pelan becoming “less and less human”?

## Identity: Pelan = Pepe

The strongest explicit line is:

- `INFO 02234DC6` — Giant Knight Ritho identifies Pepe as **“bishop Pelan.”**

This is direct in-world identification, not merely a thematic resemblance.

Independent evidence reinforces it:

- `BOOK 020CB0DF` / *The Eight Saints of Cyrod* says Pelan found Marukh in the jungles of Colovia.
- Pepe later says he met Marukh in the Colovian jungle.
- Pepe recounts going there while he still served the Eight Divines after hearing of the Imga prophet.
- `INFO 02244BD6` — Arasil says Pepe had been a priest of the Eight Divines and was kind-hearted until returning from the jungles of Colovia.
- Pepe repeatedly speaks as someone who has survived for centuries and eventually thousands of years.

Current classification: **Pelan = Bishop Pelan = Inquisitor Pepe is high-confidence within VIGILANT.**

The ESM still does not explain why the name/title changed from Pelan to Pepe.

## The four Petition to House Tharn volumes

The sequence is:

- `0251D5CB` — Vol. 11
- `0251D5CC` — Vol. 23
- `0251D5CD` — Vol. 68
- `0251D5CE` — Vol. 77

All four are titled *Petition to House Tharn* and list the author as **Unknown**. Their contents are dialogue transcripts between **Pelan** and **Amicus**.

They should therefore be treated as documentary reconstructions/transcripts rather than Pelan-authored memoirs.

### Vol. 11 — Belharza and manufactured history

Pelan objects to the imprisonment and rewriting of Belharza.

He:
- treats the Amulet of Kings as evidence for Belharza's legitimacy;
- describes Morihaus as an ancient spirit rather than a simple beast;
- rejects the Order's attempt to fabricate a replacement Belharza;
- objects to slaughtering Ayleids in order to erase inconvenient memories of Alessia, Morihaus, and Pelinal.

Amicus openly argues for fabricating memory and history so belief can reshape divine forms.

### Vol. 23 — racial exclusion and artificial heaven

Pelan opposes the removal of citizenship from elves, giants, minotaurs, and other non-human peoples.

He argues that:
- non-human peoples helped create Alessia's Empire;
- Alessia's ideal was coexistence and development rather than extermination;
- the Order's proposed program contradicts that ideal.

Amicus describes a much more radical project:
- separating Auriel from Akatosh;
- erasing elven history and non-human peoples;
- reforging the Heart of Shezarr;
- remaking the Aurbis around a human-only “heaven.”

Pelan explicitly calls this insane.

### Vol. 68 — Prisoners and the rejection of salvation

Pelan objects to executions of unidentified prisoners, including people claiming to be **Periff**.

Amicus describes the “Prisoner's” ability to create the future they want and says the Order rejects such salvation because it would destroy what the Order built.

Pelan describes the Order's achievement as a pile of corpses and still insists that the Order has the **Word**, rather than only coercive authority.

### Vol. 77 — memory failure and the Stone

The last preserved petition is the critical transition point.

Pelan and Amicus discover that neither can actually remember the Seventy-Seven Doctrines coherently.

Pelan remembers:
- a blood-covered cliff;
- Marukh already being dead;
- other Imga interpreting one bloody image in more than seventy-seven ways;
- Marukh later pointing at Akatosh, declaring Auriel unworthy, vomiting up a burning Stone, and collapsing back into a mangled corpse.

Amicus says the Stone chose them.

Pelan answers:

**“I was chosen. It chose me.”**

This is the clearest early evidence that Pelan's later fate becomes entangled with the Stone.

## Memory-form chronology

The ESM makes Pelan/Pepe's bodily change visible through different NPC records.

### Memory 1 — The Grand Inquisitor

`NPC_ 0212BF48` / `zzzCHInquisitorPepeMemory`:
- display name: **Inquisitor Pepe**
- used by `QUST 0212C4F4` / *The Grand Inquisitor*
- uses a master-game humanoid race
- does **not** use Pepe's custom Sleeper skin/body.

This is an early, still-human representation.

### Memory 5 — Adabal

`NPC_ 0205ADFD` / `zzzCHInquisitorPepeMemory2`:
- used by `QUST 0205AE03` / *Adabal*
- templates from the earlier memory form;
- retains the same ordinary humanoid race.

In the Pepe dialogue branch, the player asks him to get rid of the Stone and hide it where no one can find it. Pepe agrees and swears on Mara's name.

At this point the ESM still represents him as physically human.

### Memory 6 — Remains of the Miracle

`NPC_ 0206A230` / `zzzCHInquisitorPepeMemory3`:
- used by `QUST 0206A23B` / *Remains of the Miracle*
- now uses `RACE 020818A6` / **Alessian Sleeper Race**
- now uses Pepe's custom body/skin through `ARMO 02108EB1` / `zzzCHSkinPepe`
- templates from the present-day Pepe identity.

This is the first memory form in the checked sequence that uses Pepe's visibly transformed body.

## “I changed considerably”

`INFO 0206B54F` in *Remains of the Miracle* is unusually explicit.

Asked whether he is Pepe, he confirms that he is and says he has **changed considerably**.

The same conversation establishes that centuries have passed.

When threatened with execution, Pepe says:

- he held the Stone for too long;
- he is now an **empty shell without a soul**;
- the interrogator should learn from the **monster** standing before them and stop grasping for the Stone.

This is the strongest direct self-explanation of Pepe's transformation currently found in the ESM.

## Physical implementation

Present-day `NPC_ 02081E46` / **Inquisitor Pepe** uses:

- `RACE 020818A6` / **Alessian Sleeper Race**
- `ARMO 02108EB1` / `zzzCHSkinPepe`
- `ARMA 02108EB0` / `zzzCHNakedPepeAA`
- model: `actors\AoM\ep4\Alessian\Pepe.nif`

The Alessian Sleeper Race itself uses:

- `Actors\Hagraven\Character Assets\skeleton.nif`
- `Actors\Hagraven\HagravenProject.hkx`

This is concrete structural evidence that later Pepe is no longer implemented as an ordinary humanoid body.

The race is also used by other Alessian Sleeper/Inquisitor forms, so the Hagraven-based implementation should be read as an **Alessian Sleeper transformation class**, not a body type unique to Pepe.

## Longevity versus corruption

Two sources explain different parts of Pelan's long transformation.

### Saint tradition

*The Eight Saints of Cyrod* says:
- Alessia's blessing extended Pelan's life for thousands of years;
- his form gradually became less and less human.

### Pepe's own testimony

In *Remains of the Miracle*, Pepe says:
- he held the Stone too long;
- he became an empty shell without a soul;
- he regards his current body as monstrous.

These claims are compatible but not identical.

Current Lorekeeper interpretation:

- **millennial longevity** is attributed by the saint tradition to Alessia's blessing;
- **the monstrous/soulless state** is self-attributed by Pepe to prolonged possession of the Stone;
- the ESM does not prove that either explanation is complete.

## Pelan relics: correction

The plugin contains:

- `ARMO 02500DDC` — **Pelan's Mask**
- `WEAP 020EA4C2` — **Staff of St. Pelan**

These establish a later Pelan relic/saint tradition, but they are **not** direct identity evidence for Pepe.

### Pelan's Mask

The mask is referenced by:
- a crafting recipe;
- a leveled collectible list.

No structural record currently shows primary Pepe wearing it.

### Staff of St. Pelan

The staff is structurally carried by:
- `NPC_ 020EA4C5` / **Archpriest Centius**

It also participates in a dedicated reaction trigger/script.

Therefore the staff is a relic named for Pelan, not evidence that Pepe personally wields it in the present-day encounter.

## Current reconstruction

The strongest supported sequence is:

**Pelan meets Marukh in Colovia → becomes a major Alessian/Marukh associate → opposes the Order's increasingly revisionist and exterminatory program → discovers that the doctrines themselves are unstable/forgotten → accepts that the Stone has “chosen” him → remains physically human through the Adabal memory → keeps/hides the Stone → centuries pass → by Remains of the Miracle he has changed into the Alessian Sleeper/Pepe body → he attributes his soulless, monstrous condition to holding the Stone too long → he survives into present Coldharbour as Inquisitor Pepe.**

## Open questions

The ESM does not yet establish:

- why Pelan begins using the name **Pepe**;
- exactly when between Memory 5 and Memory 6 his body changes;
- whether the Stone literally removes his soul or whether “empty shell” is figurative/metaphysical testimony;
- how Alessia's blessing interacts with the Stone's corruption;
- whether the external Papyrus layer contains an explicit transformation event.

## Reliability

- **A structural:** Pelan/Pepe identity line from Ritho; memory-form race/skin change; quest assignments; present Pepe race/body; named relic records.
- **B testimony:** Pepe's statements about Colovia, centuries, holding the Stone, being soulless/monstrous.
- **C documentary:** *Petition to House Tharn* transcripts; *The Eight Saints of Cyrod* saint biography.
- **Unresolved:** complete causal mechanism of the transformation and the Pelan → Pepe name change.
