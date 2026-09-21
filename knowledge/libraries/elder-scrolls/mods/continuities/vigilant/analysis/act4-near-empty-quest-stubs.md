# Act 4 near-empty quest stubs

Continuity: `tes.mod.vigilant`

Primary structural source:
- `FLST 0251EABB` / `zzzCHAct4QuestStarterList`

This page records the five Act 4 side quests for which the current persisted VIGILANT corpus retains **starter-list membership but no quest-specific narrative body, resolved speaker, scene, alias dossier, or placement chain**.

The purpose is to make absence explicit and prevent future continuation passes from repeatedly treating these quests as undiscovered.

## More Skooma

- EditorID: `zzzCHSubQuest01`
- Title: **More Skooma**
- Structural status: member of the Act 4 starter list

No quest-specific character, scene, dialogue, location, or item relationship is currently preserved in the browsable VIGILANT corpus.

Do not infer a Khajiit, drug-trade, or Dro'Zel connection from the title alone.

Current classification: **known implemented Act 4 quest; narrative body missing.**

## Archer of Kyne

- EditorID: `zzzCHSubQuest02`
- Title: **Archer of Kyne**
- Structural status: member of the Act 4 starter list

No quest-specific actor, scene, dialogue, placement, or relationship to the later **Kyne's Dragon** quest is currently preserved.

The shared Kyne naming is not sufficient to merge the quests.

Current classification: **known implemented Act 4 quest; narrative body missing.**

## Knight of Julianos

- EditorID: `zzzCHSubQuest07`
- Title: **Knight of Julianos**
- Structural status: member of the Act 4 starter list

No dedicated knight identity, scene, or dialogue is currently retained.

Do not connect this quest to Jhunal merely because both involve knowledge/magic traditions; no such structural relationship is presently preserved.

Current classification: **known implemented Act 4 quest; narrative body missing.**

## Knight of Zenithar

- EditorID: `zzzCHSubQuest08`
- Title: **Knight of Zenithar**
- Structural status: member of the Act 4 starter list

No dedicated knight identity, dialogue, location, or trade/religious narrative is currently retained.

Current classification: **known implemented Act 4 quest; narrative body missing.**

## Knight of Kynareth

- EditorID: `zzzCHSubQuest12`
- Title: **Knight of Kynareth**
- Structural status: member of the Act 4 starter list

No dedicated knight identity, dialogue, scene, or relationship to **Archer of Kyne** or **Kyne's Dragon** is currently retained.

The Kyne/Kynareth naming cluster is worth revisiting after exact source recovery, but should remain unmerged now.

Current classification: **known implemented Act 4 quest; narrative body missing.**

## Negative-evidence rule

Repository-wide searches currently find the five quest EditorIDs only in the Act 4 orchestration record.

That means Lorekeeper can safely record:
- quest existence;
- quest title;
- Act 4 orchestration membership;

but should **not** fabricate:
- protagonists;
- antagonists;
- locations;
- outcomes;
- divine relationships;
- cross-quest identities.

## Recovery priority

When source bytes or a richer dialogue/quest extraction becomes available, recover for each quest:

1. QUST FormID and aliases;
2. objectives/stages;
3. SCEN ownership;
4. INFO/DIAL records conditioned on the quest;
5. NPC/reference bases;
6. cell/location placements;
7. VMAD properties and PEX fragment bodies;
8. items/books uniquely referenced by the quest.

## Current implication

With this file, **all fifteen Act 4 side quests now have at least an explicit Lorekeeper status**:

- some have substantial narrative reconstruction;
- some have structural dossiers;
- these five are explicitly marked as source-body gaps.

This is a coverage milestone, not a claim that the Act 4 lore ingestion is complete.
