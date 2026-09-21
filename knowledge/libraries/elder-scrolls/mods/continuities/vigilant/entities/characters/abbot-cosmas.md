# Abbot Cosmas

- Continuity: `tes.mod.vigilant`
- Primary NPC: `0210330D` / `zzzCHBossAbbot`
- Summon form: `02115EB8` / `zzzCHSummonAbbot`
- Main-quest alias: `zzzCHMQ00` alias 8, `Abbot`
- Boss quest: `024F57B8` / **VS Abbot**
- Placed boss reference: `02114871` in **Marukh's Underground Priory** (`CELL 02101AA1`)

## Official-lore substrate

VIGILANT's Abbot Cosmas is built around an obscure licensed Alessian figure. *The Cleansing of the Fane* records an **Abbot Cosmas** leading the Brothers of Marukh against the Ayleid temple Malada with holy fire and destroying relics and books.

VIGILANT reuses Cosmas, Malada, Marukhite institutions, and the Alessian religious setting as explorable Act 4 material. The licensed book supports the historical name and Malada campaign; VIGILANT's boss encounter and Coldharbour afterlife role are mod-specific.

## VIGILANT role

Cosmas is a bound actor in the main **Coldharbour** quest and is physically placed in **Marukh's Underground Priory**, directly on the route Pepe describes toward the Marukh/Stone material and Malada.

The current normalized INFO corpus does not give the boss form a unique body of attributed dialogue. Lorekeeper should therefore avoid inventing motives beyond the quest role and source-history association.

## Boss-state mechanics

`VS Abbot` uses `QF_zzzCHBossQuestAbbot_024F57B8`. Its boss alias deterministically:

- sets stage **5** on combat;
- sets stage **10** on death;
- sets stage **20** on cell detach after stage 10.

## Evidence anchors

- `NPC_ 0210330D` — VIGILANT boss form.
- `ACHR 02114871` — placement in Marukh's Underground Priory.
- `QUST 0212F24E` — main-quest Abbot alias.
- `QUST 024F57B8` — dedicated boss quest.
- Licensed comparison: *The Cleansing of the Fane*.
