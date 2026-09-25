# Skyrim Mod Factory — Feature Intent and Compatibility Touch Sets

Created: 2026-09-24
Status: schemas + first-pass overlap detector implemented

## Feature intent

`skyrim-feature-intent-v1` captures the design question before implementation details obscure it.

It records:
- observable behavior;
- triggers;
- forbidden behavior;
- target populations;
- constraints;
- implementation choice and rejected alternatives;
- persistence/performance expectations;
- acceptance criteria.

The important field is **acceptance criteria**. Every feature should state how completion can be proven.

Examples:
- static: generated MGEF has intended archetype/flags;
- runtime: qualifying bandit receives perk;
- negative: non-bandit does not receive perk;
- persistence: state survives save/load;
- performance: 50-actor stress fixture remains within budget;
- visual: mesh has no clipping under defined poses;
- compatibility: Simonrim-owned field remains unchanged.

Acceptance criteria drive fixture/test generation.

## Touch set

`skyrim-compatibility-touchset-v1` describes what a project can affect:

- record signatures/FormKeys/field paths;
- asset paths;
- runtime mutation domains;
- native hook surfaces;
- UI surfaces;
- save state;
- generated outputs.

This is more useful than saying two mods are both "combat mods."

Two combat mods can be independent if one edits weapon damage and one replaces hit reactions; two unrelated-looking mods can conflict if both own `NPC_.ACBS` or the same skeleton path.

## First-pass comparator

`tools/skyrim_mod_factory/compare_touchsets.py` reports likely overlap for:
- same FormKey + overlapping field paths;
- same asset path;
- same runtime mutation domain/selector;
- same declared native hook surface.

It intentionally does **not** call overlap a conflict.

Next-stage compatibility reasoning should classify:
- compatible independent edits;
- intentional override;
- merge/patch required;
- ordering required;
- runtime interaction;
- mutually exclusive;
- unknown / fixture required.

## Project workflow

For every project:
1. capture feature intents;
2. select architecture;
3. derive touch set;
4. compare with known dependencies/modlist;
5. generate compatibility patches/rules where deterministic;
6. turn remaining ambiguous overlaps into fixtures.

## Dynamic targets

When a runtime rule selects forms dynamically, touch set may use a selector instead of enumerating every FormKey.

For a concrete user load order, a resolver should expand selectors to the observed target set and compare the resolved touch set as a build artifact.

## Long-term use

The Simonrim Balancer can export Simonrim touch sets and field-ownership conventions.

Then new user mods can automatically answer:
- which Simonrim systems they overlap;
- which fields should be preserved;
- whether runtime distribution avoids a static conflict;
- what compatibility fixture should be generated.
