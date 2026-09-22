# Act 4 direct-source recovery — previously incomplete side quests

Continuity: `tes.mod.vigilant`

Source:
- user-supplied translated `Vigilant.esm`
- English Translation (Silent) 1.8.2
- archive dated 2026-06-16

This pass resolves the nine Act 4 quests that were previously marked as missing or partial.

Full recovered response text:
- `dialogue/act4/recovered-sidequests.md`

## 1. More Skooma

- `QUST 021273E0`
- EditorID: `zzzCHSubQuest01`
- title: **More Skooma**
- alias **Khajiit** → `NPC_ 020FED32` / **Ja'zhan**
- alias **TravelMarker** → `REFR 021273E9`

Direct body:
- 2 DIAL topics
- 3 INFO responses

Ja'zhan says:
- he is trapped by leeches and a large guard near the prison entrance;
- he is running out of skooma;
- after the player helps, he can get fresh air and offers to trade cheaply.

Conclusion:
**More Skooma is a Ja'zhan survival/travel-unlock side quest, not a generic skooma quest.**

## 2. Archer of Kyne

- `QUST 021279A1`
- `zzzCHSubQuest02`
- **Archer of Kyne**
- alias **Archer** → `NPC_ 020CA4A9` / **Bourlor**
- alias **Prey** → `NPC_ 020ECCB3` / **Vernaccus**
- alias **ArcherBow** → quest bow alias

Direct body:
- 5 DIAL topics
- 8 INFO responses

Bourlor:
- has practiced knife throwing for centuries without success;
- wants another attempt at Vernaccus;
- can be recruited by returning his bow.

Vernaccus identifies himself as:
- **Bane of Kyne**
- and directly remembers prior humiliation by the player.

Conclusion:
**Archer of Kyne directly links Bourlor and Vernaccus.**

## 3. The Black Worm

- `QUST 02129061`
- `zzzCHSubQuest03`
- **The Black Worm**
- alias **blackworm** → `NPC_ 020AEFE3` / **Black Worm**
- alias **Prisoner** → `NPC_ 0223C4B1` / Dremora Worm Keeper
- alias **TravelMarker** → `REFR 02129623`

Direct body:
- 3 DIAL topics
- 4 INFO responses

The Black Worm:
- asks the player to unlock the cell;
- refuses to identify himself;
- avoids explaining why he is imprisoned;
- uses manipulative/flattering language.

This directly proves the quest title is instantiated by a specific Black Worm NPC.

It does **not** by itself name Mannimarco.

## 4. Funeral

- `QUST 02129BCA`
- `zzzCHSubQuest04`
- **Funeral**
- alias **Sister** → `NPC_ 020B21DB` / **Martha**
- alias **SisterDead** → `NPC_ 02129BE5` / **Martha**

Direct body:
- 8 DIAL topics
- 8 INFO responses

Martha:
- searches for the graves of her family;
- names them **Johan, Simon, and Tlass**;
- says she has searched for years;
- learns the graves are in the **Chapel of Arkay's Cemetery**;
- thanks the player and remains to indulge in nostalgia.

The Sister/SisterDead alias pairing proves a living/skeletal Martha identity transition or variant.

## 5. Knight of Julianos

- `QUST 021265FB`
- `zzzCHSubQuest07`
- **Knight of Julianos**
- alias **Knight** → `NPC_ 020BDABE` / **Sir Henrik**
- alias **KnightDead** → `NPC_ 0212660D` / **Sir Henrik**

Direct body:
- 21 DIAL topics
- 34 INFO responses

Sir Henrik:
- repeatedly gets imprisoned/trapped;
- mentions a slave trader and cheap alcohol;
- searches for fellow knights;
- expects reunion at Mathmalatu Priory;
- asks the player to investigate traces of two knights;
- gives direct Varla testimony;
- discusses the Ayleid prison tower.

This completely resolves the former Sir Henrik source gap.

## 6. Knight of Zenithar

- `QUST 021306FA`
- `zzzCHSubQuest08`
- **Knight of Zenithar**
- alias **Knight** → `NPC_ 020BCF1E` / **Sir Ralvas**
- alias **Cat** → `NPC_ 020FED32` / **Ja'zhan**
- alias **MarkerChapel** → common knight-return marker

