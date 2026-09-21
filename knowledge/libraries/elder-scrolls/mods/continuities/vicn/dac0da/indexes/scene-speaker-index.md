# DAc0da scene / speaker index

**Continuity:** `tes.mod.vicn.dac0da`  
**Source:** `DAc0da.esm`  
**Coverage:** all 79 SCEN records

## Resolution method

Scene ownership is resolved from DIAL actions whose topic records carry direct `QNAM` quest links. The six scenes without dialogue actions are resolved from direct owning-quest FormID references embedded in their SCEN payloads. Speaker names are resolved from each dialogue action's numeric scene alias back through the owning QUST alias table and, when available, its unique NPC form.

- **79 / 79** scenes have an owning quest resolved.
- **73** scenes contain DIAL-backed spoken actions.
- **6** scenes are non-dialogue choreography/control scenes.
- This index resolves **who says scene-bound lines**; it does not make alternate branches simultaneous or promote speaker testimony into objective narration.

## Scene count by owning quest

| Quest | Title | Scenes |
|---|---|---:|
| `00AA0C` `zDcdMq00` | The Call of Landfall | 2 |
| `004475` `zDcdMq01` | The Sea of Causality | 8 |
| `004931` `zDcdMq02` | Negative Legacy | 4 |
| `004981` `zDcdMq03` | Patchwork | 1 |
| `00B21B` `zDcdMq04` | Numidium Tertius | 4 |
| `00CA1E` `zDcdMq05` | Censored Fate | 2 |
| `004566` `zDcdMqAgent` | Agent Event | 1 |
| `00CA5B` `zDcdMqArgoEnd` | Pan-Argonia | 1 |
| `00B3A8` `zDcdMqBoss02` | VS GC9 | 2 |
| `00B5EE` `zDcdMqBoss04` | VS Zurin Arctus | 3 |
| `004564` `zDcdMqDragon` | Golden Dragon Flight | 1 |
| `00525E` `zDcdSqAbnur` | Abnur Tharn | 2 |
| `0047E5` `zDcdSqAugur` | Augur of the Obscure | 1 |
| `00B420` `zDcdSqGhostChoir` | Scene of Ghost Choir | 4 |
| `0050DC` `zDcdSqHalfElf` | The End of All Wishes | 3 |
| `00CDD9` `zDcdSqSheogorath` | Cheese Party | 1 |
| `00CE40` `zDcdSqSloadRadio` | Sload Radio | 4 |
| `0052C2` `zDcdSqWorm` | Echoes of Mnemolichite | 14 |
| `005303` `zDcdSqWormSub01` | Option: Dreugh | 2 |
| `005FBE` `zDcdSqWormSub03` | Group Battle: The Revenant | 2 |
| `006134` `zDcdSqWormSub04` | The Sea of Radiance | 1 |
| `004B1C` `zDcdSqYngol` | Drowned Nighthawk | 16 |

## Complete SCEN index

