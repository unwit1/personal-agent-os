# Skyrim CTDA Condition Encoding — xEdit 4.1.5f

Imported: 2026-09-24
Source: `TES5Edit/TES5Edit` tag `xedit-4.1.5f`
Source file: `Core/wbDefinitionsTES5.pas`
Source blob SHA: `8455d8b86440712de6e280f1e113572ffefbd11d`
Status: finite source-derived schema

## CTDA structure

A Skyrim condition entry contains, at minimum:

- **Type** — one byte combining comparison operator and condition flags;
- **Comparison Value** — literal Float or GlobalVariable depending on Type flag;
- **Function** — numeric condition-function index;
- **Parameter #1**;
- **Parameter #2**;
- **Run On** — evaluation context;
- **Reference** — used when Run On requires an explicit reference;
- **Parameter #3** — used by functions that require a third parameter.

The 402 known function indices are cataloged in `condition-function-catalog-xedit.md`.

## Comparison operator bits

Upper three bits of CTDA Type:

| Bits/value | Operator |
|---|---|
| `0x00` | Equal to |
| `0x20` | Not equal to |
| `0x40` | Greater than |
| `0x60` | Greater than or equal to |
| `0x80` | Less than |
| `0xA0` | Less than or equal to |

xEdit treats other upper-bit patterns as an unknown comparison operator.

## Lower-bit flags

| Value | Flag | Meaning |
|---|---|---|
| `0x01` | Or | OR this condition with the next/condition group rather than default AND semantics |
| `0x02` | Use aliases | Interpret applicable function parameters as quest-alias data |
| `0x04` | Use global | Comparison value is a GLOB reference rather than literal float |
| `0x08` | Use packdata | Interpret applicable parameters as package-data inputs |
| `0x10` | Swap Subject and Target | Swap subject and target context for evaluation |

### Flag constraints

xEdit source notes that **Use aliases** and **Use packdata** are exclusive interpretations of function parameters.

## Comparison value

### Literal comparison
Without `Use global`, the comparison operand is a Float stored directly in CTDA.

### Global comparison
With `Use global`, the comparison operand is a FormID to a `GLOB`. The condition therefore changes as that GlobalVariable changes at runtime.

## Run On values

| ID | Context |
|---:|---|
| 0 | Subject |
| 1 | Target |
| 2 | Reference |
| 3 | Combat Target |
| 4 | Linked Reference |
| 5 | Quest Alias |
| 6 | Package Data |
| 7 | Event Data |

### Subject
The ordinary subject of the condition context, such as the actor/reference being evaluated.

### Target
The relevant target supplied by the condition-owning system.

### Reference
Use the explicit Reference field stored in CTDA.

### Combat Target
Use subject actor's current combat target.

### Linked Reference
Resolve linked reference from the condition context/reference.

### Quest Alias
Use quest alias identity/context.

### Package Data
Use data input from an AI package.

### Event Data
Use Story Manager/event data supplied to the condition context.

## Function parameter type enum

xEdit's `TCTDAFunctionParamType` enum contains **57 parameter types** in this release.

