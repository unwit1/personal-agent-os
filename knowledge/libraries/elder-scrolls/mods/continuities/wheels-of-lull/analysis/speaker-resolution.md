# Dialogue speaker and condition resolution

Continuity: `tes.mod.wheels-of-lull`  
Source: `WheelsOfLull.esp`  
SHA-256: `230b102cd1ec13f2d104da8803d32c19227ef519eaca766a00b076c322aa78bb`

## Coverage

All **410 INFO** records were decoded for CTDA conditions and cross-linked to their owning DIAL topic and quest.

Resolution results:

- **exact_semantic_custom_voice**: 229
- **exact_form_or_scene**: 61
- **shared_custom_voice_candidates**: 57
- **role_level_custom_voice**: 34
- **contextual_wailway_train_not_condition_proven**: 19
- **exact_talking_activator_voice**: 6
- **unresolved**: 4

The resolver is deliberately conservative. Shared custom voice types remain candidate sets unless a direct `GetIsID`, `GetIsAliasRef`, or SCEN action alias supplies a stronger binding. The Wailway locomotive is stored as a separate high-confidence contextual attribution because most of its INFO records do not carry a speaker condition.

## Deterministic evidence layers

1. `GetIsID` condition -> concrete speaker/object form.
2. `GetIsAliasRef` condition -> quest alias -> forced/unique reference.
3. SCEN dialogue action -> actor alias -> forced/unique reference.
4. Character-specific custom voice type -> semantic persona when the voice class is continuity-specific.
5. Shared custom voice type -> explicit candidate set, not a forced speaker.

## Important ambiguity cases

- Archeron and the apparent Divayth Fyr share the `_lull_archeron` voice class. Scene aliases resolve some lines exactly; other lines retain both candidates unless the implementation provides stronger evidence.
- The `_lull_intelligences` voice class is shared by Watchman-215, the Cartwright, and the Analyst.
- The underwater voice class is shared by Decade Belarus and Second Atlantan.
- The `_lull_masscroft` voice class is reused by Masscroft, Yagrum Bagarn, and several Thalmor Experiment actor forms; generic voice-only attribution is therefore not collapsed to one individual.
- Female guard/mining-guard and FRF voice classes are also shared.
- The Skull is a talking activator, not an NPC record, and is resolved through its custom voice/TACT implementation.
- One vanilla courier INFO override depends on an external base-game quest alias and remains unresolved locally.

## Files

- `speaker-resolution-compact.jsonl.gz` — one compact row per INFO with decoded conditions and conservative speaker resolution.
- `condition-function-map.json` — function/operator/run-on map used by this pass.
- `speaker-index.json.gz` — reverse index from resolved speaker/persona to INFO and topic FormIDs.

These files are derived analysis; the original raw source shards remain authoritative.
