# Varla the Man-Hunter

- Continuity: `tes.mod.vigilant`
- Primary boss: `020E6A48` / `zzzCHBossVarla`
- Summon form: `021B9236` / `zzzCHSummonVarla`
- Boss quest: `024F69C2` / **VS Varla**
- Memory quest link: `0213965A` / **Knight of Hounds**
- Placed boss reference: `020E6A49` in **Varla's Hall** (`CELL 020E63D8`)

## Knight of Hounds memory

In the memory sequence, Emperor Belharza addresses Varla as an Ayleid orphan whom he personally raised to knighthood and treats as a son despite no blood relationship. Belharza orders Varla to participate in the indiscriminate killing of Ayleids, including women and children. Varla's refusal/compassion creates the break between them.

Because this is a VIGILANT memory quest, Belharza's account remains memory testimony rather than objective First Era history.

## Later Man-Hunter

Coldharbour dialogue presents a later Varla who rules eastern territory from Fort Welkynd/Varla's Hall and threatens trespassers with his hounds.

Sir Henrik says Varla once ruled an eastern part of the Alessian Empire and was killed after his subjects revolted against his brutality. See `entities/characters/sir-henrik.md`. Giant Knight Ritho remembers Varla as a courageous and honorable friend who later changed under fear, began hunting his own people, and acquired the title **Man-Hunter**. After Varla's defeat, Ritho says Varla is finally free.

These are independent character testimonies inside VIGILANT and should remain attributed rather than synthesized into an omniscient biography where they disagree.

## Boss mechanics

The `VS Varla` quest explicitly links back to *Knight of Hounds* through its `MemQ` VMAD property. Its boss alias:

- advances to stage **5** on combat;
- advances to stage **10** on death;
- advances to stage **20** after the cell detaches following the kill.

The boss quest also owns a Varla-specific music type and a door reference.

## Evidence anchors

- `INFO 020E6A4E`–`020E6A54` — Varla's own Coldharbour dialogue.
- `INFO 02139664`–`02139673` — Belharza addressing Varla in *Knight of Hounds*.
- `INFO 02157AAB` — Sir Henrik's account.
- `INFO 02167055`, `0216705B` — Ritho's account and reaction to Varla's release.
- `QUST 024F69C2` — boss-state link to Memory Quest 03.
- `ACHR 020E6A49` — Varla's Hall placement.


## Supplementary parentage layer

The a123999 VIGILANT background article identifies **Mary** as Varla's biological mother and **Umaril** as his biological father.

This fits two separate ESM-backed structures:
- *Knight of Hounds* presents Varla as an **Ayleid orphan** raised by Belharza with no blood relationship;
- *Pelinal the Bloody* separately places Mary in an Umaril/pregnant-captive memory context.

The currently persisted ESM corpus does **not** contain a direct line stating the parentage.

Therefore Lorekeeper should preserve:

- **ESM:** Varla is an Ayleid orphan/foster son of Belharza.
- **supplementary:** Mary + Umaril are Varla's biological parents.

Detailed reconstruction:
- `analysis/varla-mary-umaril-parentage.md`

The same supplementary source says learning his true birth contributed to Varla's later collapse into the Man-Hunter identity. Ritho and Henrik independently confirm the later moral/political collapse, but not its parentage cause.
