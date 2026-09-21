# Clockwork technical record layer

Continuity: `tes.mod.clockwork`  
Primary source: user-provided `Clockwork.esp`  
ESP SHA-256: `6850eb707a5b47f60fcec7bfb3494a4d7e909549c6c199cca81fc18780f73406`

This directory preserves record-structural evidence useful to Lorekeeper without confusing implementation data with character testimony.

## Contents

- `record-inventory.json` — ESP record-type counts plus core named records.
- `scene-index.md` / `scene-index.json` — all **22 SCEN records**, owning quests, and actor aliases.
- `core-vmad-wiring.json.gz` — story-relevant VMAD scripts/properties for quests, effects, scenes, and major NPC mechanics.
- `mechanics.md` / `mechanics.json` — narrative-relevant mechanics supported by plugin records, with interpretation cautions.
- `scene-role-resolution.json` — supplemental alias-level speaker resolution for the scripted Gilded introduction.

- `quest-vmad-story-state.md` / `.json` — quest-fragment state ownership, triggers, globals, enable parents, and cross-quest handoffs.

- `runtime-behavior.md` / `.json` — non-quest VMAD mechanics and state transitions for Shadow, Gilded, Amalgam, Recall, and bathing.

- `travel-machine-network.md` / `.json.gz` — exact Travel Room selector → enabled portal → Terminus/Recall cell graph, including Raven Rock gating.
- `pneumatic-network.md` / `.json.gz` — exact Pneumatic Tube Receptacle endpoints, room-to-room transfer/sort edges, and local sorting stations.

- `../events/runtime-causality.md` / `.json` — direct stage setters, object-driven quest transitions, scene-phase machinery, and runtime causality mapped onto the narrative graph.\n\n## Interpretation boundary

Implementation evidence can establish what the mod actually makes happen—for example, which scene alias speaks, which spell Shadow's management quest invokes, or which script starts Amalgam's retreat. It does **not** automatically establish an in-universe metaphysical law.

Examples:

- Gilded self-reanimation scripts support repeated downed/recovery behavior, but do not alone prove unlimited immortality.
- Shadow's slow-time spell corroborates Camilla's description of time standing still, but does not completely explain Shadow's nature.
- A SCEN actor alias can resolve a line to `Gilded01` without identifying one fixed NPC base form.

Query this layer together with `../dialogue/`, `../quests/`, `../books/`, and `../claim-seeds.json`.
