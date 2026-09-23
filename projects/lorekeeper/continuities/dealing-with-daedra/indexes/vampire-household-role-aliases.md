# Vampire household role aliases

Continuity: tes.mod.dealing-with-daedra
Purpose: deterministic retrieval across enable-parent/state variants in the Book of Curses arc.

The ESP implements several narrative characters as multiple NPC base forms that are enabled/disabled as the storyline progresses. These should not be treated as separate lore characters merely because their FormIDs differ.

## Vampire Master

Narrative role: Vampire Master / Vampire Lord

NPC forms:
- 055075A9 — dealsvamplord1 — "Vampire Lord"
- 055075AA — dealsvamplord2 — "Master"
- 055075AB — dealsvamplord3 — "Master"
- 05520B49 — dealsvamplord4 — "Master"
- 05520B4A — dealsvamplord5 — "Master"
- 05520B4B — dealsvamplord6 — "Master"
- 05520B4C — dealsvamplord7 — "Master"
- 0552AD88 — dealsvamplord8 — "Master"

All are members of faction 055075A7 (dealsvampfaction / vamphubfaction), use the same Vampire Lord race/voice configuration, are placed as alternate actors in the same Master's Lair cell, and represent successive quest states.

## Frysla

NPC forms:
- 055075AC — dealsvampthotA1 — recruitment/inn state;
- 055117DE — dealsvampthotA2;
- 055117E1 — dealsvampthotA3;
- 055117E0 — dealsvampthotA4;
- 0551181F — dealsvampthotAvig.

The post-recruitment forms are placed in the Master's Lair and share the same identity/name. Treat them as one Frysla character with state variants.

## Serra

NPC forms:
- 055075AD — dealsvampthotB1;
- 055117E2 — dealsvampthotB2;
- 055117E3 — dealsvampthotB3;
- 055117E4 — dealsvampthotB4;
- 0551181D — dealsvampthotBvig.

These are likewise state variants of one Serra identity.

## Retrieval rule

When an INFO contains multiple positive Subject GetIsID conditions joined as alternatives and every candidate belongs to one of the identity groups above, resolve the dialogue to the narrative role rather than marking it ambiguous.

Example:
INFO 05534FC6 permits Master forms 05520B49 or 05520B4C. Both are the Vampire Master, so the line "No, slave. If you want to learn more curses then go find me more pages." is role-resolved even though it is not single-FormID-resolved.

Do not generalize this rule merely from identical display names. Generic "Escort", "Patron", "Recruiter", or similar records may represent genuinely different people. Role collapse requires explicit identity/state evidence.
