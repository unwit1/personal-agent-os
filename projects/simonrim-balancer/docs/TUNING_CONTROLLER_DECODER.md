# Global Tuning / Controllers / Reversion Decoder — 2026-09-23

## Coverage

- GMST/GLOB settings: 118
- Cross-module semantic setting comparisons: 18
  - modified: 8
  - identical: 10
- IDLE records: 16
- Same-vanilla-form Blade and Blunt vs No Killmoves comparisons: 4
- QUST records: 10
- Quest stages: 11
- SMQN story-manager quest nodes: 6
- Story-manager quest links: 5
- MESG records: 15
- Decode failures: 0
- Approved rules: 0

## Semantic setting identity

GMST records are compared by their game-setting EDID rather than only by FormID. GLOB records remain FormID/canonical-identity based.

This is necessary because optional modules can ship a local GMST record with the same engine setting name rather than a normal FormID override.

## Important module comparisons

### Adamant Smithing
Compared with Adamant's same semantic settings:
- fSmithingArmorMax: 10.0 -> 8.9
- fSmithingWeaponMax: 10.0 -> 6.1
- fSmithingConditionFactor: unchanged

### Blade and Blunt — No Sprint Changes
- fSprintStaminaDrainMult: 0.0 -> 8.0

This is direct reversion-module evidence and should not be mixed into the main Blade and Blunt baseline.

### Blade and Blunt — Vanilla difficulty sliders
The optional BBVanillaSliders plugin changes five of the twelve same-name Blade and Blunt difficulty multipliers and forwards seven unchanged. Its package path/name indicates a vanilla-difficulty-modifier option, but the current FOMOD semantic mapping did not supply an explicit module role, so that interpretation remains derived metadata rather than silently rewriting source provenance.

### No Killmoves
Four BBNoKillmoves IDLE records share canonical Skyrim Forms with BladeAndBlunt.esp. Animation file/event/parent metadata is unchanged; their CTDA condition fingerprints differ. This is modeled as a sibling-override comparison because BBNoKillmoves does not master BladeAndBlunt.esp.

## Controllers

The QUST + SMQN layer now identifies controller startup structures separately from their Papyrus behavior:

- Adamant controller / treasure-hunter / perk quests
- Adamant Smithing controller node
- Simonrim Attack Speed Fix controller node
- Blade and Blunt controller node
- Hand to Hand controller node
- Mysticism controller infrastructure
- Mysticism slower-unlocks skill event quest

The already-decoded VMAD layer supplies script, fragment and alias behavior links for these quests.

## Guardrails

- Reversion/compatibility settings are scoped to their optional module.
- Sibling overrides are not called parent-child deltas unless a real master relationship exists.
- Story-manager placement proves startup/routing structure, not the meaning of the script body.
- No tuning value is automatically an approved design rule.
