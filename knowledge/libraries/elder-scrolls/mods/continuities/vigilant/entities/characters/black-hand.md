# Black Hand — direct VIGILANT encounter

- Continuity: `tes.mod.vigilant`
- Primary boss form: `NPC_ 021E3F62` / `zzzCHBossBlackHand` — **Black Hand**
- Secondary form: `NPC_ 023288E7` / `zzzCODregsBlackHand` — **Black Hand**
- Race: `RACE 021E5405` / **Black Hand Race**
- Direct location:
  - boss `ACHR 021E40BE` → **Ossuary** (`CELL 021E3F63`)
  - secondary `ACHR 023288E8` → **Bruiant Mansion South Wing** (`CELL 023239B1`)
- Ring: `ARMO 020D957B` / **Sithis' Eye Ring**
- Reaction message: `MESG 022313C2`
- Direct source: translated VIGILANT 1.8.2 ESM supplied by user

## Direct implementation

The Black Hand is not merely a supplementary concept.

VIGILANT directly implements:

- **Black Hand Race**
- **Black Hand fx**
- **Black Hand abilities**
- **Black Hand Health**
- **Black Hand Stamina**
- **Black Hand Magicka**
- **Black Hand Perk Point**
- at least two NPC forms named **Black Hand**

This is a bespoke encounter identity/system.

## Boss placement

The main Black Hand boss:
- `NPC_ 021E3F62`
- is placed as `ACHR 021E40BE`
- inside **Ossuary**.

A second Black Hand form:
- `NPC_ 023288E7`
- is placed as `ACHR 023288E8`
- in **Bruiant Mansion South Wing**.

Both use the dedicated Black Hand race.

This supports more than one Black Hand manifestation/body.

## Sithis' Eye Ring reaction

VIGILANT contains:

- `ARMO 020D957B` — **Sithis' Eye Ring**
- `ACTI 022313C8` — `zzzCHSithisEyeReactionTrigger`
- `MESG 022313C2` — **“Sithis' Eye Ring is reacting to the Black Hand...”**

The Black Hand dialogue INFO conditions directly reference:
- the Sithis' Eye Ring;
- the boss Black Hand NPC.

Therefore the ring ↔ Black Hand reaction is not merely thematic: it is conditionally implemented in the ESM.

## Direct dialogue

The Black Hand's dedicated dialogue topic:
- `DIAL 021EA206` / `zzzCHgdBlackHandB01T01`

contains:

`INFO 021EA207`
- “............”

`INFO 021EA208`
- “Ah, even burnt you are still sane. This explains why my voice could not reach you.”
- **“I am the Black Hand, the unwanted child of the endless Void...”**

A generic hello path additionally contains:

`INFO 021EA209`
- **“Father Sithis is with us. Now, what do you wish from me?”**

This directly establishes:
- Black Hand self-identification;
- parent/father language toward Sithis;
- Void-child identity language.

## Night Mother / five children boundary

The a123999 supplementary article describes the Black Hand as:
- five young children of the Night Mother;
- guides for dead/cursed mortals toward Sithis.

The newly recovered ESM dialogue directly supports:
- **child of the Void**
- **Father Sithis**

but does not, in the currently extracted lines, directly state:
- there are exactly five;
- the Night Mother is their mother.

Therefore the best source-separated model is:

### Direct VIGILANT
**Black Hand = bespoke Sithis-linked entity/class that calls itself an unwanted child of the endless Void and calls Sithis Father.**

### Supplementary
**Black Hand = one of five young children of the Night Mother, guiding cursed/dead mortals toward Sithis.**

The supplementary model is now much more compatible with direct ESM evidence, but the “five / Night Mother” elements remain supplementary until exact ESM text says so.

## Multiple manifestations

The ESM has at least:
- boss Black Hand in Ossuary;
- second Black Hand in Bruiant Mansion South Wing.

This may reflect:
- multiple Black Hands;
- repeated manifestations;
- one identity appearing through multiple bodies.

The current ESM records alone do not settle which.

Avoid forcing singular or plural ontology.

## Relationship to Sithis

Direct evidence now strongly establishes:

- **Black Hand → calls Sithis → Father**
- **Black Hand → calls itself → child of endless Void**
- **Sithis' Eye Ring → reacts to → Black Hand**

This is stronger than the earlier indirect faction model.

## Relationship to Manthar

Manthar can carry/drop Sithis' Eye Ring.

That item connection does not prove Manthar is a Black Hand.

Keep:
- item-system participation
separate from:
- Black Hand identity.

## Canon boundary

VIGILANT's Black Hand race, bodies, dialogue, ring reaction, and Void-child/Sithis relationship are mod-continuity implementation.

Do not equate this metaphysical Black Hand automatically with the Dark Brotherhood's ordinary organizational rank called “Black Hand.”
