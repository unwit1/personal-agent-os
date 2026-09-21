# Scene action implementation pass 25

The scene-action resolver is now specified tightly enough to produce deterministic rows without prose inference.

## Confirmed joins

For a scene dialogue topic, the scene action's Actor ID is the reference-alias ID in the associated quest. The alias may resolve to one NPC/reference or to a constrained set. INFO conditions are still evaluated after that actor is chosen. This behavior is independently documented by an existing Skyrim dialogue importer.

## Export algorithm

For each priority SCEN:
1. retain source encounter order and parse its action blocks;
2. select dialogue actions;
3. emit action index, Actor ID and linked DIAL;
4. join Actor ID to the QUST alias table;
5. resolve forced aliases immediately;
6. join DIAL to the existing child INFO map;
7. retain every INFO response, RNAM prompt, PNAM predecessor and CTDA condition;
8. evaluate speaker-relevant CTDA functions;
9. mark the row exact, constrained, ambiguous or unresolved.

## INFO preservation

Recent xEdit tooling exports INFO conditions and RNAM prompts alongside dialogue text, validating those as first-class corpus fields. xEdit also documents that INFO order affects engine response selection, so source/effective ordering must be retained.

## No text-based speaker guessing

Character names in EDIDs remain useful for discovery and auditing, but cannot substitute for the structural Actor ID → alias join.
