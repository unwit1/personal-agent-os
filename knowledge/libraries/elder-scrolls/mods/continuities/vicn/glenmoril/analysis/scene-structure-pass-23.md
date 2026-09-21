# Scene structure pass 23

The raw ESM was walked recursively through GRUP containers and compressed records, then SCEN subrecords were enumerated.

## Confirmed

Late Act 2 is heavily scene-driven. The Oneiromancer cluster alone contains explicit scenes named for Arkved, Hela/Hera, Ja'cobee, Gerhard, Ja'zel, Brandt, a Hanged Man, a baby, chicks, gate opening and other narrative beats.

This is stronger than topic-name inference because these are actual SCEN record EDIDs.

## Parser observations

Common SCEN layout observed in GLENMORIL:
- header/phase condition material: `FNAM HNAM NAM0 NEXT CTDA ... WNAM`
- actor registrations: repeated `ALID LNAM DNAM`
- action blocks: `ANAM NAM0 ALID INAM ... SNAM ENAM ...`
- some actions also contain `PNAM`, `HTID`, timing and emotion data.

The next parser stage should interpret these fields by action type and extract DIAL FormIDs + Actor IDs. Existing Skyrim importer documentation confirms that the scene Dialogue action Actor ID corresponds to a reference alias in the associated quest, and INFO conditions remain applicable. citeturn0search0turn0search4

## Immediate narrative payoff

Scene EDIDs independently reinforce several relationships already suspected from dialogue:
- Arkved is directly scene-linked to the Oneiromancer sequence.
- Hela/Hera has her own Oneiromancer scene.
- Ja'cobee has a dedicated scene.
- Gerhard appears in a dedicated character scene.
- Ja'zel has multiple distinct scene beats.
- Brandt appears in multiple character/arrival scenes.

These links can now be treated as structural participation evidence, though not yet as proof of who speaks each INFO line.
