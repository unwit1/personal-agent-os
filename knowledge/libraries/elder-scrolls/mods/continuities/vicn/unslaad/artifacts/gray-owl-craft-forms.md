# Gray OWL / Gray EGG / Shadow craft forms

Continuity: tes.mod.vicn.unslaad  
Primary source: translated Unslaad.esm 3.0.6  
Unlock quest: zzzCrbMq07 / 031DFDFB — **The Owl Flies at Dusk**

Three lore-bearing Gray-Owl ARMO records are implemented as craftable post-quest forms.

## Gray OWL

ARMO 031E7787 / zzzCrbClothGrayOwl  
Display name: **Gray OWL**

Description:
> The second CHICK. Once he was a mage of Atmora who sought to reach the "dragon".

Recipe:
- COBJ 031E778A / zzzCrbRecipeGrayOwl
- output: Gray OWL
- one ingredient, Skyrim master form 0003AD60
- crafting keyword: KYWD 0305264E / zzzCrbCraftingSnowBall
- condition: GetQuestCompleted(zzzCrbMq07) == 1

## Gray EGG

ARMO 031E7788 / zzzCrbClothGrayOwlEgg  
Display name: **Gray EGG**

Description:
> An EGG crushed by a Chick Trader of Anequina. Its "future" is now lost.

Recipe:
- COBJ 031E778B / zzzCrbRecipeGrayOwlEgg
- same single-ingredient / crafting-keyword / quest-completion structure

This record also uses the Gray Owl race as its RNAM race association.

## Shadow of the Gray OWL

ARMO 031F4114 / zzzCrbClothGrayOwl_Shadow  
Display name: **Shadow of the Gray OWL**

Description:
> The secret of Saarthal granted him insight into higher planes.

Recipe:
- COBJ 031F4115 / zzzCrbRecipeGrayOwlShadow
- same single-ingredient / crafting-keyword / quest-completion structure

## Recipe significance

All three recipes use condition function **543 / GetQuestCompleted** against QUST 031DFDFB.

They therefore become available only after **The Owl Flies at Dusk** is completed.

This makes their DESC text post-quest interpretive/reward material, not random ambient equipment flavor.

## Current reading

The three forms present complementary statements:
- **Gray OWL** → second CHICK; Atmoran mage; sought the "dragon";
- **Gray EGG** → EGG crushed by an Anequina Chick Trader; future lost;
- **Shadow** → Saarthal secret; insight into higher planes.

Together they tighten the Gray Owl's connection to:
- Chick-Trader terminology;
- Atmora;
- Saarthal;
- the pursuit of dragonhood;
- EGG/future/dream language.

They do not by themselves explain what "second" counts, who the Chick Trader was, or what specific "future" was lost.
