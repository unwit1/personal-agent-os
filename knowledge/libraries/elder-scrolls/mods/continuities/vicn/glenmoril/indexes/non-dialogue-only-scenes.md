# GLENMORIL non-dialogue-only scene index
Source: raw `Glenmoril.esm`  
SHA-256: `5669018c81acf13147ff489f486963ecc3c57515a73ed9afd210c7ede85e1cc8`
This is the first choreography pass after exact normalization of all SCEN package/timer actions. It isolates the **31 scenes with actions but no dialogue actions**, so they are not lost when lore retrieval is driven by INFO/DIAL text.
## Coverage
- timer-only scenes: **21**
- package-only scenes: **6**
- package + timer scenes: **4**
- total non-dialogue-only scenes: **31 / 31**
Package EditorIDs are implementation labels, not standalone narrative claims. The table preserves structural action order and phase bounds without promoting plot interpretation.
## Exact structural index
| Scene | Owning quest | Structural actions |
|---|---|---|
| `00785C` zzzLrhMq01Sc04 | `007733` zzzLrhMq01 | `#1` Brandt: timer 1s (phase 0→0) |
| `007EB5` zzzLrhMq04Sc02 | `007E5E` zzzLrhMq04 | `#1` Brandt: package `zzzLrhMq04BrandtTraceBlood` (phase 0→0) |
| `00830D` zzzLrhMq06Sc01 | `0082EE` zzzLrhMq06 | `#1` Brandt: package `zzzLRHMq06BrandtEscortPlayerToGhoulHole` (phase 0→0) |
| `00835B` zzzLrhMq06sc05 | `0082EE` zzzLrhMq06 | `#1` Brandt: package `zzzLrhMq06BrandtEscortPlayerToBeastLair` (phase 0→0) |
| `008704` zzzLrhMq10scLalaBlock | `008685` zzzLrhMq10 | `#2` Lalanoah: timer 10s (phase 0→0) |
| `009C77` zzzGHMq01Sc02 | `009B59` zzzGHMq01 | `#1` Jazel: timer 10s (phase 0→0) |
| `009C87` zzzGHMq01Sc03 | `009B59` zzzGHMq01 | `#1` Gerhard: timer 5s (phase 0→0) |
| `0151E1` zzzGHMq04ScSkipToBriefing | `0147BD` zzzGHMq04 | `#1` Romion: timer 1s (phase 0→0) |
| `01776F` zzzGHMq06ScGetInAirship | `017733` zzzGHMq06 | `#1` Romion: timer 1s (phase 0→0) |
| `0177C6` zzzGHMq06ScToCamp | `017733` zzzGHMq06 | `#1` Ozwald: package `zzzGHMq06OzwaldEscortToCamp` (phase 0→0) |
| `02C267` zzzGHmq06Sub01ScWait | `02C265` zzzGHmq06Sub01 | `#1` Lalanoah: timer 5s (phase 0→0) |
| `092BC0` zzzLRHrqKanraRescueSc01 | `092BBC` zzzLRHrqKanraRescue | `#1` Target: timer 1s (phase 0→0) |
| `092BC1` zzzLRHrqKanraRescueSc02 | `092BBC` zzzLRHrqKanraRescue | `#1` Target: timer 1s (phase 0→0) |
| `0F4309` zzzLaMMq02ScMutant | `0E9E2A` zzzLaMMq02 | `#1` Mutant: package `zzzLaMMq02MutantLand01` (phase 1→1); `#2` Mutant: package `zzzLaMMq02MutantLand01` (phase 2→2); `#4` Mutant: timer 5s (phase 2→2); `#5` Mutant: timer 12s (phase 3→3); `#6` Mutant: package `zzzLaMMq02MutantLand02` (phase 3→3); `#7` Mutant: package `Skyrim.esm:0CA348` (phase 0→0); `#8` Mutant: timer 1s (phase 0→0) |
| `103B87` zzzLaMMq03ScStart | `103B86` zzzLaMMq03 | `#1` Romion: timer 1s (phase 0→0) |
| `108E38` zzzLaMMq03ScGoDeck | `103B86` zzzLaMMq03 | `#1` ThalmorTA: timer 1s (phase 0→0) |
| `11E087` zzzLaMMq04ScBrandt | `11E085` zzzLaMMq04 | `#1` Brandt: timer 1s (phase 0→0) |
| `11E08E` zzzLaMMq04ScMutant | `11E085` zzzLaMMq04 | `#1` Boss: timer 1s (phase 0→0) |
| `11E090` zzzLaMMq04ScFlyAway | `11E085` zzzLaMMq04 | `#1` Boss: package `zzzLaMMq04OzwaldFlyAway` (phase 0→0); `#2` Boss: timer 20s (phase 0→0) |
| `11E0E4` zzzLaMMq04ScBed | `11E085` zzzLaMMq04 | `#1` LalanoahW: package `zzzLaMMq04LalanoahSleep` (phase 0→0) |
| `1329E4` zzzLaMMq05ScCedricWait | `1329BD` zzzLaMMq05 | `#1` Cedric: timer 1s (phase 0→0) |
| `15254E` zzzLaMMq05ScCheckLeave | `1329BD` zzzLaMMq05 | `#1` Jazel: timer 1s (phase 0→0) |
| `171173` zzzLaMMq05ScLastChase | `1329BD` zzzLaMMq05 | `#1` Jazel: timer 1s (phase 0→0) |
| `17B5C5` zzzLaMMq05ScCedricWarning | `1329BD` zzzLaMMq05 | `#1` Cedric: timer 0.1s (phase 0→0) |
| `2EBCC1` zzzRevBq01Sc01 | `1F73CC` zzzRevBossQuest01 | `#1` Shaman: timer 1.5s (phase 0→0) |
| `2EBCF8` zzzRevBq02ScHorse | `1F73E6` zzzRevBossQuest02 | `#1` Horse: package `zzzRevBq02HoserDeathRun` (phase 0→0) |
| `360C12` zzzRevCqAishaSc01 | `360BD2` zzzRevCqAisha | `#1` Aisya: timer 1s (phase 0→0) |
| `36C623` zzzRevBQ05Sc01 | `36C620` zzzRevBossQuest05 | `#1` BeastESS: package `zzzRevBq05BeastRunAway01` (phase 1→1); `#2` BeastESS: timer 12s (phase 1→1); `#3` BeastESS: package `zzzRevBq05BossShoutToPlayer` (phase 0→0); `#4` BeastESS: timer 5s (phase 0→0) |
| `3D45AE` zzzRevBqDagothSc01 | `3CE9E4` zzzRevBossQuestDagoth | `#1` Boss01: timer 0.1s (phase 1→1); `#2` Boss01: package `zzzRevBqDagothWalking` (phase 2→2); `#3` Boss01: package `Skyrim.esm:0654FE` (phase 0→1) |
| `497A02` zzzLrhMq01ScDeathCheck | `007733` zzzLrhMq01 | `#1` Lalanoah: timer 10s (phase 0→0) |
| `497A03` zzzLrhMq03ScDeathCheck | `00790A` zzzLrhMq03 | `#1` Lalanoah: timer 10s (phase 0→0) |

