# Semantic pass 06 — batch 04: vampire household state forms

This batch resolves an implementation artifact that previously made the Book of Curses storyline look more ambiguous than it is.

The Master, Frysla, and Serra are each represented by multiple NPC forms tied to quest state/enable parents.

## Master

Eight forms represent one narrative Vampire Master across recruitment, page collection, late-game, and ending states.

This explains INFO records that contain alternative Subject GetIsID checks for multiple "Master" forms: those are state-compatible speaker checks, not evidence for multiple different masters.

## Frysla and Serra

Frysla and Serra likewise have several state forms, including Vigilant-ending variants.

Serra's direct dialogue is sparse but establishes willing identification with the household: after becoming a vampire she says the increased strength/speed and hunger are a worthwhile price for serving the Master (INFO 0553A102).

Frysla's forms bridge the recruitment state outside the lair and later household states inside it.

## Methodological consequence

Speaker resolution now has three levels:
1. exact NPC FormID resolution;
2. verified narrative-role resolution across state variants;
3. generic/faction role resolution where individual identity cannot be established.

This preserves deterministic attribution without falsely treating every same-name generic NPC as one person.
