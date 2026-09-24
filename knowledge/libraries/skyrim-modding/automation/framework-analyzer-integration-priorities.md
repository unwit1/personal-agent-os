# Skyrim Mod Factory — Framework/Analyzer Integration Priorities

Created: 2026-09-24

## Tier 1 — integrate first

### xEdit/xDump
Why:
- strongest current Skyrim plugin-schema oracle.

Integrate:
- schema export;
- selected record dump;
- error check;
- plugin diff extraction.

### Mutagen
Why:
- typed generation and independent parse/link oracle.

Integrate:
- project generator library;
- LinkCache checks;
- winning override analysis;
- semantic record serialization.

### Spriggit
Why:
- converts binary plugin changes into Git-reviewable YAML/JSON and back.

Integrate:
- serialize after validated plugin changes;
- deserialize in clean build;
- round-trip semantic gate.

### MO2
Why:
- reproducible VFS/profile execution boundary.

Integrate:
- dedicated build/test profile;
- tool launch;
- asset winner inspection;
- generated output mods.

### Crash Logger
Why:
- runtime crash evidence can be attached to exact build.

Integrate:
- latest-crash collection;
- FormID/plugin extraction;
- stack-signature clustering.

## Tier 2 — project-dependent high value

### Antigen / Mutagen.Bethesda.Analyzers
Use as an upstream bug-rule corpus and analyzer implementation source.

### SPID / KID / BOS / FLM / SkyPatcher
Build typed config models and validators instead of hand-writing strings.

### OAR / Pandora
Generate animation configuration/behavior patches from semantic manifests.

### PyNifly
Use Python API for NIF/TRI/HKX invariant checks and batch transforms.

### DynDOLOD/xLODGen/TexGen
Treat as dependency-graph generators with explicit input hashes.

### FOMOD validator/schema
Make installer correctness a gate.

## Tier 3 — specialized

- EasyNPC-style NPC appearance/behavior reconciliation;
- BodySlide/Outfit Studio;
- Community Shaders;
- ParallaxGen;
- RaceMenu/SKEE;
- HIGGS/PLANCK/VRIK;
- Custom Skills;
- PrismaUI/native menu frameworks;
- voice/lip generation tools.

## Typed config strategy

For every text-based framework, create an internal JSON model first.

Example:
```json
{
  "framework": "spid",
  "action": "distribute_perk",
  "form": "MyMod.esp|001234",
  "filters": {
    "keywords": ["ActorTypeNPC"],
    "factions": ["BanditFaction"],
    "sex": "any"
  },
  "chance": 100
}
```

Then render version-specific INI syntax.

Benefits:
- schema validation;
- dedupe;
- semantic diff;
- cross-render to another framework;
- easier automated tests.

The final INI should be generated output, not canonical intent.

## Analyzer rule strategy

Every discovered bug pattern should become:

```text
rule id
scope
preconditions
bad pattern
severity
why
detection algorithm
false-positive exclusions
safe fix?
test fixture
source evidence
version scope
```

This format lets the Mod Factory absorb findings from Antigen, xEdit documentation, framework issue trackers, and validated user bugs without turning them into folklore.
