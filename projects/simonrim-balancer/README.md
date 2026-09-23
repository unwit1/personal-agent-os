# Simonrim Balancer

A provenance-aware Skyrim gameplay design and balance knowledge project.

The goal is not to reduce Simonrim to a single balance score. The project imports the actual implementation of Simonrim mods, separates raw evidence from interpretation, learns repeatable design patterns, and uses those patterns to analyze or design features for other mods.

## Current snapshot

Initial ingestion: **2026-09-23**

| Mod | Version |
| --- | --- |
| Adamant | 6.0.4 |
| Hand to Hand | 2.0.2 |
| Blade and Blunt | 4.0.3 |
| Mysticism | 2.5.0 |

The initial snapshot has parsed 21 plugins containing 6,009 records and 81,523 subrecords, plus 11,676 deterministic FormID relationships, 476 BSA members, 115 Papyrus source files, configs, installer choices, and typed mechanic projections.

## Core design principle

Every rule must be traceable back to evidence.

A recommendation should be able to answer:

1. Which Simonrim mod/version supports it?
2. Which plugin, record, FormID, script, config value, or installer option is the evidence?
3. Is the statement directly observed, deterministically decoded, statistically inferred, or manually approved?
4. Is it a suite-wide rule, subsystem rule, or intentional exception?
5. Does it remain valid for the target mod/version?

## Repository role

This project is currently staged as a self-contained folder inside the private Personal Agent OS repository because the connected GitHub interface cannot create a new repository. The directory is intentionally portable so it can later be split into a dedicated simonrim-balancer repository without changing its internal architecture.

See docs/ARCHITECTURE.md, docs/IMPORT_STATUS.md, and docs/NEXT_STEPS.md.
