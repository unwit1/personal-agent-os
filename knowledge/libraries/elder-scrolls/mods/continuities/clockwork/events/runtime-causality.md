# Clockwork runtime causality overlay

Continuity: `tes.mod.clockwork`

This layer records **implemented causal transitions** that can be recovered from VMAD scripts, stage triggers, activators, packages, scenes, and quest aliases. It complements the narrative graph: journal text says what the player understands, while this file records which game records actually advance or coordinate that state.

Implementation evidence is authoritative for runtime behavior, but it is not automatically an in-universe metaphysical explanation.

## Foot Of The Mountain — Isidor → note → tunnels

The opening progression is unusually explicit:

1. **Isidor dies → stage 10.**  
   `NPC_ 0505F157` / `CLWIsidor` carries `defaultSetStageOnDeath` with `StageToSet = 10` and `myQST = 0505F6C9` / *Foot Of The Mountain*.
2. **Camilla's Note enters the player's inventory → stage 20.**  
   `BOOK 0505F158` carries `defaultsetstageonplayeracquireitem`.
3. **The note is closed after reading → stage 30.**  
   The same BOOK carries `defaultSetStageOnCloseBookNotAlias`.
4. **The tunnel-entry trigger fires → stage 40.**  
   `REFR 050632CB` carries `defaultSetStageOnEnter` for stage 40.

The quest's objective-10 target is alias 8, `IsidorAlias`. Together these records structurally identify the journal's “strange assailant” as **Isidor**, not merely an unnamed bandit associated with Camilla.

## Shadow Under The Mountain — forced forward progression

Three entry/progression triggers set the main quest stages directly:

- `REFR 050632CD` → stage 10
- `REFR 0520CA3E` → stage 20
- `REFR 0520CA43` → stage 30

The separate `CLWShadowManage01Quest` runs stage-conditioned Shadow packages through:

- Velothi Mountain Tunnels for management stages 10/20/30
- Bone Hollow for management stages 40/50

That same internal quest directly references `CLWShadowSlowTimeSpell` / **Shadow Under The Mountain**. Thus the haunting route, Shadow actor state, and slow-time presentation are all runtime-coordinated rather than journal-only narration.

## Steam-Powered — pipeline and machinery state

### Enter repair state

`REFR 05440B5F` sets *Steam-Powered* stage 90 on player entry.

### Ten repairs → stage 100

`ACTI 05440B5C` / **Ruptured Pipeline** runs `CLWPipeRepairScript` and references:

- `CLWSQ02PipeTotal = 10`
- `CLWSQ02PipeCount`
- `MISC 05431799` / **Disassembled Dwemer Pipe**
- objective 90
- `pStage = 100`

This makes the ten-pipe requirement a real counted state transition.

A later trigger, `REFR 054D919B`, sets stage 105. The quest VMAD owns `CLWSQ02Machines01EnableParentREF`, lighting state, siren state, and the Travel Machine recall/autoload parent, showing that *Steam-Powered* is the central machinery-state controller.

### Mechanical repair → can't-leave state

`REFR 054F7875` directly sets stage 130. The associated package `054F7876` targets the player marker inside `CELL 0503C62F` / **Clockwork Castle Travel Room**, while the quest owns the collision and trigger used by the cannot-leave sequence.

This is strong runtime evidence that the supernatural/compulsive block is staged only after the physical machine has been restored.

## Crystalline Heart — Amalgam and the repair chain

### Search/encounter triggers

- `REFR 0552A362` → stage 40
- `REFR 0559027A` → stage 70

The stage-70 Amalgam actor runs `CLWAmalgamBleedoutScript`, tying apparent defeat to paralysis, teleportation, the Sickness Ward retreat marker, portcullis/grate state, and the stage-70 scene.

### Barrier-breach chain

The post-retreat sequence is directly wired through objects:

1. At/after stage 80, `BOOK 0559F638` / **Unfinished Note** is configured to advance the search to stage 90; it also knows the stage-100 path if the needed handle is already obtained.
2. `MISC 0558B137` / **Dwemer Lever Handle** advances stage 90 → 100 when acquired.
3. `ACTI 0558B134` / **Lever Base** consumes/uses that handle and advances to stage 110.
4. `REFR 05562478` / the ballista control runs `CLWBallistaScene01ACTIScript` and sets stage 120 while switching Amalgam-destruction/heart/barrier state.
5. `ACTI 055BDD00` / **Crystal Heart (Empty)** inside Amalgam sets stage 130 when the heart is recovered.

This is a deterministic object-driven chain beneath the journal summary.

### Lamashtu heart transfer — scene-phase state machine

The transfer at stage 140 is not represented as one activator directly setting stage 150. Instead, `SCEN 0565B8B8` and its placed interactables coordinate `GLOB 056567A5` / `CLWSQ03S140ScenePhaseGLOB`.

Confirmed interactive phase advances include:

- Lamashtu chest plate: phase **1 → 2** and later **13 → 14**
- Lamashtu-heart internals: **3 → 4** and later **11 → 12**
- heart/transference box: **5 → 6**
- soul-transference control: **7 → 8**
- filled-heart box interaction: **9 → 10**

The scene fragment owns Lamashtu's active/inactive body references, both heart boxes, the chest plate, the heart static, the transfer machinery, player/Lamashtu scene markers, visual effects, and the same phase global. The intervening phase changes are scene-fragment choreography.

Lorekeeper should therefore describe the heart replacement as a **scripted multi-step procedure** and avoid inventing a single “magic button” transition.

## I Against I — final confrontation and release

`REFR 0573BCD3` advances *I Against I* to stage 40 on activation, placing the player into the Shadow confrontation state.

The two principal final Shadow combat forms then connect combat resolution to the narrative aftermath:

- `CLWShadowBleedoutScript` uses the Shadow fight-phase global, vanish effect, and `CLWSQ04LamRemarksScene01`.
- `CLWShadowDyingScript` sets the fight-phase global to **3**, directly references placed Lamashtu, and starts the same post-fight remarks scene.

This makes the transition from fight → Lamashtu reunion/reinterpretation mechanically explicit.

`REFR 0578D464` later sets stage 70. The final quest also owns/references the exact collision and trigger used by the earlier cannot-leave sequence and the Travel Room portal infrastructure. The player-facing journal establishes stage 200 as the point at which departure is restored; the exact stage-200 fragment body is not reconstructed here, so this overlay does not invent a more specific setter.

## Travel-door follower gating note

Most Terminus return doors carry `DefaultNoFollowDoorScript` with *I Against I* stage 200 as the threshold for follower handling. The Morthal return door is an outlier: it points to *Foot Of The Mountain* with a threshold of 200 even though that quest's parsed stages are 0, 10, 20, 30, 40, and 255.

Because this script is specifically follower-door handling—not the Travel Machine's core player teleport logic—Lorekeeper records this as an **implementation anomaly/outlier**, not an in-world fact and not proof that Morthal travel unlocks differently.
