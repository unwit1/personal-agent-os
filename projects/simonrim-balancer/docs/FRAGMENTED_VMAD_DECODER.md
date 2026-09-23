# PERK / QUST Fragmented VMAD Decoder

## Scope

The supplied Simonrim snapshot contains six `PERK` records and seven `QUST` records with record-specific VMAD tails. This checkpoint decodes them using xEdit's current TES5 definitions for `wbVMADFragmentedPERK` and `wbVMADFragmentedQUST`.

## PERK results

- 6 / 6 records decoded; zero failures.
- 6 generic script attachments and 10 generic properties.
- 6 generated perk fragments.
- All six fragment indices resolve to an exact decoded PERK effect entry.
- 10 object-property relationships resolve to canonical Forms; zero unresolved targets.

The five Mysticism lock-opening perks bind generated `PRKF_*` scripts with two global properties. Adamant's necromancy controller binds one generated fragment to the perk effect that adds an activation choice. These are implementation facts, not generalized design rules.

## QUST results

- 7 / 7 records decoded; zero failures.
- 4 ordinary quest script attachments containing 46 properties.
- 10 stage/log-entry fragments.
- 4 VMAD alias structures with 5 alias-script attachments and 20 alias properties.
- 66 object-property relationships; zero unresolved targets.
- One quest (`WISkillIncrease02` in MysticismSlowerUnlocks) contains only the generic VMAD prefix and no fragmented tail; that absence is valid and preserved.

## Architectural consequence

Generated fragment bindings, quest-stage fragments, quest scripts, and alias scripts are distinct behavioral evidence types. The Balancer stores them separately from record-number balance fields and from Papyrus source code. Later behavioral analysis can join a fragment binding to the supplied `.psc` source when present, or explicitly mark source as unavailable.

## Rule status

No VMAD fragment or property is an approved Simonrim rule. Promotion remains evidence- and review-gated.
