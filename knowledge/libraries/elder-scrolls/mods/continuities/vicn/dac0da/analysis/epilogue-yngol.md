# Yngol epilogue

**Quest:** `zDcdEpiQYngol`  
**Title:** Epilogue Yngol  
**Source:** `DAc0da.esm:00CED0`  
**Continuity:** `tes.mod.vicn.dac0da`  
**Evidence mode:** QUST/VMAD/REFR/CONT structure; no directly owned dialogue

## Structural role

The Yngol epilogue is not a dialogue scene.

Its quest VMAD contains one direct property:

- `YngolBodyRef` -> `DAc0da.esm:00CECF`

The main **Drowned Nighthawk** quest independently has a direct `qEpiYngol` property pointing to this epilogue quest, proving that the aftermath is launched from Yngol's side-quest state machine.

The epilogue quest has stages 0 and 10 only and no owned DIAL topics.

## YngolCorpseRef

`DAc0da.esm:00CECF` is a placed reference with editor ID:

- `DcdEpiQYngolCorpseRef`

Its record flags are `0x0C00`, including the normal Skyrim **initially disabled** flag. This means the corpse/aftermath state is activated by quest logic rather than always present in the world.

The compiled quest fragment body is not embedded in the ESM, so the exact enable/disable call should remain implementation-pending.

## Enable-parented aftermath

Two separate placed references use `YngolCorpseRef` as their enable parent:

### Dead dragon skeleton

`DAc0da.esm:00CECE` -> base form:

- `DAc0da.esm:003381`
- `zDcdHarakkDragonDeadSkeleton`

This is a static dead-dragon skeleton.

### Reward chest

`DAc0da.esm:00CED2` -> base form:

- `DAc0da.esm:00CED1`
- `zDcdTreasAtmoranChest_YngolHammer`
- FULL: **Chest**

The chest contains:

- three rolls from `zDcdLitemAtmoraCoins`;
- one roll from `zDcdLitemTotem`;
- **Yngol's Forgehammer** (`DAc0da.esm:004335` / `zdcdYngolHammer1H`).

Yngol's Forgehammer has the direct description:

> Damage increases with smithing skill level.

The random totem pool includes items such as:

- Idol of Tsa the Dozing Rat;
- Golden Idol of Tsa the Dozing Rat;
- Silver Idol of Tsa the Dozing Rat;
- Wooden Warrior Idol.

These are reward/inventory evidence, not dialogue claims.

## Branch interpretation

**Drowned Nighthawk** has multiple Yngol outcomes, including a branch in which Yngol flies toward Harakk and another in which he seeks a warrior's death.

Because this epilogue is triggered through quest-state logic and materializes a corpse/skeleton/reward aftermath, it must be treated as a **branch-dependent aftermath** rather than the universal canonical ending of DAc0da's Yngol story.

The ESM structure alone does not prove which exact Drowned Nighthawk branch starts the epilogue; that condition remains dependent on compiled quest fragments/scripts.