| ID | xEdit enum | Source annotation | Line |
|---:|---|---|---:|
| 0 | `ptNone` | — | 2243 |
| 1 | `ptInteger` | — | 2244 |
| 2 | `ptFloat` | — | 2245 |
| 3 | `ptVariableName` | Integer | 2246 |
| 4 | `ptSex` | Enum: Male, Female | 2247 |
| 5 | `ptActorValue` | Enum: wbActorValue | 2248 |
| 6 | `ptCrimeType` | ?? Enum | 2249 |
| 7 | `ptAxis` | ?? Char | 2250 |
| 8 | `ptQuestStage` | ?? Integer | 2251 |
| 9 | `ptMiscStat` | ?? Enum | 2252 |
| 10 | `ptAlignment` | ?? Enum | 2253 |
| 11 | `ptEquipType` | ?? Enum | 2254 |
| 12 | `ptFormType` | ?? Enum | 2255 |
| 13 | `ptCriticalStage` | ?? Enum | 2256 |
| 14 | `ptObjectReference` | REFR, ACHR | 2257 |
| 15 | `ptInventoryObject` | ARMO, BOOK, MISC, WEAP, AMMO, KEYM, ALCH, ARMA, LIGH, LVLI, COBJ | 2258 |
| 16 | `ptActor` | ACHR | 2259 |
| 17 | `ptVoiceType` | VTYP | 2260 |
| 18 | `ptIdleForm` | IDLE | 2261 |
| 19 | `ptFormList` | FLST | 2262 |
| 20 | `ptQuest` | QUST | 2263 |
| 21 | `ptFaction` | FACT | 2264 |
| 22 | `ptCell` | CELL | 2265 |
| 23 | `ptClass` | CLAS | 2266 |
| 24 | `ptRace` | RACE | 2267 |
| 25 | `ptActorBase` | NPC_ | 2268 |
| 26 | `ptGlobal` | GLOB | 2269 |
| 27 | `ptWeather` | WTHR | 2270 |
| 28 | `ptPackage` | PACK | 2271 |
| 29 | `ptEncounterZone` | ECZN | 2272 |
| 30 | `ptPerk` | PERK | 2273 |
| 31 | `ptOwner` | FACT, NPC_ | 2274 |
| 32 | `ptFurniture` | FURN | 2275 |
| 33 | `ptMagicItem` | SPEL | 2276 |
| 34 | `ptMagicEffect` | MGEF | 2277 |
| 35 | `ptWorldspace` | WRLD | 2278 |
| 36 | `ptVATSValueFunction` | — | 2279 |
| 37 | `ptVATSValueParam` | — | 2280 |
| 38 | `ptReferencableObject` | — | 2281 |
| 39 | `ptRegion` | REGN | 2282 |
| 40 | `ptKeyword` | KYWD | 2283 |
| 41 | `ptAdvanceAction` | ?? Enum | 2284 |
| 42 | `ptCastingSource` | ?? Enum | 2285 |
| 43 | `ptShout` | SHOU | 2286 |
| 44 | `ptLocation` | LCTN | 2287 |
| 45 | `ptRefType` | LCRT | 2288 |
| 46 | `ptAlias` | index into QUST quest aliases | 2289 |
| 47 | `ptPackdata` | index into PACK package data inputs | 2290 |
| 48 | `ptAssociationType` | ASTP | 2291 |
| 49 | `ptFurnitureAnim` | enum | 2292 |
| 50 | `ptFurnitureEntry` | flags | 2293 |
| 51 | `ptScene` | SCEN | 2294 |
| 52 | `ptWardState` | enum | 2295 |
| 53 | `ptEvent` | Struct | 2296 |
| 54 | `ptEventData` | LCTN, KYWD or FLST | 2297 |
| 55 | `ptKnowable` | MGEF, WOOP, ENCH | 2298 |
| 56 | `ptFactionOpt` | NULL, FACT | 2299 |

## Why CTDA bugs are easy to misdiagnose

Two conditions can show the same function name but behave differently because of:
- comparison operator;
- OR/AND grouping;
- Global comparison;
- alias/package parameter reinterpretation;
- Subject/Target swap;
- Run On context;
- explicit Reference;
- parameter Form identity.

A patch that forwards only the function and visible comparison value can still change behavior if it loses Type flags or Run On data.

## Patching rules

1. Treat one CTDA as a structured predicate, not an independent function call.
2. Preserve order: OR flags make neighboring condition ordering semantically significant.
3. Compare Type byte, function, all parameters, Run On and Reference.
4. When conditions originate in a Quest, inspect alias IDs before forwarding them into another quest/version.
5. When `Use global` is set, inspect the GLOB winner/runtime state.
6. Story Manager and package conditions can depend on event/package contexts unavailable in ordinary console testing.
7. Do not translate xEdit's parameter enum directly into Papyrus types; they are plugin-condition schema categories.
