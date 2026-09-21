# Amicus Tharn and the Petition trail

Continuity: `tes.mod.vigilant`

Primary source: user-provided `Vigilant.esm`

This pass reconstructs how the four *Petition to House Tharn* volumes are physically tied to **Amicus Tharn**.

## Documentary sequence

The four surviving volumes are:

1. `0251D5CB` — Vol. 11
2. `0251D5CC` — Vol. 23
3. `0251D5CD` — Vol. 68
4. `0251D5CE` — Vol. 77

All are by **Unknown** and contain Pelan/Amicus dialogue transcripts.

## Physical distribution

Three container records are named `zzzCHCorpseTharn01` through `03`.

All three:
- display as **Denounced One**;
- use the same model: `Clutter\VigCgt\statue\AmicusDead.nif`;
- contain exactly one Petition volume.

The progression is:

| Corpse | Location | Petition |
|---|---|---|
| `0251D67F` | First Inquisition Court | Vol. 11 |
| `0251D680` | Belharza's Hidden Charnel | Vol. 23 |
| `0251D681` | Belharza's Hidden Charnel | Vol. 68 |

The final volume changes presentation.

`NPC_ 0251D68A` / **Amicus Tharn** uses death list `0251D68C`, and that list contains **Vol. 77**.

So the ESM deliberately moves from **dead-image containers** to **the living/boss identity** for the final petition.

## Boss ownership

Amicus Tharn is not an incidental spawn.

`QUST 0251ADBF` / **Broken Horns** contains alias:

- `Boss` → `NPC_ 0251D68A` / Amicus Tharn

The placed actor:
- `ACHR 0251D68F`

is in:
- `CELL 0251C043` / **Belharza's Hidden Charnel**

This places Amicus inside the same Belharza-focused quest network in which his documentary ideology is especially relevant.

## Why Belharza matters

Vol. 11 establishes Amicus as an advocate for:
- denying Belharza's identity;
- fabricating a replacement Belharza;
- reshaping divine/historical identity through belief;
- killing witnesses whose memories preserve unwanted versions of the past.

Later, VIGILANT places Amicus Tharn as a boss in **Belharza's Hidden Charnel**.

That is strong thematic and structural closure: the ideologue who argued Belharza could be rewritten is physically embedded in Belharza's final quest-space.

## The four-volume ideological arc

### Vol. 11
**Memory and identity can be manufactured.**

### Vol. 23
**The world can be remade into a human-only heaven.**

### Vol. 68
**Prisoner freedom must be rejected because it threatens the Order's constructed world.**

### Vol. 77
**The doctrines themselves are no longer remembered, and the Stone has chosen Amicus and Pelan.**

The sequence therefore moves from political revisionism into explicit metaphysical instability.

## “Denounced One”

The corpse/container display name **Denounced One** is significant but ambiguous.

Possible readings include:
- Amicus has been condemned by a later faction;
- the corpses are memorial/statue-like reconstructions;
- Coldharbour is repeating different ideological stages as dead images;
- “denounced” refers to the recorded speaker rather than a literal corpse.

The ESM does not choose among these interpretations.

Because all three use `AmicusDead.nif` and `Tharn` EditorIDs, they can safely be linked to Amicus. Their ontology should remain unresolved.

## Boss equipment

`OTFT 0251D68B` / `zzzCHOutfitHrBattlemageAmicus` contains:
- Marukhati Selective Armor;
- Marukhati Selective Gauntlets;
- Marukhati Selective Mask;
- Marukhati Selective Hood.

Amicus also carries:
- `WEAP 025056E7` / **Heretic's Staff**

The ESM thus visually classifies the later Amicus as a Marukhati/Alessian combatant rather than merely preserving him as a scholar or court official.

## Current conclusion

The strongest reconstruction is:

**Amicus participates in the Pelan debates → his ideological record is preserved as four petitions → three AmicusDead “Denounced One” representations carry the first three volumes → the final Belharza complex contains Amicus Tharn himself → defeating him yields Vol. 77.**

This makes Amicus one of VIGILANT's clearest examples of a documentary character becoming an environmental and combat identity.

## Open questions

Still unresolved:
- the precise chronology between the petitions and Broken Horns;
- why the title/name **Tharn** attaches to Amicus;
- whether the corpse images represent actual bodies;
- whether Amicus's final manifestation is historical survival, Coldharbour reconstruction, or Stone/memory persistence;
- whether external Papyrus supplies additional explanation.
