# The Wheels of Lull

Sub-continuity for the Skyrim mod **The Wheels of Lull**.

- Continuity ID: `tes.mod.wheels-of-lull`
- Primary source: user-provided `WheelsOfLull.esp`
- ESP SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`

## Structured lore-source ingestion: complete

- BOOK **33/33**
- QUST **32/32**
- DIAL **337/337**
- INFO **410/410**
- NPC_ **75/75**
- LCTN **33/33**
- CELL **103/103**
- MESG **53/53**
- SCEN **14/14**
- **1,090 structured lore-bearing source records** persisted.

The final batch completes the plugin messages and scenes. Messages preserve exact user-facing description/button text where present. Scenes preserve owning quest, subrecord order, and deterministic references to dialogue/quest/NPC records where those FormIDs resolve.

Notable final records include Technomancy knowledge, monitoring/tram state messages, Wailway interaction messages, and scenes for Archeron introductions, Numinar's speech, the traitor confrontation, Llavados explanations, Wailway ending, Fyr's saboteur sequence, and the Numinar approach.

## Provenance

All material remains scoped to `tes.mod.wheels-of-lull`. Character testimony, quest narration, message/UI text, scene structure, and implementation evidence remain distinct evidence classes.

## Post-ingestion analysis

The raw/structured source import is complete. Downstream work can now use the full preserved corpus for deterministic speaker-condition resolution, character/location/artifact/faction dossiers, cross-source claim extraction, contradiction handling, and retrieval indexes without reparsing the ESP.
