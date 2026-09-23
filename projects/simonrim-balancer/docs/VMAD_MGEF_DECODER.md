# MGEF VMAD Script / Property Decoder

## Scope

This checkpoint decodes generic Papyrus VMAD payloads on MGEF records only. QUST fragments/aliases and VMAD on PERK, NPC_, ARMO and ACTI are deliberately deferred.

All supplied MGEF VMAD records use VMAD version 5 and object format 2. Observed property types in this slice are Object, String, Int32, Float and Bool; no arrays occur.

## Results

- 395 / 395 MGEF VMAD records decode to exact byte consumption; 0 failures and 0 trailing bytes.
- 416 script attachments across 115 distinct script names.
- 1,067 typed properties.
- Property mix: 915 Object, 83 Float, 33 Int32, 33 Bool, 3 String.
- 915 object-property relations resolve to canonical Form identities; 0 unresolved targets.
- 4 Object properties use a non--1 alias binding and preserve both the target Form and alias ID.
- 234 / 416 attachments match supplied PSC source; 80 / 115 distinct attached names have supplied source.
- 31 exact imported-baseline VMAD comparisons: 30 modified and 1 identical forward.

## Behavioral delta evidence

The exact delta layer detects script replacement as well as property changes. Examples include Adamant Bound Bow effects replacing BoundBowEffectScript with MAG_BoundBow_Script, and multiple Power Surge effects replacing magicAttachAshPileOnDeath with MAG_PerkPowerSurge_Script. These are implementation facts, not inferred author intent.

## Source cross-checking

When a matching PSC is present in the supplied BSAs, attached property names are checked against parsed source declarations. Missing source is recorded as evidence availability, not treated as a broken attachment. Property/source mismatches remain explicit for later investigation.

## Architecture consequence

VMAD is now a first-class behavior-evidence layer:

MGEF -> attached script -> typed property -> referenced Form or scalar value.

This lets future design queries combine static spell/magic-effect numbers with runtime behavior and configured script properties. Numerically similar effects must not be assumed equivalent when their script configuration differs.

## Rule status

No script choice, attachment frequency or property value is an approved Simonrim rule.
