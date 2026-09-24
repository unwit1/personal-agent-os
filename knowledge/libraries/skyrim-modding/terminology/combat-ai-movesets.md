# Skyrim Modding Terminology — Combat AI, Movesets, and Attack Frameworks

Imported: 2026-09-24
Status: sourced deep-ingestion pass 8

## Vanilla combat layers

### Combat AI
Engine decision logic choosing approach, attack, block, bash, retreat, spell, power attack and other combat actions.

### CombatStyle
Record containing weights/preferences used by combat AI.

### AttackData
Engine/behavior data describing attack event, timing, angle, stamina/damage multipliers and related attack metadata.

### Attack event
Animation graph event that starts a particular attack branch/clip.

### Attack state
Behavior state representing attack-ready, attack-start, combo or recovery logic.

### Combo
Sequence of attack actions linked according to behavior/runtime conditions.

### Recovery
Post-attack phase before another action can begin.

### Commitment
Design property where an attack's movement/rotation is constrained during execution rather than freely redirected.

### Turn rate
Maximum/weighted actor rotation speed during combat/action states.

### Attack reach
Gameplay/collision concept describing effective melee hit distance.

### Hit frame
Animation time/event window in which attack collision/damage is expected to occur.

### Cancel window
Animation interval during which another action can interrupt/transition out of the current attack.

### I-frame
Temporary invulnerability window, often supplied by dodge/combat frameworks rather than vanilla ordinary movement.

## MCO / ADXP ecosystem

### MCO
Community shorthand for Modern Combat Overhaul / Attack-MCO framework family used by many modern third-person movesets.

### ADXP
Attack-DXP lineage associated with MCO-style behavior where attacks are animation-driven and often use AMR/root motion.

### Moveset
Collection of attack animations plus behavior/OAR/SCAR/AMR metadata determining how they are selected/executed.

### Moveset condition
Condition restricting a moveset by weapon, stance, race, actor, keyword, skill or other context.

### Attack chain
Ordered set of attacks/combo branches.

### Light attack
Ordinary attack branch.

### Power attack
Higher-cost/stronger attack branch.

### Directional attack
Attack selected according to movement/input direction.

### Root-motion attack
Attack whose translation/rotation comes from animation motion data rather than only vanilla actor movement.

### Moveset annotation
Animation metadata carrying framework-specific events or AI/payload information.

## SCAR

### SCAR
**Expansion:** Skyrim Combos AI Revolution. Native AI framework allowing NPCs to use combo-oriented modern combat movesets.

### SCAR ActionData
Framework metadata describing an attack action so AI can evaluate when/how to select it.

### Attack Ready Stage
SCAR 2.x authoring stage that supplies ActionData for initial attacks available from an attack-ready state.

### Attack Combos Stage
SCAR authoring stage defining follow-up combo choices/transitions.

### DummyAnimation
Behavior animation node/clip used as a metadata container for SCAR ActionData rather than necessarily as a visibly played attack.

### SCAR_1hmReadyDummy.hkx
Character behavior dummy animation used by SCAR as the container for first-attack ActionData for applicable humanoid movesets.

### SCAR annotation
Animation annotation encoding ActionData consumed by SCAR.

### AI distance
ActionData range constraint affecting whether an AI attack is suitable for target distance.

### AI angle
ActionData directional constraint affecting attack selection.

### AI chance/weight
Metadata influencing candidate attack choice rather than guaranteeing an action.

### SCAR creature patch
Behavior/moveset support needed for non-character behavior projects where built-in humanoid dummy setup does not apply.

### SCAR 2.x
Newer SCAR framework lineage with documented Attack Ready and Attack Combos authoring stages.

## Precision interaction

### Precision
Native melee collision framework using weapon/body geometry and animation timing.

### Collision capsule/shape
Runtime melee collision volume associated with weapon/attack.

### Collision activation window
Time range during attack when collision is active.

