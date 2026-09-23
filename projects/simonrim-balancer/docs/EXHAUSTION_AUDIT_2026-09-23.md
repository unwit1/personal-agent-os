# Simonrim Balancer — Source Exhaustion Audit — 2026-09-23

This audit establishes the semantic coverage boundary for the supplied Adamant 6.0.4, Hand to Hand 2.0.2, Blade and Blunt 4.0.3, and Mysticism 2.5.0 archives.

## Plugin-record coverage

- Total plugin records: **6,009**
- Record types: **53**
- Unmapped record types: **0**
- Gameplay / behavioral / typed-support records: **5,556**
- Keyword identity records: **208**
- Presentation-support inventory records: **224**
- TES4 plugin headers: **21**

The four categories sum to all 6,009 records.

### Fully or typed semantically modeled families

Magic and progression:
- MGEF, SPEL, PERK, ENCH, SCRL, BOOK, AVIF, DUAL

Combat / movement / actors:
- WEAP, AMMO, ARMO, NPC_, RACE, CLAS, CSTY, MOVT, PROJ, EXPL, HAZD

Distribution / economy:
- LVLI, COBJ, CONT, FLST, OTFT, ALCH, MISC, FACT

Tuning / controllers / interaction:
- GMST, GLOB, IDLE, QUST, SMQN, MESG, ACTI

World/support:
- REFR, CELL, WRLD

Each of these families has deterministic typed outputs appropriate to its gameplay role. External Skyrim/DLC baseline bodies remain explicitly unavailable where they were not supplied.

### Identity-only family

- KYWD: all 208 keyword records are preserved as canonical identifiers and relationship targets. Keywords have no independent numeric balance payload, so their design meaning is expressed through the records that use them rather than by inventing standalone keyword rules.

### Presentation/support inventory families

The following 224 records are fully retained in the lossless raw layer and indexed by canonical identity, but are intentionally not mined as independent balance laws:

- ARTO
- EFSH
- IPCT
- IPDS
- STAT
- LIGH
- IMAD
- ADDN
- TXST
- SNDR
- SOUN
- ARMA
- HDPT
- LSCR

These families primarily carry effect art, shaders, impact presentation, models, lighting, image-space, texture, sound, armor-model, cosmetic, and load-screen data. Their references remain available to explain implementation, but their presentation values are not treated as balance principles.

## Source-artifact coverage

Top-level archive/source artifacts: **73**

- ESP plugins: 21 — losslessly parsed.
- BSA archives: 4 — member inventory parsed; author text/source extracted where textual.
- Runtime/config files: 9 — decoded.
- FOMOD XML files: 6 — installer/options modeled separately.
- Papyrus source at top level: 1 — parsed.
- Binary/presentation assets at top level: inventoried and hashed.

BSA members: **476**
- NIF: 134
- PEX: 123
- PSC: 114
- DDS: 78
- WAV: 26
- TXT: 1

Papyrus source corpus:
- 114 PSC files from BSA + 1 loose PSC = **115 parsed source files**.

Behavior configuration:
- **169 decoded entries** across 9 runtime/distribution/config files after adding the previously missed commented Scrambled Bugs JSON.
- FOMOD installer semantics remain a separate 20-option channel.

## Deliberate binary boundary

The project inventories and hashes native/compiled assets but does not claim semantic source-level understanding of code that was not supplied as source:

- DLL: 2
- PDB: 2
- compiled PEX bytecode: inventoried; supplied PSC source is preferred where available
- HKX/NIF/DDS/WAV: presentation/runtime asset inventory

Native DLL/PDB reverse engineering is outside this ingestion pass. That limitation is explicit rather than silently filling gaps with inference.

## Evidence-layer completion

The supplied archives are now represented through:

1. lossless plugin records/subrecords;
2. master-aware canonical Form identity;
3. typed gameplay decoders;
4. override/delta evidence when the prior imported master exists;
5. VMAD script/property/fragment/alias evidence;
6. Papyrus source behavior observations;
7. SPID/KID/SKSE/TOML/JSON runtime configuration;
8. FOMOD optional-module semantics;
9. world placement / vendor / support relationships;
10. presentation and binary inventories.

## What is still unknowable from these four archives alone

- Exact Skyrim/DLC-before-Simonrim record bodies for 1,619 external-baseline overrides.
- Source-level behavior inside native DLLs not shipped as source.
- Source bodies for attached scripts not included by these packages.
- Intent beyond what can be demonstrated from implementation, supplied comments/docs/configuration, or repeated evidence.

These are evidence limitations, not unfinished parsing work.

## Rule status

**Approved Simonrim design rules: 0.**

The evidence corpus is now mature enough to generate reviewable rule candidates, but candidates must remain distinct from canonical rules until evidence, scope, counterexamples, optional-module contamination, and exceptions have been reviewed.
