# Speaker resolution — pass 02

The first speaker pass was intentionally conservative: it treated every positive GetIsID condition in an INFO record as a potential speaker check. That under-resolved dialogue because Skyrim dialogue conditions also run GetIsID against references/targets that are not the speaker.

## Improved deterministic rule

A named speaker is now resolved only when all of the following are true:

1. the INFO belongs to a mod-added Dealing with Daedra record;
2. the condition function is GetIsID (function 72);
3. the comparison is Equal 1;
4. the condition runs on Subject (run-on 0), which is the dialogue speaker;
5. exactly one unique NPC FormID satisfies those positive Subject checks.

This avoids mistaking target/reference conditions for speaker candidates.

## Coverage

- Mod-added INFO records: 1,807
- Deterministically resolved to one Subject NPC: 1,636
- INFO resolution: 90.5%
- Total dialogue response strings in plugin: 2,674
- Responses covered by resolved INFO: 2,472
- Response-text coverage: 92.4%

The remaining 171 INFO records are deliberately left unresolved at the individual-NPC level.

Of those, 47 contain a positive Subject GetInFaction condition and are better treated first as faction/generic-role dialogue rather than guessed onto a named actor. The rest rely on broader conditions, generic base-game roles, staged state, race/location checks, or other contextual routing.

## Consequence for earlier dossiers

Pass-01 named-speaker dossiers remain valid. This pass mainly recovers additional dialogue that had multiple GetIsID conditions because non-speaker references were being tested in the same INFO.

This method is reproducible directly from the ESP and should replace the older "exactly one GetIsID anywhere in the INFO" rule.
