# VMAD linkage pass 01

Continuity: tes.mod.vicn.unslaad
Primary source: translated Unslaad.esm 3.0.6

This pass reads **embedded VMAD script names and property names only**.

It does not claim access to unseen Papyrus source bodies. Property names are implementation evidence for how records are wired in the plugin.

## The Owl Flies at Dusk — QUST 031DFDFB

Primary fragment script:
- QF_zzzCrbMq07_031DFDFB

High-value VMAD property names include:
- MuralTrg
- CradleKey
- RevealOwl
- OwlShadow
- FireLitTRG
- BrazierFire
- GreatDragonSoul
- DoorFuture
- Alias_Cradle
- Alias_MuralMarker
- Alias_DollMarker
- Alias_BlackOwl
- Alias_GrayOwl
- Alias_JacobeeTA
- ScNightmare
- ScInfection
- ScFarewell

This directly confirms that the Mural, Dragon's Cradle, ice-doll/future path, soul-fire brazier, and Gray/Black Owl sequence are one implementation graph.

### Mural activator
ACTI 031DFE1C / Mural of Jhunal has script:
- CrbTrgSetstageOnAct

Properties:
- StageTo
- myQuest

The Mural itself is therefore a quest-stage trigger; its visual mural content is still not exposed by this metadata.

### Ice Doll
ACTI 031E26B8 has:
- CrbDovahkiinTriggerScript
- StageTo
- MsgDovahkiin
- myQuest

### Brazier
ACTI 031E4F02 uses the same generic trigger script/property pattern.

### Gray-Owl mind trigger
ACTI 031E4F3C has:
- CrbMq07DragonfireProtectScript
- MsgErosio
- Erosio
- Mq07

This is direct implementation support for the "Gray Owl worms its way into your mind" message belonging to the Mq07 dragonfire/protection sequence.

## Lingering Snow — QUST 03117B3F

Primary fragment script:
- QF_zzzCrbMq05_03117B3F

High-value property names include:
- DovahkiinBody
- Alias_Dragonslayer
- DovahBarrier
- MagnusFire
- MagnusFireLit
- MagnusFireBoom
- MagnusBeacon
- Alias_Owl
- Alias_OwlWound
- OwlAbility
- BossRush
- CrbMq06
- CrbMq07
- LizzTimeWarpMarker
- DoorPresent
- DoorLU
- Alias_Lizz
- Alias_Ulliss
- Alias_Aisha
- Alias_Kedama

This directly links Dov-Ah-Kiin, Magnus-fire, Owl, time-warp, Lost-Unslaad/present doors, and the transition into later quests at the implementation layer.

## The Final Journey — QUST 03465EBF

Attached scripts include:
- CrbMq08QuestScript
- QF_zzzCrbMq08_03465EBF

High-value property names include:
- DoorLyg
- Alias_IceMirrorMarker
- Alias_LygMidMarker
- Alias_LygEndMarker
- Alias_IceSealMarker
- SealTrg
- WordSealRef
- Alias_WESMarker
- WESEnt
- AlduinPortal
- AlduinMouth
- Alias_Cleverman
- Alias_Woody
- Alias_Arkved
- Alias_Boss
- Mq09

This is hard implementation evidence that **Lyg**, the **ice mirror**, and the ice-seal route are deliberately wired as one quest mechanism.

It substantially strengthens the existing Herkel dialogue interpretation of the mirror as a route to Lyg.

## Loveletter to the Fifth Era — QUST 0347A32B

Primary fragment script:
- QF_zzzCrbMq09_0347A32B

High-value properties include:
- Alias_ControlUnitMarker
- Alias_ShorMarker
- ShorTrigger
- ShorMask
- HeartRef
- HeartAct
- Alias_Herkel
- Mq08
- Mq10

The associated Control Unit activator has:
- CrbKalpicShipControlUnitScript
- StageTo
- MsgAccepted
- MsgDenied
- myQuest
- ReqQuest

This confirms the ship control unit is explicitly scripted as a quest-gated transition object.

## Loveletter gate / end-act trigger

ACTI 033CB45A has:
- CrbTeleportToEndActTrgScript
- TeleportMarker
- MsgReqLoveletter
- qLoveLetter

The property name **qLoveLetter** is direct implementation evidence that the "something timeless" access gate is specifically wired to the Loveletter quest/state rather than merely being interpreted that way from nearby text.

## GC9 Insight

ACTI 034C6343 / GC9: John Satisfaction has:
- CrbActMessageLikedContainer
- MyMsg

Combined with the reference's VMAD pointer to MESG 034C6340, this confirms the GC9 object/message pairing directly.

## Method boundary

VMAD property names prove plugin wiring and developer-intended associations.

They do not reveal:
- the full Papyrus function bodies;
- runtime branch logic not represented in initial properties;
- whether a property name is metaphorical or purely technical.

Use this layer to strengthen links, not to invent script behavior.

## Resolution summary

This VMAD pass is sufficient to close the currently listed high-value wiring questions:

- Mq07: Mural → Cradle → future ice doll → soul-fire → Gray/Black Owl graph;
- Mq05: Dov-Ah-Kiin → Magnus-fire → Owl → Lizz time-warp → present/Lost-Unslaad routing;
- Mq08: ice mirror → Lyg route → ice seal / World-Eater route;
- Mq09: Loveletter-gated end-act transition and Kalpic Ship control unit;
- GC9 object → message pairing.

Remaining unknowns are script-body/runtime details that are **not exposed by embedded property metadata**. Unless Papyrus source or bytecode is later added, those should be labeled unavailable rather than left as open ingestion tasks.

VMAD property names remain structural evidence only; they do not independently settle cosmological interpretation.
