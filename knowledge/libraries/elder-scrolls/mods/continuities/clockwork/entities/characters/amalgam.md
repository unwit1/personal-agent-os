# Amalgam

Continuity: `tes.mod.clockwork`  
Entity type: degraded Gilded / self-modified machine-bound person  
Primary named NPC form: `05510DF1` (`CLWAmalgamCenturion01`)

## Continuity summary

Amalgam is an early Gilded who responded to deterioration by repeatedly modifying and enlarging his machine body. Lahar says Amalgam was the first of their brothers and sisters to lose himself in a distinctive way: he disappeared into unused portions of Nurndural, after which other Gilded vanished and were later found without their crystalline hearts.

Amalgam's own dialogue frames the heart-taking as an attempt at redundancy and survival. He says one heart was unsafe because if it broke he would be gone forever, but his enlarged body consumes or breaks hearts and drives him to seek more.

Lamashtu additionally says Amalgam discarded his original bones, and that his warped replacement body further warps an already damaged mind.

Before the player physically confronts him, Amalgam communicates remotely through speaker horns in the Sickness Ward. Those scene records do not have an NPC-form speaker: their scene actor is `SpeakerHorn01` from the dedicated `CLWDialogueAmalgam` quest. Lorekeeper therefore stores them as high-confidence diegetic Amalgam dialogue while keeping that distinction from strict NPC-form attribution.

## Evidence

- `INFO 0551B02C` (Lahar) — Amalgam's disappearance, missing Gilded, discarded shells without hearts, and the belief that Amalgam incorporated those hearts into a new body.
- `INFO 0556769D` / `0556768F` — Amalgam says one heart was too few and unsafe.
- `INFO 0556769E` / `05567690` — Amalgam says he needs hearts because his enlarged body causes them to break one after another.
- `INFO 05567699` — says some taken hearts do not work and cannot leave his body.
- `INFO 0568E3AF` (Lamashtu) — says Amalgam discarded his bones and that his altered body worsened his damaged mind.
- `SCEN 0553972F`, `0556C7BD` + `QUST 0552F492` — speaker-horn dialogue is routed through `CLWDialogueAmalgam` alias 0.
- `INFO 0559A4B6` + `SCEN 0559A4B3` — scene alias 3 resolves to the Amalgam ambush encounter base.

## Attribution note

Clockwork uses several Amalgam NPC/encounter forms sharing faction and voice data. Lorekeeper therefore distinguishes:
- strict unique primary-Amalgam INFO records: `../../dialogue/amalgam.md`
- eight-form pool dialogue: `../../dialogue/amalgam-form-pool.md`
- remote speaker-horn dialogue: `../../dialogue/amalgam-speaker-horn.md`

This preserves what is known without pretending every line came from the same physical NPC form.
