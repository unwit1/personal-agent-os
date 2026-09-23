# Multi-actor speaker groups

Some Dealing with Daedra INFO records contain multiple positive Subject GetIsID alternatives.

These are not all errors or unresolved records.

## Same narrative entity, multiple state records

- **Arincine** — two state-specific actor records share 10+ lore/service lines.
- **Servitor** — two actor records share possessive/relationship greeting dialogue.
- **Vampire Master** — multiple stage-state Master records share dialogue; already normalized under vampire-master.md.

These may be indexed at the narrative-entity level.

## Defined group/role sets

- **Riften steward world-state role** — two base actors can deliver identical corruption/Thane dialogue depending political state.
- **Temple priest set** — three base priests deliver the same no-divorce/Mara-commitment response.
- **Widows unhappy-spouse set** — Frabbi, Olda, and Nivenor share parts of the husband-targeting branch, with individual grievance responses.
- **Cult of the Return Recruiter variants** — multiple Recruiter forms deliver the same public-recruitment message.
- **Family member set** — Jurger Stonearm, Rithrannir, and Salonia share outsider/goodbye lines.
- **Gentleman's Club Patron sets** — multiple Patron actor records share ambient/service lines.
- **Escort sets** — multiple Escort records share bath/sexual-service dialogue.
- **Labourer set** — construction labourers share worksite dialogue.

These should be indexed as group dialogue unless another source resolves the exact physical speaker.

## Complex sets that should remain contextual

Some INFO records allow heterogeneous actor sets because they implement generic training/payment or system dialogue.

Example: a "cannot afford training" line can be delivered by Beldam Annes, Quinergus, Thaer, Lysara Carius, Regalt, Keeper Harorn, a Dagon cultist, Gatekeeper figures, and others.

Such records encode a reusable interaction system, not shared lore doctrine.

## Rule

Narrative identity > role set > heterogeneous context.

Do not force a lower-level identity when the plugin deliberately supplies a higher-level speaker set.
