# Skyrim Mod Factory — Typed Runtime-Patch Intent

Created: 2026-09-24
Status: implementation in progress; SPID renderer available

## Why an intermediate representation

Framework config syntax should be generated output.

Canonical project intent should say:
- what is being distributed/swapped/keyworded/replaced;
- which forms are targeted;
- which semantic filters apply;
- expected recipients/results;
- framework/version selected.

This allows:
- schema validation;
- semantic diffs;
- deduplication;
- overlap analysis;
- conversion between implementation frameworks;
- grammar migration when a framework changes;
- fixture evaluation before launching the game.

## SPID v1 renderer

Implemented:
- `schemas/skyrim-runtime-patch-intent-v1.schema.json`;
- `tools/skyrim_mod_factory/render_spid.py`.

Current grammar evidence:
`powerof3/Spell-Perk-Item-Distributor/resources/SPID Complete Reference.txt`
blob snapshot should be recorded in the intent.

SPID's current reference defines:

`FormType = FormOrEditorID|StringFilters|FormFilters|LevelFilters|TraitFilters|CountOrPackageIndex|Chance`

Supported form types in that source snapshot include:
- Spell;
- Perk;
- Item;
- Shout;
- Package;
- Keyword;
- Outfit;
- SleepOutfit;
- Faction;
- Skin;
- generic Form type inference.

### SPID form identity

Prefer stable EditorIDs when appropriate.

Source reference also supports:
`0xLocalOrFormID~Plugin.esp`.

The Mod Factory should independently resolve the intended form and verify that the reference maps to the expected record type.

### Filter composition

Current SPID reference states:
- filter sections are multiplicative / logical AND with one another;
- expressions within a section are additive / logical OR;
- exclusion semantics require their own source-defined handling;
- only one Level expression is accepted, while additional skill expressions can coexist according to grammar.

The initial renderer preserves source expressions but does not yet parse every expression into a deeper AST. That deeper filter parser is a next implementation target.

### Chance

Current reference supports decimal 0–100 and `!` suffix for deterministic chance.

The semantic IR stores:
```json
{"percent": 50, "deterministic": true}
```
and renderer emits `50!`.

## Frameworks awaiting source-verified renderers

- KID;
- BOS;
- FLM;
- SkyPatcher;
- OAR.

Do not render these by copying SPID grammar. Each provider gets:
1. pinned parser/docs;
2. typed AST;
3. renderer;
4. parser/round-trip fixture;
5. framework-log validation.

## Future filter AST

Replace raw expression strings progressively with typed nodes:

```text
And
  FormHasFaction(BanditFaction)
  LevelRange(10, 50)
  Not(Keyword(ActorTypeGhost))
  Trait(Female)
```

Then:
- render to SPID syntax;
- render equivalent supported logic to another framework;
- evaluate against fixture NPCs/forms;
- compare predicted recipient set with framework runtime logs.

## Runtime overlap analyzer

Given all project intents:
- resolve target form identities;
- evaluate static filter intersections;
- identify multiple frameworks mutating the same field/form;
- predict explicit ordering where documented;
- mark dynamic/unknown interactions for runtime fixture testing.

## Config ownership

Generated `*_DISTR.ini`, `*_KID.ini`, etc. should contain a header indicating:
- generated file;
- source intent id;
- grammar snapshot;
- generator commit.

Manual edits to generated files should be detected as drift and either imported back into semantic intent or overwritten on rebuild.
