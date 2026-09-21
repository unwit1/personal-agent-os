# Internal / technical QUST records

These five QUST records are present in `Clockwork.esp` but are not ordinary player-facing journal quests. They are cataloged separately so all **12/12 QUST records** are browseable without mixing implementation/state records into the story sequence.

| FormID | EditorID | Name | Player journal text |
|---|---|---|---|
| `0552F492` | `CLWDialogueAmalgam` | Amalgam Dialogue | none |
| `0524471E` | `CLWDialogueGilded` | Gilded Dialogue | none |
| `0506FCE4` | `CLWShadowManage01Quest` | CLW Shadow Manage01 Quest | stage numbers only; no journal text |
| `05543959` | `CLWMCM01Quest` | CLW MCM01 Quest | none |
| `0502AB87` | `CLWMiscTracking01Quest` | CLW Misc Tracking 01 Quest | none |

## Interpretation policy

- `CLWDialogueAmalgam` and `CLWDialogueGilded` are dialogue-host quests. Their role is directly supported by the DIAL/INFO and scene records attached to them.
- `CLWShadowManage01Quest` exposes stages 10, 20, 30, 40, 50, and 60 but no player-facing journal strings in the raw QUST extraction. The name strongly suggests runtime Shadow state management, but exact stage semantics are not invented without Papyrus/scene-condition evidence.
- `CLWMCM01Quest` is retained as an MCM/configuration technical quest by editor ID; no player-facing journal content is present.
- `CLWMiscTracking01Quest` is retained as a miscellaneous tracking/state quest by editor ID; no player-facing journal content is present.

Source: `../../raw/quest-records.txt.gz`.
