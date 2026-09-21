# Bathing and hygiene

Continuity: `tes.mod.clockwork`  
Topic type: domestic technology / gameplay corroboration

The Master Bedroom bathing room has working hot/cold water controls:

- `ACTI 0501A0C2` — Shower
- `ACTI 0501AB9F` — Cold Water
- `ACTI 0501ABA0` — Hot Water
- `FURN 050195E4` — Bathtub

During the bedroom tour, Lahar says washing the mortal body **aids social interaction and fortifies against disease**.

The plugin turns that statement into a temporary gameplay effect:

- `SPEL 0502181E` — **Clean from Bathing**
- associated effects include **Fortify Barter** and **Resist Disease**
- spell description: “Prices are 5% better. 10% resistant to disease.”

This is a clean case where gameplay mechanics deliberately literalize Lahar's dialogue rather than merely supplying an unrelated convenience.

## Evidence

- Bedroom-tour INFO `052FB0D6`
- `SPEL 0502181E`
- `MGEF 0502181D` / Fortify Barter
- `MGEF 0502181B` / Resist Disease
