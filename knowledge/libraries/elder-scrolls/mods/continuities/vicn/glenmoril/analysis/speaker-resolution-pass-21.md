# Speaker-resolution pass 21

The raw ESM was reparsed to retain dialogue-relevant subrecords rather than only the earlier inventory fields.

## Deterministic progress

QUST alias structures were successfully extracted using ALST/ALLS + ALID and forced-reference fields. This gives actor/reference maps for the major late-Act-2 quests.

Important confirmations:
- Oneiromancer directly aliases Romion, Ozwald, Ja'zel and Hela/Hera.
- Broken Egg directly aliases Lalanoah, Brandt, Skoll, Jhunal and Ulrik/Boss01.
- The Last Chick Trader directly aliases Ja'cobee and Ulliss.
- Louse directly aliases Yelem and Boltzmer.
- Or the Gospel directly aliases Lalanoah, Brandt, Ozwald, Romion, Cedric, Ja'zel, Witch and Hircine.

## INFO resolution method

Skyrim dialogue speaker attribution cannot safely be inferred from response text alone. The next resolver should combine:
1. INFO conditions;
2. quest alias IDs/forced references;
3. SCEN actor registrations and dialogue actions;
4. explicit speaker fields when present;
5. NPC/ACHR base/reference mapping.

INFO conditions are being retained as raw CTDA bytes until their function/parameter layout is decoded. This is intentionally conservative: assigning speakers from guessed CTDA offsets would corrupt the dialogue corpus.

## Source-format validation

xEdit documentation confirms QUST reference aliases are introduced by ALST, named by ALID, and may be filled by reference/condition mechanisms. Scene tooling likewise treats actor registrations and linked dialogue as part of SCEN structure. citeturn0search2turn0search0
