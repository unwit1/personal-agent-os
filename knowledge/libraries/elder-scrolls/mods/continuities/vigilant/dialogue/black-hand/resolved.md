# Black Hand — resolved direct dialogue

Source:
- user-supplied translated `Vigilant.esm`
- translation archive version: 1.8.2 / 2026-06-16

## Direct actor

Primary actor:
- `NPC_ 021E3F62`
- EditorID `zzzCHBossBlackHand`
- display name **Black Hand**
- race `RACE 021E5405` / **Black Hand Race**
- placed as `ACHR 021E40BE`
- location **Ossuary** (`CELL 021E3F63`)

Secondary actor:
- `NPC_ 023288E7`
- EditorID `zzzCODregsBlackHand`
- display name **Black Hand**
- same Black Hand race
- placed as `ACHR 023288E8`
- location **Bruiant Mansion South Wing** (`CELL 023239B1`)

## Dedicated topic

`DIAL 021EA206` / `zzzCHgdBlackHandB01T01`

INFO 021EA207:
> ............

INFO 021EA208:
> Ah, even burnt you are still sane. This explains why my voice could not reach you.

Second response:
> I am the Black Hand, the unwanted child of the endless Void...

The INFO conditions directly reference:
- `ARMO 020D957B` / **Sithis' Eye Ring**
- `NPC_ 021E3F62` / **Black Hand**

## Ring-gated hello

Generic hello DIAL:
- `DIAL 0212850A` / `zzzCHgdHello`

INFO 021EA209:
> Father Sithis is with us. Now, what do you wish from me?

This INFO:
- points into the Black Hand topic;
- carries conditions referencing the Sithis' Eye Ring and Black Hand actor.

## Ring reaction system

`MESG 022313C2` / `zzzCHMsgSithisRingReaction`

> Sithis' Eye Ring is reacting to the Black Hand...

Associated trigger:
- `ACTI 022313C8`
- `zzzCHSithisEyeReactionTrigger`

## Direct identity conclusions

The ESM directly supports:

- Black Hand calls itself a **child of the endless Void**.
- Black Hand calls Sithis **Father**.
- Sithis' Eye Ring detects/reacts to Black Hand.
- Black Hand is implemented through a dedicated race and ability/stat family.
- at least two Black Hand actor forms are placed in the world.

## Source boundary

The a123999 claim that the Black Hand are **five children of the Night Mother** remains supplementary.

The recovered direct dialogue is compatible with a child/Sithis/Void ontology but does not itself state:
- exactly five Black Hands;
- Night Mother maternity.
