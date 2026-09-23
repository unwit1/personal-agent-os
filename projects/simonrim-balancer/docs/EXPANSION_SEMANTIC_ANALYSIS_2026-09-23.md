# Simonrim Expansion Semantic Analysis — 2026-09-23

This checkpoint completes the first semantic exhaustion pass for the 17-mod Simonrim expansion supplied on 2026-09-23. It is append-only and does not rewrite the original Adamant / Hand to Hand / Blade and Blunt / Mysticism snapshot.

## Scope

Supplied mods: Adamant Bard Addon 1.1.0, Aetherius 2.15.1, Apothecary 1.3.9, Apprentice 1.1.0, Arena 1.2.0, Artificer 1.0.11, Candlehearth 1.1.1, Crusader 0.6, Gourmet 1.2.0, Manbeast 2.1.1, Mercantile 1.0.0, Pilgrim 1.3.1, Power Attack Speed Perks 1, Scion 2.2.2, Sorcerer 1.1.0, Starfrost 2.0.0, and Stormcrown 1.1.17.

## Exhaustion boundary

The supplied expansion now has an explicit treatment for every plugin record:

- 9,769 records across 68 record types
- 0 unmapped record types
- 8,988 semantic gameplay records
- 216 typed support / routing records
- 236 keyword identity records
- 276 presentation / navigation inventory records
- 53 plugin headers / provenance records
- 0 parser-error files

The source layer also contains 12 BSAs / 898 members, 239 PSC source occurrences (202 unique by hash), 2,046 decoded configuration values, and 55 FOMOD options.

## Behavioral decoding

All 935 VMAD payloads decode with exact byte consumption:

- 1,121 script attachments
- 3,953 typed properties
- 386 fragments
- 83 quest aliases
- 690 attachments matched to supplied PSC source
- 0 VMAD failures

This makes runtime behavior first-class evidence rather than an inferred property of numeric records.

## Major mechanic coverage

The expansion adds direct evidence for:

- Arena encounter-zone levels and flags
- Aetherius racial base stats, racial spells and optional NPC absorption
- Apothecary ingredients, ingestibles and distribution
- Apprentice class/trait implementation, race integrations and alternate variants
- Artificer artifact armor, weapons and enchantments
- Candlehearth dialogue and world edits
- Gourmet cooking, vendors, leveled lists and compatibility distribution
- Manbeast werewolf effects/perks
- Pilgrim religion, perk trees, shrine placement and compatibility options
- Scion vampire effects/perks
- Sorcerer staff/scroll crafting and perk infrastructure
- Starfrost survival, hunger/injury behavior and integration
- Stormcrown shout/word/spell behavior
- the supplied small Simonrim integration/add-on plugins

## Internal override evidence

Within this expansion, 187 records have an exact supplied parent-plugin baseline because the current plugin actually masters another supplied plugin.

- 125 differ at the raw record level
- 62 are identical forwards
- 156 have deterministic semantic projections
- 99 are semantically modified
- 57 are semantically identical

Another 342 sibling-override pairs are tracked separately. They are not called parent-child deltas because no master relationship establishes that direction.

## Observed patterns and candidate layer

The first deterministic review pass produced:

- 363 repeated implementation profiles
- 42 non-boilerplate author/FOMOD statements
- 405 review candidates
- 93 review families
- 52 multi-candidate families
- 32 cross-mod families
- approved rules: **0**

Notable cross-mod review families include constant-effect ability structures, magic-effect archetype/cast/delivery profiles, leveled-list structures, perk structures, race base-stat profiles, armor/enchantment conventions, ingestible structures and weapon profiles.

## Example implementation findings

These are implementation observations, not approved rules:

- Arena's 321 encounter zones are strongly concentrated at minimum levels 5, 10, 15, 20, 25 and 30, with zero-valued max levels throughout the supplied plugin.
- Aetherius differentiates player-race starting Health/Magicka/Stamina profiles and embeds racial spell behavior rather than expressing every race as the same base-stat template.
- Stormcrown supplies 28 shout records plus 6 new Words of Power in the supplied version; the new Lightning Breath and Poison Breath shout records use 30/45/60-second recovery triples.
- Apprentice's installer explicitly identifies traits intended to interoperate with Blade and Blunt, Pilgrim and Gourmet, and provides variants that change race/class behavior.
- Starfrost's Injury Integration Addon explicitly depends on Blade and Blunt, Mysticism, Apothecary and Pilgrim, providing direct suite-integration evidence.
- Gourmet's installer explicitly links its Survival Mode patch to Starfrost.

## Edge cases preserved

Four Starfrost MGEF records contain no DATA payload. They are retained as empty/placeholder implementation records rather than counted as decoder failures.

Two duplicate plugin occurrences in installer paths are retained for provenance but hash-deduplicated for logical comparison.

## Rule guardrails

- A repeated numeric profile is not an approved rule.
- Optional modules and compatibility patches retain their narrow scope.
- Cross-mod recurrence does not prove author intent.
- Installer text is strong explicit-source evidence but still requires implementation/scope review for rule promotion.
- Presentation/navigation data cannot independently create balance rules.
- Missing Skyrim/Update/DLC/Creation baseline bodies are never guessed.
- Approved Simonrim design rules remain **0**.
