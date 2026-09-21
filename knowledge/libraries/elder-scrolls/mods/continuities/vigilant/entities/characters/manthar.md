# Manthar

- Continuity: `tes.mod.vigilant`
- Historical role: sorcerer and architect of the Alessian Order
- Boss form: `NPC_ 021146D9` / `zzzCHBossBoneLord` — **Sorcerer Manthar**
- Summon form: `NPC_ 0213B503` / `zzzCHSummonBoneLord` — **Sorcerer Manthar**
- Placed boss reference: `ACHR 021146DA`
- Encounter location: **Funeral Temple** (`CELL 021114AF`)

## Saint tradition

`BOOK 020CB0DF` / *The Eight Saints of Cyrod* describes Manthar as a sorcerer and architect of the Alessian Order.

It says he:
- worked with **Nenyond**;
- helped construct hundreds of priories funded by Nenyond;
- participated in the construction of Nenyond's underground priory;
- disappeared together with Nenyond while exploring Dawn Era ruins uncovered during the work.

The book later says **Silorn** entered the sealed ruins searching for Nenyond and Manthar and never returned intact.

## VIGILANT implementation

The ESM gives Manthar a concrete post-historical identity:

- `021146D9` — **Sorcerer Manthar**, implemented as the `zzzCHBossBoneLord` NPC;
- `0213B503` — a summon version of Sorcerer Manthar;
- `MGEF 0213B504` — **Conjure Sorcerer Manthar**;
- `ACHR 021146DA` — the boss form is physically placed in **Funeral Temple**.

The Funeral Temple is directly linked by the Coldharbour door graph to **Nenyond's Underground Priory**, making Manthar's boss placement spatially consistent with the disappearance story preserved in *The Eight Saints of Cyrod*.

## Bone Lord transformation pass

A focused raw-record pass is preserved at:

`analysis/manthar-bone-lord.md`

The key result is that the ESM contains **no Manthar-specific transformation event**.

A whole-plugin FormID scan found the boss base `021146D9` referenced only by its placed actor `021146DA`; neither the boss base nor the placed actor is owned by a dedicated transformation quest or scene.

The boss VMAD uses only generic encounter scripts:

- `masterambushscript`
- `defaultActivateLinkedRefOnceOnDeath`
- `CHModKarmaOnDeath`

The boss is already configured as **Sorcerer Manthar** using the **Alessian Lawmage Race** and **Bone Lord** skin when encountered.

### Death-to-summon chain

Manthar's death list `LVLI 021280D4` includes:

- `BOOK 0213B506` / **Necromancy Tome: Sorcerer Manthar**

The tome teaches `SPEL 0213B505` / **Conjure Sorcerer Manthar**, which summons `NPC_ 0213B503` / `zzzCHSummonBoneLord`.

Thus the ESM explicitly supports:

**Bone Lord Manthar defeated → Manthar necromancy tome acquired → summonable Bone Lord Manthar**

That explains the later summon form, but not the original transformation of historical Manthar.

### Sithis ring caution

The boss death list also contains **Sithis' Eye Ring**. Its enchantment is **Twin Souls**, and the ring participates in a broader Black Hand/Sithis dialogue and crafting system.

It is therefore not evidence that Sithis transformed Manthar.

### Current conclusion

The identity continuity is strong; the mechanism is not.

The ESM proves the historical Manthar and Bone Lord Manthar are intended as one identity cluster, but does not tell us whether the historical body was reanimated, reconstructed by Coldharbour, altered by the buried ruins, affected by the Stone, or transformed by some other agent.

Until the external script/BSA layer is available, that gap should remain explicit.

## Evidence limits

No INFO records currently resolve uniquely to Manthar. His surviving role is therefore reconstructed from:

1. the saint biography;
2. NPC identity/name;
3. placed boss form;
4. summon/magic-effect implementation;
5. the Nenyond/Funeral Temple geography.

The ESM strongly supports that VIGILANT intends **Sorcerer Manthar** to be the same historical identity cluster described in the saint text, but it does not yet explain how the missing architect became the Bone Lord boss form.

## Canon boundary

Manthar's Alessian biography, disappearance with Nenyond, and later Bone Lord manifestation belong to `tes.mod.vigilant` unless separately corroborated by licensed Elder Scrolls sources.
