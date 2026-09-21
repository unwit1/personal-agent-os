# Remaining VIGILANT dialogue — structural classification

This layer classifies all **89** INFO records that are not uniquely attributable after deterministic normalization. No personal speaker is assigned from wording alone.

## Categories

- **17** — dynamic/condition-filled quest aliases
- **15** — scene-bound placed/reference actors whose base identity is not uniquely recoverable from `Vigilant.esm` alone
- **13** — INFO aliases pointing to specific placed/reference forms
- **12** — location/ref-type aliases rather than fixed NPCs
- **10** — genuine structural conflicts between multiple NPC candidates
- **10** — dynamically filled scene aliases
- **4** — voice-type pools that do not narrow to one NPC
- **4** — external/master unique-actor references
- **4** — no usable speaker/alias/scene identity structure

Only **4/89** therefore lack usable identity structure entirely. The remaining records are still usable as quest-, role-, or scene-level evidence.

## High-value clusters

- **Johan the Fool:** the traveling bard dialogue introduces itself as **Bal**, but the speaker is routed through a location-derived alias. Record the bard persona's self-identification without silently converting the alias into a uniquely resolved Molag Bal NPC.
- **Beyond the Shores of Madness:** most unresolved narration is tied to placed scene roles such as Bard/Sheogorath memory actors. These are scene-role testimony, not objective narration.
- **Madness:** the KingShadow lines use dynamic scene aliases. Preserve them as a role cluster until location/runtime evidence resolves individual actors.
- **Sacred Anatomancer:** the exact quest body and report are now recovered from the supplied VIGILANT 1.8.2 ESM. Some gatekeeper/anatomancy lines remain alias/role-level rather than uniquely personal, but the source text is preserved at `dialogue/sacred-anatomancer/resolved.md`; see `analysis/sacred-anatomancer-source-gap.md` for the direct-source resolution.
- **Generic Minotaur Village:** greetings intentionally resolve to an ambient pool/multiple candidates; do not force them onto individual named Minotaurs.
- **Dine and Dash:** payment dialogue routes through a unique actor outside the locally resolvable VIGILANT NPC set; preserve it as innkeeper/payment-role dialogue.

## Four records with no usable identity structure

- `INFO 02008862` — *Lazy Afternoon* — no decoded response text.
- `INFO 022A534E` — *Pelinal the Bloody* — hostile line about enjoying killing.
- `INFO 022A5350` — *Pelinal the Bloody* — Mythic Era / Ada-blood line.
- `INFO 022A5352` — *Pelinal the Bloody* — threat to cleave the listener's head.

The three Pelinal-memory lines remain anonymous/unresolved rather than being assigned from their wording.

## Machine-readable companion

See `unresolved-classification.json` for every INFO FormID grouped by structural reason.

## Policy

An unresolved personal identity does not make the dialogue unusable. Lorekeeper should cite the INFO record, quest, scene/alias role when known, and the appropriate reliability class while leaving the personal speaker field null.
