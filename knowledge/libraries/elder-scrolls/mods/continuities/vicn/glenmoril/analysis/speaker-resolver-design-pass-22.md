# Speaker resolver design pass 22

External format validation now supplies the missing deterministic model for Skyrim scene dialogue.

A Skyrim dialogue-import implementation documents the chain:

**SCEN → dialogue action Actor ID → quest alias → alias fill mechanism → NPC/reference**, while INFO conditions continue to filter which line is eligible.

This aligns with the QUST alias map already extracted from GLENMORIL. xEdit's QUST documentation independently confirms ALST as reference-alias IDs and ALID as alias names.

## Consequence for GLENMORIL

Late-Act-2 scene lines can be resolved without guessing from prose:

1. identify DIAL used by a SCEN dialogue action;
2. read that action's Actor ID;
3. match Actor ID to the associated QUST alias;
4. resolve the alias through forced reference / unique actor / external alias / conditions;
5. apply INFO conditions as a final constraint.

## Condition paths

A Skyrim dialogue importer explicitly uses `GetIsID`, `GetInFaction`, `GetIsAliasRef`, and voice-type constraints when resolving speakers. This gives us a concrete CTDA decoding target rather than treating all condition functions generically.

## Conservative rule

Where an alias is condition-filled rather than forced to one actor, the result must remain a candidate set unless conditions uniquely resolve it.

Sources:
- Serifu Skyrim importer documentation: scene Actor ID ↔ quest alias and condition-based speaker resolution.
- xEdit QUST documentation: ALST/ALLS alias structure and fill types.
