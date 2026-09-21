# Clockwork implementation outliers

Continuity: `tes.mod.clockwork`

This file records technical irregularities that should **not** be converted into lore.

## Morthal Terminus return-door follower threshold

Most inspected Terminus return doors use `DefaultNoFollowDoorScript` with:

- `myQuest = 0508DA63` / *I Against I*
- `myQuestStage = 200`

The Morthal return door, `REFR 050462B0` / `CLWDoorMorthalToCastleTravelRoom01REF`, instead uses:

- `myQuest = 0505F6C9` / *Foot Of The Mountain*
- `myQuestStage = 200`

The parsed *Foot Of The Mountain* stages are 0, 10, 20, 30, 40, and 255; there is no stage 200 entry.

### Interpretation

The script is `DefaultNoFollowDoorScript`, so this concerns follower-door handling rather than the core player Travel Machine destination selection. Lorekeeper therefore records it as an implementation outlier rather than asserting a different in-world rule for Morthal or a different Travel Machine unlock.
