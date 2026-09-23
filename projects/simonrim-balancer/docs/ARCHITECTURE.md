# Architecture

## Evidence model

The balancer must not silently convert an implementation detail into a design law. Data moves through explicit stages:

| Stage | Meaning |
| --- | --- |
| raw | Byte-accurate or source-text evidence |
| decoded | Deterministic interpretation of a known field |
| projected | Normalized mechanic representation |
| observed_pattern | Statistical or repeated implementation pattern |
| rule_candidate | Proposed design rule with evidence links |
| approved_rule | Human-reviewed rule usable by the design assistant |
| exception | Intentional deviation that must not become a general rule |

No stage overwrites the previous one.

## Canonical entities

Source layer:
- ModVersion
- SourceArtifact
- Plugin

Bethesda record layer:
- Record
- Subrecord
- Relation

Mechanic projection layer:
- Spell
- MagicEffect
- EffectInstance
- Perk
- GameSetting
- Global
- Weapon
- Armor
- CraftRecipe
- LeveledEntry
- PapyrusScript
- ConfigValue
- InstallerOption

Rule layer:
- ObservedPattern
- RuleCandidate
- RuleEvidence
- ApprovedRule
- Exception

## Query modes

### Simonrim Strict
Question: What would the suite most likely do?

Uses approved rules first, then high-confidence observed patterns. It favors established conventions and flags deviations.

### Simonrim Complementary
Question: What new feature can fit the ecosystem without destabilizing it?

It identifies occupied mechanics, stacking risks, missing niches, progression gaps, resource interactions, and compatibility dependencies.

## Version model

All evidence is version-scoped. Rules can be current for one version, superseded, stable across multiple versions, or disputed by later implementation.

## Storage

Git is canonical for immutable ingestion snapshots, schemas, approved rules, architecture, and generated reports.

A generated SQLite index should become the fast local query layer. It should be reproducible from Git-tracked evidence rather than becoming the sole source of truth.

The spreadsheet is the human review surface for filtering, comparing, annotating, and discovering patterns.

Future MCP/API tools should include:
- balance.search
- balance.get_record
- balance.get_mechanic
- balance.compare
- balance.find_rules
- balance.analyze_feature
- balance.analyze_mod
- balance.propose_changes
- balance.verify_design
- balance.patch_plan

## Ingestion pipeline

1. Hash and inventory archives.
2. Extract source artifacts.
3. Parse ESP/ESM/ESL records losslessly.
4. Inventory BSA members and recover author-supplied text sources.
5. Parse configs and FOMOD metadata.
6. Create deterministic relations.
7. Create typed mechanic projections.
8. Resolve FormIDs against masters/load order.
9. Compute statistics and clusters.
10. Create evidence-backed rule candidates.
11. Human-review and promote candidates.
12. Expose approved rules to design tools.

## Architecture priorities revealed by this snapshot

The first four mods show that the system needs multiple evidence channels:
- ESP records carry numeric values and dependency graphs.
- Papyrus source carries runtime behavior that record values alone cannot show.
- SKSE INI/TOML/JSON files expose mechanics outside plugins.
- FOMOD choices reveal deliberate compatibility and reversion paths.
- Optional ESPs encode explicit boundaries where alternate behavior is supported.

Therefore recommendations must not be made from record statistics alone.
