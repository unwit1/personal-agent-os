# Skyrim Mod Factory — Schema Triangulation and Self-Checking

Created: 2026-09-24
Status: canonical validation policy

## Objective

No AI-generated Skyrim binary/config/script artifact should be trusted because one library accepted it.

For high-risk formats, use **independent validators with different implementations**.

## Plugin record triangulation

Preferred validation chain:

1. **Author/generate**
   - houseCARL/Mutagen;
   - Spriggit deserialize;
   - Synthesis/Mutagen patcher;
   - CK where editor-owned semantics require it.

2. **Mutagen reload**
   - parse entire output;
   - resolve every FormLink;
   - verify expected typed values.

3. **xEdit/xDump**
   - load with masters;
   - Check for Errors;
   - unresolved references;
   - record/subrecord schema;
   - header/FormVersion;
   - ESL range/flags;
   - context-dependent record flags.

4. **Spriggit round-trip**
   - serialize output;
   - deserialize to second binary;
   - normalize;
   - compare semantic record tree.

5. **Intent diff**
   - compare before/after only for declared touch-set;
   - unexplained field changes fail.

### Plugin pass condition

PASS only when:
- all parsers load;
- all masters resolve;
- no unexpected records/fields changed;
- intended fields match manifest;
- round-trip produces semantically equivalent data;
- independent schema tools agree on all touched structures.

### Coverage disagreement

If Mutagen accepts a record that xEdit rejects, or vice versa:
- block promotion;
- preserve both errors;
- identify exact schema/version gap;
- compare xEdit definition + official master example;
- add regression fixture;
- never let the LLM choose the answer by plausibility.

## Papyrus triangulation

1. Papyrus language-server diagnostics.
2. Provider corpus/signature lookup.
3. official PapyrusCompiler or Caprica/Pyro compile.
4. optional second compiler cross-check.
5. PEX inspect/decompile metadata.
6. plugin VMAD/script property binding validation.
7. Lilac/unit-style runtime tests.
8. runtime debugger/DevBench when behavior remains ambiguous.

Fail on:
- missing parent;
- ambiguous ScriptName provider;
- missing native provider;
- stale PEX;
- VMAD property mismatch;
- undeclared persistent schema migration.

## SKSE/native triangulation

1. compiler warnings/errors;
2. clang-tidy/static analysis where possible;
3. CommonLib types/relocations;
4. PE/import scan;
5. SKSE plugin declaration/runtime matrix;
6. load log;
7. hook/API readiness log;
8. runtime MCP/DevBench assertion;
9. Crash Logger/PDB on failure.

Never equate successful DLL load with successful feature initialization.

## NIF triangulation

1. PyNifly/Nifly parse.
2. structural invariant checks.
3. NifSkope load.
4. Blender import/headless render.
5. optional round-trip back to NIF.
6. compare block/shader/skin/collision invariants.
7. in-game visual/physics test.

Fail if:
- parser disagreement;
- missing bones/textures;
- invalid partitions;
- unweighted vertices where not intended;
- bounding data is invalid;
- shader/texture-slot contract inconsistent;
- collision layer/material invalid.

## Texture/material checks

Use at least:
- DDS metadata parser/DirectXTex-equivalent validation;
- image decode;
- expected dimensions/mips;
- material/NIF referenced path;
- rendered preview.

AI image generation never bypasses game-format validation.

## Animation/behavior triangulation

1. source HKX/annotation metadata.
2. OAR config parser.
3. Pandora behavior generation and logs.
4. generated behavior/output asset winner.
5. animation skeleton-node audit.
6. runtime condition match/debug.
7. runtime event/contact assertion.

## Runtime patcher schema checks

For SPID/KID/BOS/FLM/SkyPatcher/OAR:
- pin framework version;
- use framework's own parser/log when possible;
- maintain an Agent OS grammar/schema snapshot;
- parse with independent local validator;
- resolve every referenced Form/EditorID/plugin;
- detect duplicate/overlapping rules;
- query running/static result after application where observable.

## FOMOD

1. XML schema validation.
2. source file closure.
3. option dependency graph.
4. simulate every supported option combination.
5. build into clean staging.
6. install simulation into temporary tree.
7. compare installed result against expected manifest.

## BSA

1. pack.
2. list archive.
3. extract into clean temp directory.
4. hash compare against staged inputs.
5. verify archive/path policy.

## Schema-check confidence

### Level A — generated + one parser
Development only.

### Level B — two independent parsers
Acceptable for low-risk intermediate artifacts.

### Level C — two parsers + round-trip + intent diff
Default release requirement for plugin/config artifacts.

### Level D — Level C + runtime assertion
Required for high-impact gameplay/persistence/native behavior.

## Self-check principle

Every analyzer must report its denominator:
- number of plugins read vs total expected;
- number of records parsed vs selected;
- number of crash logs parsed vs discovered;
- number of rules accepted/rejected;
- number of test cases executed/skipped;
- number of files inspected vs manifest total.

A validator that silently skips unknown input is a failed validator.

## Mutation testing

For every important gate, deliberately inject representative bad data and prove the gate fails.

Examples:
- dangling FormLink;
- invalid ESL FormID;
- wrong CTDA parameter;
- stale PEX;
- bad VMAD property;
- missing texture;
- wrong biped partition;
- invalid OAR condition;
- stale generated LOD;
- missing FOMOD payload;
- broken SKSE API version.

If the validator passes the mutated fixture, the validator is not a release gate.

## AI double-check behavior

Before saying "fixed":
1. restate expected postcondition;
2. rerun the narrow validator;
3. rerun independent validator;
4. inspect diff;
5. rerun dependent tests;
6. query runtime if relevant;
7. only then mark resolved.

No self-certification from generated code.
