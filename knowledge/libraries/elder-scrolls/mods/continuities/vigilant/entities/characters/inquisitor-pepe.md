# Inquisitor Pepe

- Continuity: `tes.mod.vigilant`
- Primary form: `NPC_ 02081E46` / `zzzCHInquisitorPepe`
- Related forms: `0212BF48` / `zzzCHInquisitorPepeMemory`; `021363DC` / `zzzCHInquisitorPepeGhost`; `0211CCC3` and `0211CCC4` additional ghost forms
- High-confidence primary dialogue coverage: 55 INFO records
- Role: principal guide/historical narrator in the opening Coldharbour main quest

## Guide role

Pepe meets the player after they awaken from a sarcophagus in Coldharbour. He identifies Mathmalatu Priory, describes major regions and threats, and provides the practical route toward the Imperial City, Malada, Marukh, Dro'Zel, and ultimately the Tower.

He is therefore not merely an exposition NPC: his dialogue supplies the main navigational framework for the first Coldharbour main quest.

## Historical testimony

Pepe speaks as someone personally implicated in Alessian history. He claims to remember the waterfront during plague-era events, burning Mary, killing a Sload, serving the Eight Divines, finding Marukh in the Colovian jungle, witnessing Marukh dance with an apparition of Alessia, and hearing the command to make the Stone into a Tower.

He later condemns the Alessian Order and says its rulers became enslavers. He describes Marukhati hostility to elves/Anui-El, the Stone's loss during the War of Righteousness, and the coming Greymarch.

These lines are invaluable for VIGILANT's internal cosmology but remain Pepe's testimony.

## Pelan identity and bodily transformation

VIGILANT explicitly connects Pepe to **Pelan**:

- `INFO 02234DC6` — Giant Knight Ritho refers to Pepe as **bishop Pelan**.
- `INFO 02244BD6` — Arasil says Pepe had been a kind-hearted priest of the Eight Divines until he returned from the jungles of Colovia.
- Pepe himself says he met Marukh in the Colovian jungle and had still served the Eight Divines when he went there.

The memory sequence provides a physical chronology:

- *The Grand Inquisitor* — `NPC_ 0212BF48`, ordinary humanoid form.
- *Adabal* — `NPC_ 0205ADFD`, still ordinary humanoid.
- *Remains of the Miracle* — `NPC_ 0206A230`, now the custom **Alessian Sleeper Race**/Pepe body.

In `INFO 0206B54F`, the transformed Pepe confirms his identity and says he has changed considerably.

The same Memory 6 conversation says he held the Stone too long, is now an empty shell without a soul, and describes himself as a monster.

This is strong testimony that prolonged possession of the Stone is connected to his degraded state, although the ESM does not prove that it is the sole cause.

Present-day Pepe's race/body implementation is explicitly nonstandard:
- `RACE 020818A6` / **Alessian Sleeper Race**
- Hagraven skeleton/animation project
- bespoke `Pepe.nif` body through `zzzCHSkinPepe`

Detailed reconstruction:

`analysis/pelan-pepe-transformation.md`

## Change in Aetherius

Pepe's ghost forms become less sarcastic and more explicitly cautionary. They urge the player to stop, describe the Stone as a key to the soul that awakens the Oblivion inside, express remorse connected with Alessia, and warn about Molag Bal using powerful corpses as vessels.

This gives Pepe an arc from cynical guide who pushes the player onward to a ghostly warning voice attempting to halt the final progression.

## Evidence anchors

- `INFO 0212F252` onward — awakening and guide dialogue in *Coldharbour*
- `INFO 0212F264`–`0212F278` — priory/wasteland/Molag Bal orientation
- `INFO 0212F839`–`0212F83D` — Greymarch/Jyggalag account
- `INFO 0212F85E`–`021303D9` — Pepe's self-implicated Alessian/Marukh history
- `INFO 021303F7`–`0213040E` — Tower route and Greymarch transition
- `INFO 021369AD`, `021369AF`, `0211CCD0`–`0211CCDD` — ghost warnings in *Aetherius*

## Reliability note

Pepe is simultaneously guide, participant, confessor, cynic, and unreliable historical witness. His testimony should remain claim-level evidence rather than a neutral chronology.
