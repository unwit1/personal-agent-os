# Runtime behavior evidence

Continuity: `tes.mod.clockwork`

This layer summarizes non-quest VMAD on magic effects and NPC archetypes. It answers “what does the mod actually script this actor/effect to do?” while keeping implementation evidence separate from character testimony.

## Shadow

### Tunnel distortion

`MGEF 0507FD83` / `CLWShadowSlowTimeEffect` uses a dedicated Shadow image-space modifier and fade-from-black outro. Combined with the `Shadow Under The Mountain` slow-time spell, this corroborates the staged perceptual/time-distortion described in Camilla's trail.

### Final fight → Lamashtu remarks

Two Shadow combat forms use dedicated scripts:

- `05769C7E` / `CLWShadowBleedoutScript`
- `05778FE2` / `CLWShadowDyingScript`

Both reference `SCEN 0576EDA3` / `CLWSQ04LamRemarksScene01`. The final-dying script also:
- sets `CLWSQ04ShadFightPhaseGLOB` to **3**;
- directly references placed Lamashtu actor `052BE2D6`.

This makes the transition from Shadow's final combat state into Lamashtu's post-reunion dialogue structurally explicit. It supports the event ordering in the story graph; it does not independently prove the metaphysical truth of Lamashtu's later “copies/reflection” interpretation.

## Gilded recovery

Eight generic hostile/ambush Gilded archetypes use `CLWGildedRes01Script`. The script properties point to:

- `0553E847` / **Reanimate (Self)**
- `0554395D` / configurable Gilded-down state
- a Dwarven-sphere heavy-stagger sound

This shows that repeated downing/recovery is an intentional shared Gilded mechanic. Lorekeeper should describe this as **implemented recovery/reanimation behavior**, not automatically as infinite immortality.

## Amalgam

`NPC_ 0559026E` / stage-70 Amalgam uses `CLWAmalgamBleedoutScript`, which points to:

- the stage-70 scene;
- the Sickness Ward retreat marker;
- `Crystalline Heart`;
- a paralysis explosion;
- the common Clockwork teleport explosion;
- grate/portcullis controls;
- a 30-second failsafe.

So the encounter's paralysis-and-retreat sequence is directly scripted into Amalgam's bleedout behavior.

## Recall spell

`CLWRecallToCastleSpellEffectScript` references:

- the MCM fast-travel check;
- the Clockwork Travel Room portal/door;
- the recall marker;
- teleport visual effect;
- a dedicated failure message.

The spell is therefore more than generic teleportation: it maintains a marked return point and a fixed Clockwork endpoint with travel-validity checks.

## Bathing

The bathing effect fires `CLWBathingMsg`. Together with the separate **Clean from Bathing** buff, this forms a deliberate mechanical counterpart to Lahar's claim that cleanliness aids social interaction and disease resistance.

## Interpretation rule

Use runtime evidence to corroborate **behavior and causal sequencing**. Do not let scripts silently override or manufacture lore claims about souls, identity, immortality, or history.
