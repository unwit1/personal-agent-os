# Amicus Tharn and House Tharn

Continuity: `tes.mod.vigilant`

This pass asks whether VIGILANT establishes **Amicus Tharn** as a literal genealogical member of the historically attested House Tharn, or merely associates him with the name and ideological tradition.

## What the ESM says directly

The plugin uses the Tharn name in three separate ways around Amicus:

1. the boss is explicitly named **Amicus Tharn**;
2. the boss/death/corpse EditorIDs repeatedly use `Tharn`:
   - `zzzCHBossAmicusTharn`
   - `zzzCHDeathItemAmicusTharn`
   - `zzzCHCorpseTharn01`
   - `zzzCHCorpseTharn02`
   - `zzzCHCorpseTharn03`
3. the four documentary books are titled **Petition to House Tharn**.

This is enough to classify Amicus as **intentionally associated with House Tharn** inside VIGILANT.

## No genealogy in the plugin

A full-string/name pass across `Vigilant.esm` finds no explicit:
- parent;
- child;
- sibling;
- ancestor;
- descendant;
- marriage;
- family-tree statement

linking Amicus to another named Tharn.

The ESM also does not state that Amicus is:
- a direct ancestor of Abnur Tharn;
- a descendant of Fervidius Tharn;
- a sibling/child of Fervidius;
- the founder of House Tharn.

Therefore Lorekeeper should **not invent a family relationship** beyond the surname/House association.

## Fervidius Tharn is deliberately present in the same mod

VIGILANT also embeds books attributed to **Fervidius Tharn**, Arch-Prelate of the Marukhati Selective.

Two notable examples in the plugin are:

- `BOOK 02054ED3` — **On the Detachment of the Sheath from the Integument**
- `BOOK 024A8AF7` — **Vindication for the Dragon Break**

The raw ESM strings explicitly identify Fervidius Tharn as author/Arch-Prelate.

Their VIGILANT placements include Alessian/Coldharbour religious and inquisition spaces such as:
- Narfin's Inquisition Court;
- Mathmalatu Priory;
- Baptist's House;
- other Act 4 interiors.

This means VIGILANT does not introduce the surname **Tharn** in a vacuum. It places Amicus's Tharn identity inside a setting already foregrounding Fervidius Tharn's Marukhati writings.

## Base-canon context

Licensed Elder Scrolls material already establishes **Fervidius Tharn** as a First Era member of the Tharn family and a major Alessian/Marukhati figure.

It also presents House Tharn as an old Nibenese family with traditions stretching back into Alessian-era history.

That makes VIGILANT's use of **Amicus Tharn** in a First Era Alessian/Marukhati context historically compatible as a mod-continuity insertion.

However, licensed material does **not** establish an Amicus Tharn matching this VIGILANT character.

Therefore:

- **House Tharn as an ancient Alessian-era family:** compatible with licensed lore.
- **Fervidius Tharn as a Marukhati/Alessian figure:** licensed lore.
- **Amicus Tharn as a specific First Era family member:** VIGILANT-specific.
- **exact kinship between Amicus and Fervidius/later Tharns:** unresolved.

## Additional VIGILANT Tharns

The raw ESM also contains three named Tharns in the **Feral Soul-Shriven** system:

- **Radokhan Tharn** — Holy Brothers of Marukh Priory
- **Ortutay Tharn** — Marukh's Underground Priory
- **Marosi Tharn** — Malada Aldmerisel

All three are implemented as generic Soul-Shriven variants with Alessian/Marukhati gear and no unique dialogue or genealogy.

Detailed analysis:

`analysis/feral-soul-shriven-tharns.md`

Their presence strengthens the interpretation that VIGILANT deliberately populates its Alessian/Marukhati historical layer with members or representatives of the **Tharn** tradition.

It does **not** establish direct kinship between:
- the trio and Amicus;
- the trio and Fervidius;
- any of them and later named Tharns.

Amicus should remain a separate high-depth character dossier rather than being flattened into this radiant trio.

## Petition title: addressed to House Tharn, not proof of authorship

The books are titled **Petition to House Tharn**, and each lists the author as **Unknown**.

The contents are Pelan/Amicus dialogue transcripts.

The title therefore most naturally indicates that the records are being presented **to House Tharn** or preserved under that heading. It does not by itself prove:
- Amicus authored the petitions;
- Amicus is the recipient;
- Amicus is the head of House Tharn.

Amicus's own surname provides the direct House association.

## Possible relationship to Fervidius

Because:
- Amicus is a Tharn;
- he is active in Alessian/Marukhati ideological debates;
- VIGILANT foregrounds Fervidius Tharn's Marukhati writings;
- the petitions themselves are explicitly filed as communications to House Tharn;

the mod appears to be **deliberately placing Amicus inside the same historical Tharn/Marukhati tradition**.

But no direct line says:

**Amicus → Fervidius**

or:

**Fervidius → Amicus**.

Current classification: **strong dynastic/thematic association; no recoverable genealogy**.

## Chronology caution

Amicus's petition debates concern:
- Belharza;
- early Alessian identity formation;
- the Order's racial policies;
- Prisoner figures;
- instability of the Seventy-Seven Doctrines.

Fervidius Tharn's licensed historical prominence is much later in the First Era, near the Middle Dawn.

VIGILANT's memory/Coldharbour structure is not a reliable simple linear timeline, and the plugin does not explicitly date Amicus.

Therefore Amicus should not automatically be positioned as Fervidius's father, son, contemporary, or predecessor based solely on theme.

## Lorekeeper relation model

Recommended relations:

- `Amicus Tharn --associated_with--> House Tharn` — **high confidence**
- `Amicus Tharn --associated_with--> Alessian Order / Marukhati ideology` — **high confidence**
- `Amicus Tharn --thematically_linked_to--> Fervidius Tharn` — **medium/high confidence**
- `Amicus Tharn --kin_of--> Fervidius Tharn` — **unresolved; do not assert**
- `Amicus Tharn --ancestor_of--> Abnur/Jagar/Clivia Tharn` — **unsupported**

## Conclusion

The strongest evidence supports reading **Amicus Tharn** as a VIGILANT-specific member or representative of **House Tharn**, inserted into a historically compatible Alessian/Marukhati family tradition.

VIGILANT deliberately reinforces that association by preserving Fervidius Tharn's Marukhati texts in the same continuity.

What it does **not** provide is a family tree.
