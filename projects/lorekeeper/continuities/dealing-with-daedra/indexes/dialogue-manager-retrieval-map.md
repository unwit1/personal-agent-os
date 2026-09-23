# Dialogue-manager retrieval map

Dealing with Daedra stores most narrative dialogue inside a small number of large QUST containers. Use this map before searching the full 1,809 INFO corpus.

| QUST | Editor ID | INFO | responses | Main lore domains / leading resolved speakers |
|---|---|---:|---:|---|
| 05380CA3 | dealsdialogues | 205 | 251 | Sadren Sarethi/Wispmothers; School of Julianos/Knights Mentor; early flesh-magic and institutional dialogue |
| 0550C6B0 | dealsdialogues2 | 126 | 243 | vampire/curse and page-collection arc; Gatekeepers; Skaafin/Clavicus Vile; Mr. Aedwatch; Eraamion/Mysticism |
| 0555DC0D | dealsdialogues3 | 253 | 381 | Cult of the Return/The Herald; Vigilant Toruld; Gatekeeper/Vigilant conflict; smugglers and related occult contacts |
| 055F0DB3 | dealsdialogues4 | 321 | 536 | Exile Witch/Doom-Truth contract; Dagon cell; courier/logistics; Rift Bank; Quinergus; Skegor; trafficking/criminal branches |
| 05632C14 | dealsdialogues5 | 248 | 293 | Grados/Mageblight/Thalmor theories; Darklings/Nocturnal; Deyanira; smuggler/Syndicate links; Widow crossover |
| 05651407 | dealsdialogues6 | 228 | 334 | Lysara/Widows of Mephala; Carsten/Syndicate; Operative Green; broader criminal and cult service networks |
| 056C18D8 | dealsdialogues7 | 347 | 552 | Thaer/Family/flesh magic; Beldam Annes/North-Jerall; Brethren/Deep Ones; Ratway survival/criminal microeconomy |
| 05787B55 | dealshirelingmanager | 79 | 82 | Talmeth Dres hireling dialogue, House Dres worldview, witchhunter practice |

## Retrieval guidance

For named-character lore, start with entities/characters and the deterministic speaker transcripts where available.

For a faction or metaphysical topic, start with topics/ and claims/ before opening a dialogue manager.

Use raw INFO records only when:
- the speaker is unresolved;
- condition/branch context matters;
- the semantic dossier cites an INFO that needs verification;
- alias or scene-driven dialogue requires further attribution.

## Why the map matters

The plugin reports only 19 QUST records, but seven dialogue-manager quests contain 1,728 of the 1,809 INFO records. Treating QUST count as story count therefore badly understates the mod's narrative structure.
