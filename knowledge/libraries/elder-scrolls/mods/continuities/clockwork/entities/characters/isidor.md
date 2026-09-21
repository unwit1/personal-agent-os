# Isidor

Continuity: `tes.mod.clockwork`  
Entity type: adventurer / Camilla's intended expedition partner / opening assailant  
NPC: `0505F157` (`CLWIsidor`)

## Continuity summary

Isidor is Camilla's intended partner for the expedition into the newly uncovered ruins. Camilla's note tells him to meet her near Cragwallow Slope and to acquire the best equipment he can, even by attacking a traveler if necessary.

The ESP resolves the opening encounter structurally: Isidor's NPC carries `defaultSetStageOnDeath` configured to set *Foot Of The Mountain* to stage 10. Stage 10 is the journal entry for killing/encountering the “strange assailant,” and objective 10 targets quest alias 8, `IsidorAlias`.

Isidor is therefore the road assailant whose body supplies Camilla's Note, not merely a separate expedition partner inferred from the note.

## Evidence

- `BOOK 0505F158` — *Camilla's Note*; instructs Isidor to obtain equipment and is the note recovered in the opening quest chain.
- `NPC_ 0505F157` VMAD — `defaultSetStageOnDeath` → `QUST 0505F6C9` stage 10.
- `QUST 0505F6C9` — objective 10 targets alias 8 `IsidorAlias`; stage 10 describes the strange assailant's body.
- `BOOK 0505F158` VMAD — acquire note → stage 20; close/read note → stage 30.
