# Staff Enchanting

Quest FormID: `057A69D2`  
Editor ID: `CLWSide02Quest`

## Quest stages

- `10` — active component-delivery state
- `100` — terminal/completed state

## Objective

- `10` — Deliver 1 Heart Stone and 3 empty Greater Soul Gems to Lahar to build a Staff Enchanter in Clockwork Castle

## Alias

- `0` **Lahar** → Lahar

## Runtime wiring

- `INFO 057A69D4` asks for **1 Heart Stone** and **3 Greater Soul Gems** and references this side quest from its result fragment.
- `INFO 057A69D6` requires quest stage 10 plus the required item counts.
- Its result fragment references `CLWStaffEnchanterEP01REF`, both component bases, and `CLWLaharBlankStaffSpawn01`.
- `REFR 050299D9` / `CLWStaffEnchanterEP01REF` is placed in the **Mage's Study**.

The ESP exposes the fragment wiring but not Papyrus source; exact internal fragment statements are therefore not fabricated.

See `../events/optional-quest-runtime.md`.