| SCEN | Editor ID | Owning quest | Resolved scene speakers / control | DIAL topics |
|---|---|---|---|---:|
| `004476` | `zDcdMq01ScSamon01` | `004475` `zDcdMq01` | Akashiya-Samon | 2 |
| `0044AC` | `zDcdMq01ScSamon02` | `004475` `zDcdMq01` | Akashiya-Samon | 1 |
| `004504` | `zDcdMq01ScSload01` | `004475` `zDcdMq01` | Worm Cultist<br>N'Danda | 2 |
| `004509` | `zDcdMq01ScSload02` | `004475` `zDcdMq01` | N'Danda<br>Worm Cultist | 2 |
| `004511` | `zDcdMq01ScSload03` | `004475` `zDcdMq01` | Worm Cultist<br>N'Danda | 3 |
| `004518` | `zDcdMq01ScSload04` | `004475` `zDcdMq01` | N'Danda | 1 |
| `00451B` | `zDcdMq01ScSload05` | `004475` `zDcdMq01` | N'Danda | 2 |
| `00453C` | `zDcdMq01ScDragon01` | `004475` `zDcdMq01` | [non-dialogue control scene] | 0 |
| `004565` | `zDcdMqDragonSc01` | `004564` `zDcdMqDragon` | [package-only: zDcdMqDragon01OrbitStart, zDcdMqDragon01PerchShip, zDcdMqDragon01FilightAway] | 0 |
| `004593` | `zDcdMqAgentSc01` | `004566` `zDcdMqAgent` | [package-only: zDcdMqAgentEatDreugh, zDcdMqAgentNoticePlayer, zDcdMqAgentRetreat] | 0 |
| `0047EC` | `zDcdSqAugurSc01` | `0047E5` `zDcdSqAugur` | AugurTA | 1 |
| `00493A` | `zDcdMq02ScAugur01` | `004931` `zDcdMq02` | Augur of the Obscure | 1 |
| `004946` | `zDcdMq02ScMemospore` | `004931` `zDcdMq02` | Augur of the Obscure<br>Crab Spirit<br>Rolls-On-Roads | 7 |
| `00496D` | `zDcdMq02ScZurin01` | `004931` `zDcdMq02` | ZurinTA<br>The Underking | 3 |
| `00497B` | `zDcdMq02ScZurinEnd` | `004931` `zDcdMq02` | The Underking | 1 |
| `0049AC` | `zDcdMq03ScPortal` | `004981` `zDcdMq03` | Rolls-On-Roads | 3 |
| `004B31` | `zDcdSqYScSleep` | `004B1C` `zDcdSqYngol` | Yngol | 1 |
| `004B39` | `zDcdSqYScOutcastA` | `004B1C` `zDcdSqYngol` | Hgelhelm the Outcast<br>Akashiya-Samon | 6 |
| `004BED` | `zDcdSqYScBoss01A` | `004B1C` `zDcdSqYngol` | Hgelhelm the Outcast<br>Yngol | 5 |
| `004BFB` | `zDcdSqYScBoss01B` | `004B1C` `zDcdSqYngol` | Hgelhelm the Outcast | 2 |
| `004C74` | `zDcdSqYScSamon01` | `004B1C` `zDcdSqYngol` | Akashiya-Samon | 1 |
| `004C8E` | `zDcdSqYScBoss02A` | `004B1C` `zDcdSqYngol` | Sindwen the Wintercaller<br>Yngol | 7 |
| `004CA0` | `zDcdSqYScBoss02B` | `004B1C` `zDcdSqYngol` | Sindwen the Wintercaller | 2 |
| `004DC1` | `zDcdSqYScBoss03A` | `004B1C` `zDcdSqYngol` | Haalj Hgelhelmson<br>Yngol2 | 8 |
| `004DD6` | `zDcdSqYScBoss03B` | `004B1C` `zDcdSqYngol` | Haalj Hgelhelmson | 3 |
| `004F96` | `zDcdSqYScBoss04A` | `004B1C` `zDcdSqYngol` | Akashiya-Samon<br>Yngol3 | 5 |
| `004FC6` | `zDcdSqYScDuelGood` | `004B1C` `zDcdSqYngol` | Akashiya-Samon<br>Yngol3 | 4 |
| `004FE9` | `zDcdSqYScDrago` | `004B1C` `zDcdSqYngol` | Yngol3<br>Yngol the Tsunaltir | 4 |
| `005035` | `zDcdSqYScStop` | `004B1C` `zDcdSqYngol` | [non-dialogue control scene] | 0 |
| `00503A` | `zDcdSqYScDragonEND` | `004B1C` `zDcdSqYngol` | Yngol the Tsunaltir<br>Tsuunalinfaxtir | 2 |
| `005043` | `zDcdSqYScDuelBad` | `004B1C` `zDcdSqYngol` | Akashiya-Samon<br>Yngol3 | 3 |
| `00505F` | `zDcdSqYScSamonEnd` | `004B1C` `zDcdSqYngol` | Akashiya-Samon | 1 |
| `0050DF` | `zDcdSqHESc01` | `0050DC` `zDcdSqHalfElf` | Girl | 1 |
| `005102` | `zDcdSqHESc02` | `0050DC` `zDcdSqHalfElf` | Beynhaal | 1 |
| `00512B` | `zDcdSqHESc03` | `0050DC` `zDcdSqHalfElf` | Beynhaal | 1 |
| `005285` | `zDcdSqAbnurSc01` | `00525E` `zDcdSqAbnur` | Mysterious Battlemage | 1 |
| `0052B1` | `zDcdSqAbnurSc02` | `00525E` `zDcdSqAbnur` | Mysterious Battlemage | 1 |
| `0052CC` | `zDcdSqWScPrisoned` | `0052C2` `zDcdSqWorm` | Vanus Galerion | 1 |
| `005305` | `zDcdSqWS1Sc01` | `005303` `zDcdSqWormSub01` | Templar of Hahd Yu'qbar | 2 |
| `00530F` | `zDcdSqWS1ScDeathCheck` | `005303` `zDcdSqWormSub01` | [non-dialogue control scene] | 0 |
| `00532A` | `zDcdSqWScEggBreak` | `0052C2` `zDcdSqWorm` | Vanus Galerion<br>Templar of Hahd Yu'qbar | 4 |
| `00535C` | `zDcdSqWScVanusTalk01` | `0052C2` `zDcdSqWorm` | Vanus Galerion<br>Templar of Hahd Yu'qbar | 6 |
| `005403` | `zDcdSqWScDreughMono` | `0052C2` `zDcdSqWorm` | Templar of Hahd Yu'qbar | 1 |
| `005436` | `zDcdSqWScVigilThank` | `0052C2` `zDcdSqWorm` | Vigilant Athanasius | 1 |
| `00543E` | `zDcdSqWScVanusFall` | `0052C2` `zDcdSqWorm` | Vanus Galerion | 2 |
| `005453` | `zDcdSqWScVanusHealA` | `0052C2` `zDcdSqWorm` | Templar of Hahd Yu'qbar<br>Vanus Galerion | 6 |
| `005467` | `zDcdSqWScVanusHealB` | `0052C2` `zDcdSqWorm` | Vanus Galerion | 4 |
| `00551F` | `zDcdSqWScSloadCity` | `0052C2` `zDcdSqWorm` | Mysterious Battlemage<br>Vanus Galerion | 7 |
| `0056BA` | `zDcdSqWScVanusAttack` | `0052C2` `zDcdSqWorm` | Vanus Galerion | 2 |
| `005FE5` | `zDcdSqWS03ScStart` | `005FBE` `zDcdSqWormSub03` | Mysterious Battlemage<br>Vanus Galerion | 2 |
| `005FFB` | `zDcdSqWS03ScInterval` | `005FBE` `zDcdSqWormSub03` | Vanus Galerion<br>Mysterious Battlemage | 5 |
| `00601E` | `zDcdSqWScGatherMember` | `0052C2` `zDcdSqWorm` | [package-only: zDcdSqWAbnurTravelToTimeBreach, zDcdSqWVanusTravelToTimeBreach] | 0 |
| `00603E` | `zDcdSqWScDreughEnd` | `0052C2` `zDcdSqWorm` | Vanus Galerion<br>Templar of Hahd Yu'qbar | 4 |
| `006048` | `zDcdSqWScAbnurEnd` | `0052C2` `zDcdSqWorm` | Vanus Galerion<br>Mysterious Battlemage | 6 |
| `006063` | `zDcdSqWScVanusEnd` | `0052C2` `zDcdSqWorm` | Vanus Galerion | 1 |
| `006140` | `zDcdSqWS04Sc01` | `006134` `zDcdSqWormSub04` | Vigilant Athanasius<br>Malmanius the Child of Radiance | 3 |
| `00AA19` | `zDcdMq00Sc01` | `00AA0C` `zDcdMq00` | Rolls-On-Roads | 1 |
| `00AA79` | `zDcdMq00Sc02` | `00AA0C` `zDcdMq00` | Rolls-On-Roads | 4 |
| `00B421` | `zDcdSqGC9Sc01` | `00B420` `zDcdSqGhostChoir` | GC01<br>Oyarsa01 | 4 |
| `00B42A` | `zDcdSqGC9Sc02` | `00B420` `zDcdSqGhostChoir` | GC02<br>Oyarsa02 | 4 |
| `00B433` | `zDcdSqGC9Sc03` | `00B420` `zDcdSqGhostChoir` | GC03<br>Oyarsa03 | 4 |
| `00B43C` | `zDcdSqGC9Sc04` | `00B420` `zDcdSqGhostChoir` | GC04<br>Oyarsa04 | 4 |
| `00B44B` | `zDcdMqBoss02Sc01` | `00B3A8` `zDcdMqBoss02` | GC9<br>O.Y.A.R.S.A | 4 |
| `00B459` | `zDcdMqBoss02Sc02` | `00B3A8` `zDcdMqBoss02` | GC9<br>O.Y.A.R.S.A | 2 |
| `00B5F0` | `zDcdMqBoss04Sc01` | `00B5EE` `zDcdMqBoss04` | Rolls-On-Roads | 7 |
| `00B61D` | `zDcdMqBoss04Sc02` | `00B5EE` `zDcdMqBoss04` | Zurin Arctus | 2 |
| `00B623` | `zDcdMqBoss04Sc03` | `00B5EE` `zDcdMqBoss04` | Zurin Arctus | 1 |
| `00B71D` | `zDcdMq04ScNM01` | `00B21B` `zDcdMq04` | Rolls-On-Roads | 4 |
| `00B726` | `zDcdMq04ScNM02` | `00B21B` `zDcdMq04` | Rolls-On-Roads | 3 |
| `00B72D` | `zDcdMq04ScNM03` | `00B21B` `zDcdMq04` | Rolls-On-Roads | 3 |
| `00B74B` | `zDcdMq04ScPsijic` | `00B21B` `zDcdMq04` | Rolls-On-Roads | 4 |
| `00CA24` | `zDcdMq05Sc01` | `00CA1E` `zDcdMq05` | Rolls-On-Roads | 2 |
| `00CA29` | `zDcdMq05Sc01Alt` | `00CA1E` `zDcdMq05` | Load Error | 2 |
| `00CA61` | `zDcdMqArgoEndSc01` | `00CA5B` `zDcdMqArgoEnd` | Rolls-On-Roads | 4 |
| `00CDDD` | `zDcdSqSheogorathSc01` | `00CDD9` `zDcdSqSheogorath` | Sheogorath | 1 |
| `00CE47` | `zDcdSqSloadRadioSc01` | `00CE40` `zDcdSqSloadRadio` | TA01 | 3 |
| `00CE4E` | `zDcdSqSloadRadioSc02` | `00CE40` `zDcdSqSloadRadio` | TA02 | 3 |
| `00CE55` | `zDcdSqSloadRadioSc03` | `00CE40` `zDcdSqSloadRadio` | TA03 | 3 |
| `00CE5C` | `zDcdSqSloadRadioSc04` | `00CE40` `zDcdSqSloadRadio` | TA04 | 3 |

## High-value uses

- Resolve aliases that otherwise appear only as generic or alternate forms in INFO records.
- Separate ordinary actors from temporal/ghost/alternate aliases used in branch scenes.
- Identify scene-only package choreography without mistaking movement/control records for new lore.
- Provide a deterministic bridge from scene dialogue to character dossiers and quest reconstructions.

## Next pass

Use this index to compare scene-bound INFO lines against the existing quest/character dossiers. Add only material that is genuinely missing or whose speaker attribution materially changes interpretation.
