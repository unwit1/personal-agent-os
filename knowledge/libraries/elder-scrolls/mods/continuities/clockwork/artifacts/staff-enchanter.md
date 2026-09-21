# Staff Enchanter

Continuity: `tes.mod.clockwork`  
Object type: magical crafting station

After sufficient castle restoration, the player can ask Lahar to build a Staff Enchanter in the Mage's Study.

Lahar requests:
- 1 Heart Stone from Solstheim
- 3 empty Greater Soul Gems

After receiving the components, he says the station will be assembled toward the back of the Mage's Study and that he can arrange trades for blank staves.

## Runtime object wiring

The actual Staff Enchanter enable reference is `REFR 050299D9` / `CLWStaffEnchanterEP01REF`, placed in `CELL 050261BA` / **Clockwork Castle Mage's Study**.

Lahar's delivery INFO (`057A69D6`) is conditioned on stage 10 plus the required item counts. Its result fragment directly references the enchanter ref, `DLC2HeartStone`, `SoulGemGreater`, and `CLWLaharBlankStaffSpawn01`. The side quest's only later stage is terminal stage 100.

## Evidence

- `QUST 057A69D2`
- `INFO 057A69D4`
- `INFO 057A69D6`
- `REFR 050299D9`
