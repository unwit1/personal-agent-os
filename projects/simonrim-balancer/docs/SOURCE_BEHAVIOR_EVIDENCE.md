# Papyrus / SKSE Configuration Behavior Evidence — 2026-09-23

This checkpoint joins author-supplied Papyrus source and loose configuration files back to the already-decoded plugin records and VMAD attachment graph.

## Coverage

- Papyrus source files: 115
- Parsed call sites: 705
- Named ActorValue / game-setting literals: 244
- Author comment lines retained as evidence: 138
- Script attachment rows: 473
- Attachments with supplied PSC source: 265
- Attachments without supplied PSC source: 208
- Distinct attached script names: 136
- Configuration entries: 129 across 8 files
- Approved design rules: **0**

A missing PSC body means that the source body was not supplied in these four archives. It does **not** mean the attachment is broken.

## Deterministic source behavior tags

The source pass identifies the presence of concrete API behavior without inferring authorial design law:

- spell management: 60 scripts
- global-variable mutation: 18
- timing / waits: 15
- ActorValue queries: 11
- runtime game-setting mutation: 10
- perk query/management: 10
- hazard/object placement: 6
- inventory manipulation: 6
- ActorValue mutation: 5
- lethal/disintegration behavior: 3
- animation control: 3

## High-signal implementation evidence

### Adamant runtime settings

`MAG_GameSettings_Script` and related source explicitly mutate engine settings:

- Quick Learner:
  - `fTrainingMultCost = 6.0` while the perk is present.
  - `fTrainingMultCost = 10.0` otherwise.
- Rune Mage:
  - `iMaxPlayerRunes = 1` with neither Rune Mage perk.
  - `iMaxPlayerRunes = 3` with Rune Mage I only.
  - `iMaxPlayerRunes = 5` with Rune Mage II.

These are exact runtime behaviors, not inferred numeric baselines.

### Adamant perk/controller behaviors

The supplied generated `QF_PerksQuest_0005F596` source explicitly:
- multiplies five Speech difficulty Globals by 0.1 for its Persuasion fragment;
- sets `SpecialLootChance` to 65 for the Treasure Hunter fragment;
- mutates additional perk/racial Globals.

`MAG_FireHazard_Script` provides explicit conditional behavior:
- Wildfire checks the perk, distinguishes dual casting, casts the appropriate spell, places the appropriate hazard, and assigns the caster as actor cause.
- Eruption requires its perk, target Health <= 50%, and a random roll <= 50 before casting its normal/dual-cast spell.

`MAG_Determination_Script` checks a blocked hit plus distance before casting the configured response spell on the aggressor.

### Hand to Hand runtime/config behavior

Papyrus:
- `MAG_PerkMisdirection_Script` changes `fPickPocketMaxChance` to 100 while active and restores it to 90.
- `MAG_PickpocketCap_Script` enforces the same 100/90 state on load depending on the relevant perk state.

SKSE INI:
- `fBonusXPPerLevel = 0.15`
- `fBaseXPHerHit = 3`
- `fSkillUnarmedDamageScalingFactor = 0.35`

These values are explicit implementation configuration.

### Blade and Blunt dynamic difficulty

The supplied level-monitor/tracker source writes difficulty multipliers at runtime. Across the level trackers, the incoming and outgoing damage multipliers move in staged increments rather than remaining fixed. The exact source lines are retained in `papyrus_runtime_mutations.csv`.

This runtime layer must be analyzed separately from static GMST values and from the optional Vanilla Sliders plugin.

### Blade and Blunt ActorValue framework

`BladeAndBlunt_AVG.toml` defines adaptive ActorValue aliases including:
- InjuryResist
- StaggerPower
- StaggerResist
- CritResist
- BleedResist
- MagickaResist
- StaminaResist
- SwordPoints
- StaggerPoints
- CastSpeed

It also declares mod-scoped inclusion mappings and maps several custom damage/resistance channels onto `ResistMagic`.

### Blade and Blunt stagger-slow implementation

`MAG_StaggerSlow_Script`:
- reads `onehandedskilladvance`;
- divides it by 100 for a weapon-speed scalar;
- applies/removes that value to `speedmult`, `weaponspeedmult`, and `leftweaponspeedmult`.

This is preserved as a concrete script algorithm.

### Mysticism Slower Unlocks

`WISkillIncrease02` reacts to skill-increase story events, checks Alteration, Conjuration, Destruction, Illusion, and Restoration against Apprentice/Adept/Expert/Master threshold Globals, and sets the corresponding school-tier distribution Global to zero when the threshold is reached.

This source behavior directly explains the optional module's leveled-list global gating decoded earlier.

### Mysticism spell behaviors

Examples preserved as source observations include:
- Banish Daedra: staged disintegration plus actor kill.
- Bound Shield: add/equip the bound shield, clean it up at effect finish, and restore the prior left-hand spell when applicable.
- teleport/recall: place portal objects and move references.
- frost slow: add/remove a helper spell for the effect lifetime.
- hazard casting: place configured hazard objects.
- Circle of Protection cleanup: cast a dispel spell.

## Configuration evidence classes

The 129 decoded config entries are classified as:
- SPID distribution: 28
- KID distribution: 4
- SKSE/runtime INI: 37
- ActorValueData TOML: 37
- Improvement Names JSON: 23

Distribution/config files are treated as executable configuration evidence, not documentation prose.

## Guardrails

- Source observations are not approved design rules.
- Comments are preserved as author evidence but are not treated as authoritative when code contradicts them.
- Missing source bodies remain explicit evidence gaps.
- Binary DLL/PDB internals are not inferred from configuration names.
- Static plugin values and runtime script/config mutation remain separate evidence layers until a query explicitly resolves their interaction.
