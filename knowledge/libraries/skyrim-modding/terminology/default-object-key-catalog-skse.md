# Skyrim Default Object Key Catalog — SKSE Source

Imported: 2026-09-24
Source: `ianpatt/skse64` master
Source file: `scripts/modified/DefaultObjectManager.psc`
Source blob SHA: `33d9ed0f3e3111f65a2c7ef8db09e335bcb40250`
Extracted valid-key entries: 346
Status: finite source-derived catalog

## Purpose

Skyrim's Default Object Manager is a hard-coded registry of four-character keys mapped to Forms. SKSE exposes:

- `GetForm(string key)`
- `SetForm(string key, Form newForm)`

The key itself has engine-defined semantics. Changing the Form assigned to a known key can change engine behavior; inventing an arbitrary new four-character key does not create a new engine subsystem.

## Catalog

| Key | Meaning in SKSE source | Source line |
|---|---|---:|
| `WWSP` | Werewolf Spell | 10 |
| `SALT` | Sitting Angle Limit | 11 |
| `APSH` | Allow Player Shout | 12 |
| `GOLD` | Gold | 13 |
| `LKPK` | Lockpick | 14 |
| `SKLK` | SkeletonKey | 15 |
| `PFAC` | Player Faction | 16 |
| `GFAC` | Guard Faction | 17 |
| `DFMS` | Default Music | 18 |
| `BTMS` | Battle Music | 19 |
| `DTMS` | Death Music | 20 |
| `SCMS` | Success Music | 21 |
| `LUMS` | Level Up Music | 22 |
| `DCMS` | Dungeon Cleared Music | 23 |
| `PVMA` | Player Voice (Male) | 24 |
| `PVMC` | Player Voice (Male Child) | 25 |
| `PVFA` | Player Voice (Female) | 26 |
| `PVFC` | Player Voice (Female Child) | 27 |
| `EPDF` | Eat Package Default Food | 28 |
| `LHEQ` | LeftHand Equip | 29 |
| `RHEQ` | RightHand Equip | 30 |
| `EHEQ` | EitherHand Equip | 31 |
| `VOEQ` | Voice Equip | 32 |
| `POEQ` | Potion Equip | 33 |
| `EACA` | Every Actor Ability | 34 |
| `CACA` | Commanded Actor Ability | 35 |
| `DEIS` | Drug Wears Off Image Space | 36 |
| `DFTS` | Footstep Set | 37 |
| `DLMT` | Landscape Material | 38 |
| `DLZM` | Dragon Land Zone Marker | 39 |
| `DCZM` | Dragon Crash Zone Marker | 40 |
| `CSTY` | Combat Style | 41 |
| `PLST` | Default Pack List | 42 |
| `PWFD` | Wait-For-Dialogue Package | 43 |
| `LRTB` | LocRefType Boss | 44 |
| `VLOC` | Virtual Location | 45 |
| `PLOC` | PersistAll Location | 46 |
| `INVP` | Inventory Player | 47 |
| `PTNP` | Pathing Test NPC | 48 |
| `FPCS` | Favor Cost Small | 49 |
| `FPCM` | Favor Cost Medium | 50 |
| `FPCL` | Favor Cost Large | 51 |
| `FGPD` | Favor Gifts Per Day | 52 |
| `AASW` | Action Swim State Change | 53 |
| `AALK` | Action Look | 54 |
| `AALA` | Action LeftAttack | 55 |
| `AALD` | Action LeftReady | 56 |
| `AALR` | Action LeftRelease | 57 |
| `AALI` | Action LeftInterrupt | 58 |
| `AARA` | Action RightAttack | 59 |
| `AARD` | Action RightReady | 60 |
| `AARR` | Action RightRelease | 61 |
| `AARI` | Action RightInterrupt | 62 |
| `AADA` | Action DualAttack | 63 |
| `AADL` | Action DualRelease | 64 |
| `AAAC` | Action Activate | 65 |
| `AAJP` | Action Jump | 66 |
| `AAFA` | Action Fall | 67 |
| `AALN` | Action Land | 68 |
| `AASN` | Action Sneak | 69 |
| `AAVC` | Action Voice | 70 |
| `AAVD` | Action VoiceReady | 71 |
| `AAVR` | Action VoiceRelease | 72 |
| `AAVI` | Action VoiceInterrupt | 73 |
| `AAID` | Action Idle | 74 |
| `AAST` | Action Sprint Start | 75 |
| `AASP` | Action Sprint Stop | 76 |
| `AADR` | Action Draw | 77 |
| `AASH` | Action Sheath | 78 |
| `ALPA` | Action Left Power Attack | 79 |
| `AAPA` | Action Right Power Attack | 80 |
| `ADPA` | Action Dual Power Attack | 81 |
| `AAS1` | Action Stagger Start | 82 |
| `AABH` | Action Block Hit | 83 |
| `AABA` | Action Block Anticipate | 84 |
| `AARC` | Action Recoil | 85 |
| `AAR2` | Action Large Recoil | 86 |
| `AAB1` | Action Bleedout Start | 87 |
| `AAB2` | Action Bleedout Stop | 88 |
| `AAIS` | Action Idle Stop | 89 |
| `AAWH` | Action Ward Hit | 90 |
| `AAFQ` | Action Force Equip | 91 |
| `AASC` | Action Shield Change | 92 |
| `AAPS` | Action Path Start | 93 |
| `AAPE` | Action Path End | 94 |
| `AALM` | Action Large Movement Delta | 95 |
| `AAF1` | Action Fly Start | 96 |
| `AAF2` | Action Fly Stop | 97 |
| `AAH1` | Action Hover Start | 98 |
| `AAH2` | Action Hover Stop | 99 |
| `AABI` | Action Bumped Into | 100 |
| `AASS` | Action Summoned Start | 101 |
| `ATKI` | Action Talking Idle | 102 |
| `ALTI` | Action Listen Idle | 103 |
| `AADE` | Action Death | 104 |
| `AADW` | Action Death Wait | 105 |
| `AIDW` | Action Idle Warn | 106 |
| `AMST` | Action Move Start | 107 |
| `AMSP` | Action Move Stop | 108 |
| `ATRI` | Action Turn Right | 109 |
| `ATLE` | Action Turn Left | 110 |
| `ATSP` | Action Turn Stop | 111 |
| `AMFD` | Action Move Forward | 112 |
| `AMBK` | Action Move Backward | 113 |
| `AMLT` | Action Move Left | 114 |
| `AMRT` | Action Move Right | 115 |
| `ARAG` | Action Reset Animation Graph | 116 |
| `AKDN` | Action Knockdown | 117 |
| `AAGU` | Action Get Up | 118 |
| `ASID` | Action Idle Stop Instant | 119 |
| `ARGI` | Action Ragdoll Instant | 120 |
| `AWWS` | Action Waterwalk Start | 121 |
| `AREL` | Action Reload | 122 |
| `PUSG` | Pickup Sound Generic | 123 |
| `PDSG` | Putdown Sound Generic | 124 |
| `PUSW` | Pickup Sound Weapon | 125 |
| `PDSW` | Putdown Sound Weapon | 126 |
| `PUSA` | Pickup Sound Armor | 127 |
| `PDSA` | Putdown Sound Armor | 128 |
| `PUSB` | Pickup Sound Book | 129 |
| `PDSB` | Putdown Sound Book | 130 |
| `PUSI` | Pickup Sound Ingredient | 131 |
| `PDSI` | Putdown Sound Ingredient | 132 |
| `HVSS` | Harvest Sound | 133 |
| `HVFS` | Harvest Failed Sound | 134 |
| `WBSN` | Ward Break Sound | 135 |
| `WASN` | Ward Absorb Sound | 136 |
| `WDSN` | Ward Deflect Sound | 137 |
| `MFSN` | Magic Fail Sound | 138 |
| `SFSN` | Shout Fail Sound | 139 |
| `HFSD` | Heartbeat Sound Fast | 140 |
| `HSSD` | Heartbeat Sound Slow | 141 |
| `IMLH` | Imagespace: Low Health | 142 |
| `SCSD` | Soul Captured Sound | 143 |
| `NASD` | No-Activation Sound | 144 |
| `MMSD` | Map Menu Looping Sound | 145 |
| `DDSC` | Dialogue Voice Category | 146 |
| `NDSC` | Non-Dialogue Voice Category | 147 |
| `SFDC` | SFX To Fade In Dialogue Category | 148 |
| `PDMC` | Pause During Menu Category (Fade) | 149 |
| `PIMC` | Pause During Menu Category (Immediate) | 150 |
| `PDLC` | Pause During Loading Menu Category | 151 |
| `MDSC` | Music Sound Category | 152 |
| `SMSC` | Stats Mute Category | 153 |
| `SSSC` | Stats Music | 154 |
| `MTSC` | Master Sound Category | 155 |
| `TSSC` | Time Sensitive Sound Category | 156 |
| `DOP2` | Dialogue Output Model (3D) | 157 |
| `DOP3` | Dialogue Output Model (2D) | 158 |
| `POPM` | Player's Output Model (1st Person) | 159 |
| `P3OM` | Player's Output Model (3rd Person) | 160 |
| `IOPM` | Interface Output Model | 161 |
| `RVBT` | Reverb Type | 162 |
| `UWLS` | Underwater Loop Sound | 163 |
| `URVT` | Underwater Reverb Type | 164 |
| `HRSK` | Keyword - Horse | 165 |
| `UNDK` | Keyword - Undead | 166 |
| `NPCK` | Keyword - NPC | 167 |
| `KWBR` | Keyword - BeastRace | 168 |
| `KWDM` | Keyword - DummyObject | 169 |
| `KWGE` | Keyword - UseGeometryEmitter | 170 |
| `KWMS` | Keyword - MustStop | 171 |
| `KWUA` | Keyword - UpdateDuringArchery | 172 |
| `KWOT` | Keyword - Skip Outfit Items | 173 |
| `FTHD` | Male Face Texture Set: Head | 174 |
| `FTMO` | Male Face Texture Set: Mouth | 175 |
| `FTEL` | Male Face Texture Set: Eyes | 176 |
| `FTHF` | Female Face Texture Set: Head | 177 |
| `FTMF` | Female Face Texture Set: Mouth | 178 |
| `FTRF` | Female Face Texture Set: Eyes | 179 |
| `IMID` | ImageSpaceModifier for inventory menu. | 180 |
| `PTEM` | Package template | 181 |
| `MMCL` | Main Menu Cell | 182 |
| `DMWL` | Default MovementType: Walk | 183 |
| `DMRN` | Default MovementType: Run | 184 |
| `DMSW` | Default MovementType: Swim | 185 |
| `DMFL` | Default MovementType: Fly | 186 |
| `DMSN` | Default MovementType: Sneak | 187 |
| `DMSP` | Default MovementType: Sprint | 188 |
| `SPFK` | Keyword - Special Furniture | 189 |
| `FFFP` | Keyword - Furniture Forces 1st Person | 190 |
| `FFTP` | Keyword - Furniture Forces 3rd Person | 191 |
| `AFNP` | Keyword - Activator Furniture No Player | 192 |
| `TKGS` | Telekinesis Grab Sound | 193 |
| `TKTS` | Telekinesis Throw Sound | 194 |
| `WMWE` | World Map Weather | 195 |
| `HMPC` | Help Manual PC | 196 |
| `HMXB` | Help Manual XBox | 197 |
| `TKAM` | Keyword - Type Ammo | 198 |
| `TKAR` | Keyword - Type Armor | 199 |
| `TKBK` | Keyword - Type Book | 200 |
| `TKIG` | Keyword - Type Ingredient | 201 |
| `TKKY` | Keyword - Type Key | 202 |
| `TKMS` | Keyword - Type Misc | 203 |
| `TKSG` | Keyword - Type SoulGem | 204 |
| `TKWP` | Keyword - Type Weapon | 205 |
| `TKPT` | Keyword - Type Potion | 206 |
| `BENW` | Base Weapon Enchantment | 207 |
| `BENA` | Base Armor Enchantment | 208 |
| `BAPO` | Base Potion | 209 |
| `BAPS` | Base Poison | 210 |
| `DRAK` | Keyword - Dragon | 211 |
| `MVBL` | Keyword - Movable | 212 |
| `ABSE` | Art Object - Absorb Effect | 213 |
| `WEML` | Weapon Material List | 214 |
| `ARTL` | Armor Material List | 215 |
| `DIEN` | Keyword - Disallow Enchanting | 216 |
| `FTML` | Favor travel marker location | 217 |
| `LKHO` | Keyword - Hold Location | 218 |
| `CWOK` | Keyword - Civil War Owner | 219 |
| `CWNE` | Keyword - Civil War Neutral | 220 |
| `LRSO` | LocRefType - Civil War Soldier | 221 |
| `KWDO` | Keyword - ClearableLocation | 222 |
| `LRRD` | LocRefType - Resource Destructible | 223 |
| `HCLL` | FormList - Hair Color List | 224 |
| `CMPX` | Complex Scene Object | 225 |
| `RUSG` | Keyword - Reusable SoulGem | 226 |
| `ANML` | Keyword - Animal | 227 |
| `DAED` | Keyword - Daedra | 228 |
| `BEEP` | Keyword - Robot | 229 |
| `NRNT` | Keyword - Nirnroot | 230 |
| `FTGF` | Fighters' Guild Faction | 231 |
| `MGGF` | Mages' Guild Faction | 232 |
| `TVGF` | Thieves' Guild Faction | 233 |
| `DBHF` | Dark Brotherhood Faction | 234 |
| `JRLF` | Jarl Faction | 235 |
| `AWWW` | Bunny Faction | 236 |
| `PIVV` | Player Is Vampire Variable | 237 |
| `PIWV` | Player Is Werewolf Variable | 238 |
| `NMRD` | Road Marker | 239 |
| `SAT1` | Keyword: Scale Actor To 1.0 | 240 |
| `VAMP` | Keyword: Vampire | 241 |
| `FORG` | Keyword: Forge | 242 |
| `COOK` | Keyword: Cooking Pot | 243 |
| `SMLT` | Keyword: Smelter | 244 |
| `TANN` | Keyword: Tanning Rack | 245 |
| `HBLK` | Help - Basic Lockpicking (PC) | 246 |
| `HBLX` | Help - Basic Lockpicking (Console) | 247 |
| `HBFG` | Help - Basic Forging | 248 |
| `HBCO` | Help - Basic Cooking | 249 |
| `HBML` | Help - Basic Smelting | 250 |
| `HBTA` | Help - Basic Tanning | 251 |
| `HBOC` | Help - Basic Object Creation | 252 |
| `HBEC` | Help - Basic Enchanting | 253 |
| `HBSM` | Help - Basic Smithing Weapon | 254 |
| `HBSA` | Help - Basic Smithing Armor | 255 |
| `HBAL` | Help - Basic Alchemy | 256 |
| `HBBR` | Help - Barter | 257 |
| `HBLU` | Help - Leveling up | 258 |
| `HBSK` | Help - Skills Menu | 259 |
| `HBMM` | Help - Map Menu | 260 |
| `HBJL` | Help - Journal | 261 |
| `HBLH` | Help - Low Health | 262 |
| `HBLM` | Help - Low Magicka | 263 |
| `HBLS` | Help - Low Stamina | 264 |
| `HBHJ` | Help - Jail | 265 |
| `HBFT` | Help - Teamate Favor | 266 |
| `HBWC` | Help - Weapon Charge | 267 |
| `HBFS` | Help - Favorites | 268 |
| `KHFL` | Kinect Help FormList | 269 |
| `HBFM` | Help - Flying Mount | 270 |
| `HBTL` | Help - Target Lock | 271 |
| `HBAT` | Help - Attack Target | 272 |
| `LSIS` | Imagespace: Load screen | 273 |
| `WMDA` | Keyword - Weapon Material Daedric | 274 |
| `WMDR` | Keyword - Weapon Material Draugr | 275 |
| `WMDH` | Keyword - Weapon Material DraugrHoned | 276 |
| `WMDW` | Keyword - Weapon Material Dwarven | 277 |
| `WMEB` | Keyword - Weapon Material Ebony | 278 |
| `WMEL` | Keyword - Weapon Material Elven | 279 |
| `WMFA` | Keyword - Weapon Material Falmer | 280 |
| `WMFH` | Keyword - Weapon Material FalmerHoned | 281 |
| `WMGL` | Keyword - Weapon Material Glass | 282 |
| `WMIM` | Keyword - Weapon Material Imperial | 283 |
| `WMIR` | Keyword - Weapon Material Iron | 284 |
| `WMOR` | Keyword - Weapon Material Orcish | 285 |
| `WMST` | Keyword - Weapon Material Steel | 286 |
| `WMWO` | Keyword - Weapon Material Wood | 287 |
| `WTBA` | Keyword - WeaponTypeBoundArrow | 288 |
| `AODA` | Keyword - Armor Material Daedric | 289 |
| `AODP` | Keyword - Armor Material Dragonplate | 290 |
| `AODS` | Keyword - Armor Material Dragonscale | 291 |
| `AODB` | Keyword - Armor Material Dragonbone | 292 |
| `AODW` | Keyword - Armor Material Dwarven | 293 |
| `AOEB` | Keyword - Armor Material Ebony | 294 |
| `AOEL` | Keyword - Armor Material Elven | 295 |
| `AOES` | Keyword - Armor Material ElvenSplinted | 296 |
| `AOFL` | Keyword - Armor Material FullLeather | 297 |
| `AOGL` | Keyword - Armor Material Glass | 298 |
| `AOHI` | Keyword - Armor Material Hide | 299 |
| `AOIM` | Keyword - Armor Material Imperial | 300 |
| `AOIH` | Keyword - Armor Material ImperialHeavy | 301 |
| `AOIR` | Keyword - Armor Material ImperialReinforced | 302 |
| `AOFE` | Keyword - Armor Material Iron | 303 |
| `AOIB` | Keyword - Armor Material IronBanded | 304 |
| `AOOR` | Keyword - Armor Material Orcish | 305 |
| `AOSC` | Keyword - Armor Material Scaled | 306 |
| `AOST` | Keyword - Armor Material Steel | 307 |
| `AOSP` | Keyword - Armor Material SteelPlate | 308 |
| `AOSK` | Keyword - Armor Material Stormcloak | 309 |
| `AOSD` | Keyword - Armor Material Studded | 310 |
| `GCK1` | Keyword - Generic Craftable Keyword 01 | 311 |
| `GCK2` | Keyword - Generic Craftable Keyword 02 | 312 |
| `GCK3` | Keyword - Generic Craftable Keyword 03 | 313 |
| `GCK4` | Keyword - Generic Craftable Keyword 04 | 314 |
| `GCK5` | Keyword - Generic Craftable Keyword 05 | 315 |
| `GCK6` | Keyword - Generic Craftable Keyword 06 | 316 |
| `GCK7` | Keyword - Generic Craftable Keyword 07 | 317 |
| `GCK8` | Keyword - Generic Craftable Keyword 08 | 318 |
| `GCK9` | Keyword - Generic Craftable Keyword 09 | 319 |
| `GCKX` | Keyword - Generic Craftable Keyword 10 | 320 |
| `JWLR` | Keyword - Jewelry | 321 |
| `KWCU` | Keyword - Cuirass | 322 |
| `LMHP` | Local Map Hide Plane | 323 |
| `SLDM` | Snow LOD Material | 324 |
| `SLHD` | Snow LOD Material (HD) | 325 |
| `ALDM` | Ash LOD Material | 326 |
| `ALHD` | Ash LOD Material (HD) | 327 |
| `DGFL` | DialogueFollower Quest | 328 |
| `PTFR` | PotentialFollower Faction | 329 |
| `AVWP` | Werewolf Available Perks | 330 |
| `AVVP` | Vampire Available Perks | 331 |
| `RIWR` | Werewolf Race | 332 |
| `RIVR` | Vampire Race | 333 |
| `RIVS` | Vampire Spells | 334 |
| `DMXL` | Dragon Mount No Land List | 335 |
| `PCMD` | Player Can Mount Dragon Here List | 336 |
| `FMYS` | Flying Mount - Allowed Spells | 337 |
| `FMNS` | Flying Mount - Disallowed Spells | 338 |
| `MNT2` | Keyword - Mount | 339 |
| `AIVC` | Verlet Cape | 340 |
| `FTNP` | Furniture Test NPC | 341 |
| `COEX` | Keyword - Conditional Explosion | 342 |
| `VFNC` | Vampire Feed No Crime Faction | 343 |
| `KWSP` | Skyrim - Worldspace | 344 |
| `ALBM` | Keyword - Armor Material Light Bonemold | 345 |
| `ALCH` | Keyword - Armor Material Light Chitin | 346 |
| `ALNC` | Keyword - Armor Material Light Nordic | 347 |
| `ALSM` | Keyword - Armor Material Light Stalhrim | 348 |
| `FMFF` | Flying Mount - Fly Fast Worldspaces | 349 |
| `AHBM` | Keyword - Armor Material Heavy Bonemold | 350 |
| `AHCH` | Keyword - Armor Material Heavy Chitin | 351 |
| `AHNC` | Keyword - Armor Material Heavy Nordic | 352 |
| `AHSM` | Keyword - Armor Material Heavy Stalhrim | 353 |
| `WPNC` | Keyword - Weapon Material Nordic | 354 |
| `WPSM` | Keyword - Weapon Material Stalhrim | 355 |

