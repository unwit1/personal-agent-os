# Gate Open scene

Source: `Glenmoril.esm:01724F` — `zzzGHMq05ScGateOpen`
Quest: `Glenmoril.esm:01719C` — Oneiromancer

Relevant aliases:
- 0 DweGear → NPC `04009DC7` → **FL-4N**
- 1 Romion → NPC `04008826`
- 2 Ozwald → NPC `040083AD`

The opening actions assign packages to all three actors. The subsequent dialogue actions resolve exactly:

| Action | Alias | Speaker | DIAL | INFO | Response |
|---|---:|---|---|---|---|
| 7 | 1 | Romion | 017253 | 017254 | Well then, FL-4N. Let's start. |
| 8 | 0 | FL-4N | 017255 | 017256 | You can count on me. I'm good at this! Snap! |
| 9 | 2 | Ozwald | 017257 | 017258 | All right, I'll go ahead. See you soon. |

The final package action sends Ozwald through `zzzGHMq05OzwaldWarpToQuagmire`.

## Lore consequences

This structurally confirms FL-4N's participation in the gate-opening procedure alongside Romion and Ozwald, and ties Ozwald's departure directly to a package explicitly named for warping to Quagmire.

Confidence: **exact structural speaker attribution**.