Direct body:
- 15 DIAL topics
- 22 INFO responses

Sir Ralvas:
- has lost his head;
- believes he lost it after colliding with a cat;
- claims Dunmer can project speech through the stomach;
- asks the player to recover the head.

Ja'zhan:
- found/stole a strange gold-looking helmet;
- sells it for 100 gold.

The “helmet” is structurally the route to restoring Ralvas's head.

## 7. Knight of Arkay

- `QUST 021C31F2`
- `zzzCHSubQuest10`
- **Knight of Arkay**
- alias **Knight** → `NPC_ 020B081A` / **Sir Torolf**

Direct body:
- 4 DIAL topics
- 4 INFO responses
- scene `SCEN 021C31F3`

Torolf's doctrine:
- God is pain of death and fear;
- overcoming pain/fear makes one divine;
- Arkay supposedly achieved this;
- Torolf has sacrificed blood, flesh, and his own body;
- he invites the player to offer flesh and blood too.

This upgrades Torolf from scene-only to a fully characterized religious extremist.

## 8. Kyne's Dragon

- `QUST 0221ED0C`
- `zzzCHSubQuest11`
- **Kyne's Dragon**
- alias **Dragon** → `NPC_ 0221AF9D` / **Kahkaankrein**
- alias **DragonBLH** → `NPC_ 0251D69A` / memory-form Kahkaankrein
- alias **SoulMarker** → `REFR 022C374C`

Direct body:
- 14 DIAL topics
- 28 INFO responses
- scene `SCEN 022C374B`

Kahkaankrein says:
- a blood curse took his wings;
- he fell into the black sea;
- the last thing he remembers was the Owl's grin;
- Alessians tried to take his blood;
- fellow dragons served Kyne but were deceived by the Owl and turned to stone;
- the dragons abandoned Alduin and chose Kyne and mortals;
- their mission was to protect Kyne's garden;
- Laza were mortal children/shepherds outside the garden, forbidden entry;
- Molag Bal stole and corrupted Kyne's animals;
- Molag Bal repeatedly returned after being killed;
- a pure Feather of Kyne can let him return to Kyne.

This is one of the most important direct-source recoveries for the Laza/Owl/Kyne cluster.

## 9. Knight of Kynareth

- `QUST 02334C8F`
- `zzzCHSubQuest12`
- **Knight of Kynareth**
- alias **JuncanBoss** → `NPC_ 020E0FEB` / **Sir Juncan**
- alias **JuncanSane** → `NPC_ 02334C90` / **Sir Juncan**

Direct body:
- 11 DIAL topics
- 20 INFO responses

Juncan:
- warns about a “flying Worm”;
- says a Vigilant was killed by it;
- knows the fort-key route;
- comments on Melus speaking with a corpse;
- travels as guard for Sir Gregory's artistic pilgrimage;
- gives Varla rumors;
- warns about a blood-smelling barrier tower;
- describes the slums route and distrusts Pepe.

This completely resolves the former Sir Juncan source gap.

## Former gap status

The previous nine-item raw-source priority is now resolved at the ESM dialogue/alias level.

Remaining limitations:
- external PEX statements;
- some runtime state transitions;
- some dynamic alias speaker precision;
- exact item/placement chains not yet exhaustively mapped for every quest.

## High-value new relationship edges

- **Ja'zhan → More Skooma**
- **Bourlor ↔ Vernaccus → Archer of Kyne**
- **Black Worm NPC → The Black Worm**
- **Martha → Funeral**
- **Sir Henrik → Knight of Julianos**
- **Sir Ralvas → Knight of Zenithar**
- **Sir Torolf → Knight of Arkay**
- **Kahkaankrein → Kyne's Dragon**
- **Sir Juncan → Knight of Kynareth**

## Major lore implications

1. The Knights of the Nine cluster is now directly anchored to multiple named side quests.
2. Laza/Owl/Kyne history gains direct testimony from Kahkaankrein.
3. The Black Worm side quest now definitely contains a Black Worm actor, though Mannimarco remains supplementary.
4. Funeral is Martha's family-grave narrative, not the broader Funeral Temple storyline.
5. More Skooma is a Ja'zhan quest.
