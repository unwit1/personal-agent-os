# GLENMORIL first-pass extraction

This file records structural evidence from the directly parsed `Glenmoril.esm`. It is an ingestion checkpoint, not a complete plot summary.

## Quest records surfaced early in the source

Examples include:

- `04171135` — **Departure** (`zzzRevMq00`)
- `04009B59` — **The Blue Bird** (`zzzGHMq01`)
- `040083AC` — **The Blessing** (`zzzLrhMq07`)
- `04007B93` — **The Black Owl** (`zzzLrhSubQuest01`)
- `0401230D` — **Tainted Orphan** (`zzzGHMq03`)
- `04008685` — **The Cat and the Chick** (`zzzLrhMq10`)
- `04017530` — **Broken Egg** (`zzzGHMq05Joint`)
- `0460026B` — **Feast of Love** (`zzzRevMq01`)
- `04007733` — **The Way is Blocked** (`zzzLrhMq01`)
- `04014B4A` — **The Owls** (`zzzGHMq05Sub05`)
- `043ABF2B` — **Rite of Cannibalism** (`zzzRevSub03Rush`)
- `0438F141` — **Ahzidal** (`zzzRevBossQuestAhzidal`)

These names are evidence that the records exist, not yet evidence of chronological order.

## Named NPC evidence

Named records include **Hela the Druidess**, **Ulrik**, **Forgotten Vessel**, **Zuzu the Oneiromancer**, **Charlatan Joel**, **Innkeeper Gonzo**, **Pawnbroker Emil**, **Alchemist Hands-of-Rock**, **Cilla**, **Asmo**, **Cerebline**, and a GLENMORIL-specific **Sheogorath** record. These should be resolved against quest aliases and dialogue before character biographies are promoted.

## Location evidence

Named locations include **Namirapolis**, **Prayer Room of Caged Children**, **Ja'cobee's Birthplace**, **City of Disbelievers Nemalauta**, **Upper Yelem**, **Fishing Village**, **Hill of Rebirth**, **Sanctuary of Namira**, **Dream Surface**, **Rift of the Great Cat**, **Throne of the Soul Matron**, **Great Hole**, **Yelem's Third Laboratory**, **Nedic Henge**, and **Varlaiswend**.

## Faction evidence

The plugin contains explicit faction records for **Glenmoril**, **Witch Hunter**, **Black Owl**, **Hircine**, **Leech Legion**, **Atmoran Army**, **Thalmor**, **Church**, **Ghoul**, **Ashlander**, **500 Companion**, **Snow Prince**, and others. Names alone do not establish alliances or chronology.

## Textual-source evidence

The 264 BOOK records include imported Elder Scrolls texts and GLENMORIL-specific notes/items. Examples include **Yelem's Note** records, **Black Book: The Gardener**, **Ancient Note**, and numerous spell/summon texts such as **Dreamstride**, **Ashes**, **Heart**, and **Taproot** records. The next text pass should separate reused official texts from Vicn-authored/source-specific material and preserve each source independently.

## Dialogue checkpoint

The ESM exposes 3,846 INFO records with decoded response strings. Early records include dialogue concerning Lalanoah, Falkreath's orphaned children, restrictions on entering town, and the consequences of the civil war. Speaker/quest/topic attribution still needs to be reconstructed from group and condition data before these lines are used as character evidence.
