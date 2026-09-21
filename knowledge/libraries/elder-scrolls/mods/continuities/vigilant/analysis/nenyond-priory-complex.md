# Nenyond's Priory and the disappearance complex

Continuity: `tes.mod.vigilant`

Primary historical source: `BOOK 020CB0DF` / *The Eight Saints of Cyrod*

This page separates the **historical disappearance story** from the **Coldharbour environment that VIGILANT actually implements**.

## Historical sequence in The Eight Saints of Cyrod

The saint text gives a compact three-person sequence:

1. **Nenyond**, an eastern Cyrodiilic lord and comparatively moderate Marukhati Selective, spends his fortune building an underground priory.
2. During construction, ruins said to date to the **Dawn Era** are discovered.
3. **Nenyond and Manthar** enter/explore the ruins and disappear.
4. **Silorn** later enters in search of them.
5. Only Silorn's skin returns.
6. The priory and excavated ruins are sealed.
7. After Nenyond's disappearance, **Varla** succeeds to the eastern lordship on Belharza's recommendation.

Only the text itself establishes that the excavated ruins were truly from the Dawn Era. The cell names and traversal graph do not independently date them.

## Implemented site

The ESM contains:

- `CELL 0210EBFD` — **Nenyond's Underground Priory**
- `CELL 021114AF` — **Funeral Temple**
- `KEYM 0212D026` — **Nenyond's Key**

The Coldharbour door graph gives a direct configured traversal pair:

**Nenyond's Underground Priory** ↔ **Funeral Temple**

Nenyond's Underground Priory also connects to the main Coldharbour exterior hub.

This is strong implementation evidence that VIGILANT treats Nenyond's foundation as a distinct explorable historical site inside Act 4's reconstructed/absorbed Coldharbour landscape.

It does **not** prove that the Coldharbour version is a perfectly preserved First Era building.

## The Funeral Temple as aftermath

The most important structural finding is that the **people who followed Nenyond into the ruins reappear in the connected Funeral Temple, while Nenyond himself does not**.

### Manthar

- `NPC_ 021146D9` — **Sorcerer Manthar**
- `ACHR 021146DA` — placed in **Funeral Temple**
- summon form: `NPC_ 0213B503`
- associated conjuration: `MGEF 0213B504`

The saint text says Manthar vanished together with Nenyond while investigating the uncovered ruins.

His later boss placement directly behind/alongside Nenyond's priory strongly preserves that disappearance relationship spatially, even though the mechanism that turned him into the Bone Lord manifestation remains unexplained.

### Silorn

- `NPC_ 02114115` — **Abbot Silorn**
- `ACHR 0243A499` — placed in **Funeral Temple**
- `ALCH 020E2593` — **Hide of Abbot Silorn**
- `CELL 02239B51` — **Silorn's Priory**

The saint text says Silorn entered the ruins looking for Nenyond and Manthar and that only his skin returned.

VIGILANT literalizes the returned-skin motif as the **Hide of Abbot Silorn** while also placing an Abbot Silorn actor in the same Funeral Temple complex as Manthar.

## Nenyond's absence

No Nenyond NPC base form has been identified in the current 1,233-NPC inventory.

No speaking INFO record, journal, summon, Stone fragment, or boss identity currently supplies a later Nenyond manifestation.

That absence matters because VIGILANT handles Manthar and Silorn differently:

- **Manthar** becomes an encounter/summon identity.
- **Silorn** becomes an actor plus relic/hide identity.
- **Nenyond** remains represented by his **name, priory, key, historical relationships, and disappearance**.

Current interpretation: **Nenyond functions as the missing center of the complex**. The environment preserves the consequences of his expedition without resolving what happened to him.

## What the structure supports

### Strong structural facts

- Nenyond's Underground Priory exists as an explorable cell.
- It directly connects to Funeral Temple.
- Manthar is physically placed in Funeral Temple.
- Silorn is physically placed in Funeral Temple.
- VIGILANT contains Nenyond's Key.
- Nenyond has no identified NPC continuation in the current inventory.

### Historical claims from the saint text

- Nenyond was a moderate Selective.
- he financed the priory with his fortune.
- the buried ruins were from the Dawn Era.
- he disappeared while exploring them with Manthar.
- Silorn later searched for them.
- Varla succeeded him on Belharza's recommendation.

Those remain attributed to *The Eight Saints of Cyrod* unless supported by an independent source.

## Open questions

- What exactly lies beneath/behind the priory in quest-state terms?
- Does `Nenyond's Key` open a specific shortcut or sealed door in the complex?
- Are enable/disable states used to make the Funeral Temple represent a deeper historical layer?
- Is Nenyond intentionally absent, or does an unresolved generic/reference alias represent him?
- Do external Papyrus scripts explain the transformation of Manthar or the return of Silorn's skin?

Answering those requires either deeper raw-reference/lock analysis or the VIGILANT script/BSA layer.

## Interpretation

The strongest current reading is not “the player finds Nenyond's tomb.”

Instead, VIGILANT builds a **disappearance complex**:

**Nenyond's project → buried ruins → Nenyond + Manthar vanish → Silorn follows → sealing → Coldharbour preserves Manthar/Silorn aftermath while Nenyond remains missing.**

That preserves the saint text's central mystery rather than resolving it.
