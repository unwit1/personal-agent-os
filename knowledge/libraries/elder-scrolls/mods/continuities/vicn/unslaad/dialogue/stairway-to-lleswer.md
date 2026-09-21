# Stairway to Llesw'er — dialogue and endpoint

Quest: zzzCrbMq06 / 031DFDFA
Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

## Quest objectives

- Return to Ja'cobee
- Retrieve Ja'cobee's remains

## Dialogue

INFO 031DFE08 — Ja'cobee:
- says Lizz has met Ulliss and that this is good.

INFO 031DFE0A — Ja'cobee:
- says it is his time to leave;
- says he was usually the one seeing others off and now accepts being seen off himself;
- rejects gold and corpses as the reason he chose this place;
- says he feels cleansed and perhaps finally forgiven;
- says Aisha is waiting for him.

INFO 031DFE0E — Ja'cobee:
- says he finally understands that his path has always been "on the whispering winds";
- names it Khenarthi's path.

## Remains

ACTI 031DFE11 / zzzCrbMq06TrigRemain is explicitly named Ja'cobee's Remains.

A later inspection message, MESG 031DD5B5 / zzzCrbMsgInsightKhajiitBodies, identifies nearby bodies as Ja'cobee and Aisha and says both are dead with contented expressions, as if they accomplished everything they intended.

## Llesw'er / Khenarthi context

The quest title directly invokes Llesw'er, while Ja'cobee explicitly invokes Khenarthi and whispering winds. The existing Elder Scrolls source library independently contains Khajiiti traditions connecting Khenarthi with guiding worthy Khajiit to the land beyond the stars / Llesw'er.

UNSLAAD's endpoint therefore deliberately uses recognizable Khajiiti afterlife imagery. The library should preserve the UNSLAAD scene itself separately from outside theological sources rather than assuming every detail maps one-to-one.

## Relationship to the two-Ja'cobee statement

Immediately before this quest, Ja'cobee tells Lizz there are two Ja'cobees and that the other is already "on the other side." Stairway to Llesw'er then presents the living Ja'cobee as preparing to die/pass on and directs the player to retrieve his remains.

The source establishes duplication/other-side language and subsequent death. It does not yet explain whether the "other Ja'cobee" is:
- a soul,
- a temporal counterpart,
- a dream copy,
- a metaphysical double,
- or something else.

Keep the mechanism unresolved.

## Endpoint closure

The endpoint is fully ingested at the level supported by the ESM:

- Ja'cobee chooses to leave/die;
- he explicitly invokes Khenarthi's path and says Aisha is waiting;
- the quest asks for his remains;
- the inspection record identifies Ja'cobee and Aisha together after death.

The earlier **two Ja'cobees / other side** statement has no source-level mechanism attached to it in the current corpus.

Classify that mechanism as intentionally unresolved:
- soul;
- temporal counterpart;
- dream copy;
- metaphysical double

are hypotheses, not extracted facts.

This question should not remain in the active ingestion queue unless new direct evidence appears.