### Hitstop
Brief slowdown/pause feedback on impact.

### Recoil
Animation/gameplay response when weapon collides/attack is blocked depending on framework.

### Weapon trail
Visual effect following attack motion.

### Attack reach mismatch
Moveset visually reaches one distance while gameplay/Precision collision uses another.

## AMR interaction

### Animation Motion Revolution / AMR
Framework enabling animation-authored motion data to drive actor translation/rotation.

### Motion extraction
Reading translation/rotation curve from animation data.

### Motion override
Replacing vanilla actor motion with animation-defined movement during selected clips.

### Root-motion mismatch
Animation contains movement not correctly interpreted by current behavior/framework, causing sliding or teleport-like motion.

## OAR and movesets

### Moveset submod
OAR submod containing weapon/actor-condition-based combat animations.

### Priority overlap
Two OAR combat submods satisfy the same condition; higher applicable priority selects animation.

### Random variant
Multiple equivalent attack clips selected randomly/weighted according to OAR configuration.

### State condition
OAR condition using combat/graph/package/equipment state to choose a moveset.

### IsReplacerEnabled dependency
OAR condition depending on another submod/replacer state.

## Behavior patching

### Attack behavior graph
Havok behavior graph/state machine controlling attack events/transitions.

### AttackReadyStateMachine
Behavior state machine used before attack execution and referenced by SCAR authoring docs.

### Behavior patch
Pandora/Nemesis change to attack graph required when a framework/moveset changes behavior structure/events beyond runtime replacement.

### Runtime-only moveset
Animation replacement that works with existing behavior structure and therefore does not require a custom behavior patch.

### Behavior-dependent moveset
Moveset requiring new events/states/transitions and therefore requiring generated behavior output.

## NPC combat integration

### Player-only moveset
Conditions prevent NPCs from receiving/using the animations.

### NPC moveset
Animation set available to NPC behavior/AI.

### AI compatibility patch
Metadata/behavior config enabling SCAR or another AI framework to understand a player-oriented moveset.

### Creature behavior project
Separate behavior graph for a creature/race family. Human character behavior patches do not automatically apply to creatures.

### Attack intent
AI-selected desire/action independent of whether animation framework ultimately resolves a valid clip.

## Diagnostic rules

1. Separate AI decision, behavior event/state, OAR animation selection, AMR movement and Precision collision.
2. NPC not using a moveset can be lack of SCAR data even when player animations work.
3. A moveset can animate correctly but slide if AMR/root-motion data is missing or mismatched.
4. A moveset can visually connect but miss if Precision collision timing/geometry differs.
5. Behavior generation is required only when graph structure/events change; OAR replacement alone does not imply Pandora/Nemesis regeneration.
6. SCAR metadata/annotations belong to the moveset/behavior support layer, not xEdit plugin conflict resolution.
7. Exact SCAR version matters because 2.x authoring semantics differ from older compatibility guidance.

## Sources

- SCAR upstream: https://github.com/max-su-2019/SCAR
- SCAR 2.x developer manual: https://github.com/max-su-2019/SCAR/blob/main/docs/EN/Developers%20Manual%20For%20SCAR%202.0%2B.md
- SCAR moveset patch tutorial: https://github.com/max-su-2019/SCAR/blob/main/docs/EN/How%20To%20Patch%20Moveset%20For%20SCAR.md
- Precision upstream: https://github.com/ersh1/Precision
- Animation Motion Revolution upstream: https://github.com/alexsylex/AnimationMotionRevolution
- Open Animation Replacer upstream: https://github.com/ersh1/OpenAnimationReplacer
- Pandora Behaviour Engine+: https://github.com/Monitor221hz/Pandora-Behaviour-Engine-Plus

## Version note

SCAR 2.x material should be treated as a newer authoring generation. Older mod pages/guides frequently describe SCAR 1.x assumptions; preserve version scope rather than merging both into one timeless rule.