## Multi-action choreography nodes
Four no-dialogue scenes contain both package actions and explicit timers and therefore carry substantially more staging information than a simple delay/control scene:
- `0F4309` **zzzLaMMq02ScMutant** (`zzzLaMMq02`): Mutant package `zzzLaMMq02MutantLand01` at phase 1→1; Mutant package `zzzLaMMq02MutantLand01` at phase 2→2; Mutant timer 5s at phase 2→2; Mutant timer 12s at phase 3→3; Mutant package `zzzLaMMq02MutantLand02` at phase 3→3; Mutant package `Skyrim.esm:0CA348` at phase 0→0; Mutant timer 1s at phase 0→0.
- `11E090` **zzzLaMMq04ScFlyAway** (`zzzLaMMq04`): Boss package `zzzLaMMq04OzwaldFlyAway` at phase 0→0; Boss timer 20s at phase 0→0.
- `36C623` **zzzRevBQ05Sc01** (`zzzRevBossQuest05`): BeastESS package `zzzRevBq05BeastRunAway01` at phase 1→1; BeastESS timer 12s at phase 1→1; BeastESS package `zzzRevBq05BossShoutToPlayer` at phase 0→0; BeastESS timer 5s at phase 0→0.
- `3D45AE` **zzzRevBqDagothSc01** (`zzzRevBossQuestDagoth`): Boss01 timer 0.1s at phase 1→1; Boss01 package `zzzRevBqDagothWalking` at phase 2→2; Boss01 package `Skyrim.esm:0654FE` at phase 0→1.

## Retrieval consequence
These scenes should be retrieved alongside their owning quest even though they contribute no dialogue rows. The next choreography pass should inspect mixed dialogue/package/timer scenes and package definitions/scripts before any movement, combat, ritual, death, or travel semantics implied by EditorIDs are promoted as lore claims.