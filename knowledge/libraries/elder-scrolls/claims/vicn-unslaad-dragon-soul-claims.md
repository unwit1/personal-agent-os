# UNSLAAD — Dragon Soul claims

- Record type: claim bundle
- Status: source-backed
- Continuity: tes.mod.vicn.unslaad
- Tags: Ulliss; Dragon Souls; Lizz; revival; Dragonslayer; Dov-Ah-Kiin

## Claims

### unslaad.ulliss.dragon-soul-conversion
- Proposition: Ulliss can directly convert **one Dragon Soul** into player power: Health, Magicka, Stamina, or perk knowledge.
- Status: supported
- Epistemic mode: direct dialogue + GetIsID speaker attribution + gameplay implementation
- Confidence: very high
- Evidence:
  - Quest zzzCrbsq01 / 03022986
  - all ten INFO rows use GetIsID 030022F6 -> Ulliss
  - `mods/continuities/vicn/unslaad/dialogue/dragon-souls.md`

### unslaad.ulliss.revival-costs-dragon-soul
- Proposition: Reviving Ulliss through **Ancient Dragon Ring + Twinkling Star** spends one Dragon Soul.
- Status: supported
- Epistemic mode: deterministic quest/message implementation
- Confidence: very high
- Evidence:
  - Quest zzzCrbSqResurrection / 0311023D
  - MESG 0311023F / zzzCrbMsgResurrection
  - `mods/continuities/vicn/unslaad/technical/revive-dragon-soul-system.md`

### unslaad.ulliss.constructed-from-dragon-souls
- Proposition: Jhunal the Gray claims Ulliss was made by sealing **dragon souls in ice** and shaping that ice into human form.
- Status: supported as attributed participant testimony
- Epistemic mode: claimed creator's testimony
- Confidence: high for Jhunal's claim; lower as neutral objective narration
- Evidence:
  - `mods/continuities/vicn/unslaad/entities/characters/ulliss.md`
- Notes: Preserve attribution to Jhunal.

### unslaad.lizz.contains-player-dragon-soul
- Proposition: Jhunal says Lizz contains part of the player's dragon soul.
- Status: supported as attributed testimony
- Epistemic mode: participant/explanatory testimony
- Confidence: high for existence of the claim
- Evidence:
  - `mods/continuities/vicn/unslaad/entities/characters/ulliss.md`
  - related Lingering Snow / epilogue material
- Supports:
  - the authored family relation among player, Ulliss, and Lizz
- Notes: Social parentage is separately corroborated by epilogue dialogue.

### unslaad.dragonslayer.soul-scaling
- Proposition: The Dragonslayer armor family converts the player's current Dragon-Soul count into equipment bonuses, generally **1% per soul up to 50%** for armor/helmet/boots/ring.
- Status: supported
- Epistemic mode: direct ENCH/MGEF mechanics
- Confidence: very high
- Evidence:
  - `mods/continuities/vicn/unslaad/artifacts/dragonslayer-soul-scaling.md`

### unslaad.dragon-souls.recurring-substrate
- Proposition: In UNSLAAD, Dragon Souls recur as a material/resource substrate for **power, resurrection, constructed bodies, inheritance/lineage, and artifact scaling**.
- Status: synthesis supported
- Epistemic mode: synthesis from multiple independent direct mechanics/testimonies
- Confidence: very high for recurrence; metaphysical generalization beyond these systems is unsupported
- Evidence:
  - unslaad.ulliss.dragon-soul-conversion
  - unslaad.ulliss.revival-costs-dragon-soul
  - unslaad.ulliss.constructed-from-dragon-souls
  - unslaad.lizz.contains-player-dragon-soul
  - unslaad.dragonslayer.soul-scaling
- Qualifies:
  - any universal TES claim that all power/identity operates through Dragon-Soul assimilation.

## Relationships to materialize

- Ulliss -> converts -> Dragon Souls
- Dragon Soul -> resource for -> Ulliss revival
- Jhunal -> claims construction relation -> Ulliss
- Lizz -> claimed partial inheritance -> player's Dragon Soul
- Dragonslayer equipment -> scales with -> Dragon-Soul count
- Dragon Souls -> recurring UNSLAAD substrate -> power/body/revival/inheritance