## High-value groups

- **Currency/items:** GOLD, LKPK, SKLK.
- **Core factions:** PFAC, GFAC, follower/favor/crime-related keys.
- **Music/audio:** DFMS, BTMS, DTMS, SCMS, sound-category/output-model/reverb keys.
- **Animation actions:** the large AA*/A*/movement action family used by engine behavior/action systems.
- **Type keywords:** TKAM/TKAR/TKBK/TKIG/TKKY/TKMS/TKSG/TKWP/TKPT.
- **Crafting:** FORG, COOK, SMLT, TANN, GCK1–GCKX.
- **Materials:** weapon/armor material keywords.
- **Followers:** DGFL, PTFR.
- **Transformations:** WWSP, AVWP, AVVP, RIWR, RIVR, RIVS, PIVV, PIWV.
- **Flying mounts:** DLZM/DCZM, DMXL, PCMD, FMYS, FMNS, FMFF, MNT2.
- **LOD/world:** SLDM, SLHD, ALDM, ALHD, KWSP.

## Diagnostic rules

1. A Default Object key is a semantic engine slot, not merely an EditorID.
2. If a mod changes a DOBJ assignment, the effect can be global and non-obvious.
3. Runtime `SetForm` can make the active mapping differ from xEdit's static DOBJ winner.
4. Crafting-menu category behavior uses specific Default Object slots and cannot be extended indefinitely by inventing keywords alone.
5. Record the original and replacement Form when a mod intentionally remaps a key.
6. Because this catalog is sourced from SKSE master rather than a pinned SKSE release tag, retain the blob SHA and diff future snapshots before treating new keys as historical facts.
