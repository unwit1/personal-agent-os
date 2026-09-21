# Scene dialogue resolution notes

The scene resolver should not search dialogue text for character names.

For scene dialogue, the deterministic route is structural:

`SCEN action → DIAL → Actor ID → QUST alias → filled reference/NPC`

The INFO selected under that DIAL can still have conditions, so actor resolution and INFO eligibility are separate steps.

This is particularly useful for GLENMORIL because the late-Act-2 QUST aliases for Romion, Ozwald, Ja'zel, Hela, Lalanoah, Brandt, Jhunal, Ulrik, Ja'cobee, Ulliss, Yelem and Boltzmer are already extracted.

When a SCEN Actor ID matches one of those forced aliases, speaker attribution can be marked **exact** once the corresponding DIAL/action mapping is parsed.
