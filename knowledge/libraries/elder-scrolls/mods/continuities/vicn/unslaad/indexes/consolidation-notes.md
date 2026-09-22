# UNSLAAD consolidation notes

Continuity: tes.mod.vicn.unslaad

The corpus has grown through parallel ingestion passes. This file tracks only **remaining** consolidation concerns.

## Completed consolidation

The following duplicate groups have been reconciled:

- **GHARTOK:** unique GC9/placement evidence folded into `artifacts/ghartok-weapons.md`; duplicate removed.
- **Elder Wood:** equipment/progression evidence folded into `artifacts/elder-wood-relics.md`; duplicate removed.
- **Earthbones / Hgmieil:** Earthbones recipe evidence folded into `artifacts/earthbones-weapons.md`, identity/progression evidence folded into `entities/characters/hgmieil.md`; overlap page removed.
- **Item descriptions:** exploratory audit folded into `indexes/item-description-completeness.md`; superseded audit removed.
- **Cross-VICN Arkved / Oneiromancer:** promoted to parent VICN relationships and local duplicate removed.
- **Cross-VICN Jhunal / Saarthal / Owls:** promoted to parent VICN relationships and local duplicate removed.

## Keep as complementary

### Gray Owl
Keep separate:
- identity/ontology;
- equipment;
- craft forms;
- mask/outfit;
- magic mechanics.

### KINMUNE / Oracle
Keep separate:
- source/provenance fragments;
- workshop placement;
- Ayrenn/Oracle relationship;
- parent cross-VICN Oracle thread.

### Jill
Keep separate:
- actor/transformation forms;
- equipment;
- staff;
- parent cross-VICN Jill thread.

## Current policy

Before creating a new dossier:

1. search the current UNSLAAD tree by exact entity/item name;
2. update the existing page if it already serves the same retrieval purpose;
3. create a new page only for a genuinely different evidence layer;
4. put cross-work synthesis under the parent `vicn/relationships/` directory rather than inside UNSLAAD whenever possible.

## Goal

The mature continuity should optimize for:
- source fidelity;
- selective retrieval;
- low context duplication;
- clear canonical entry points;
- preserved raw evidence underneath.

No additional obvious duplicate artifact dossiers are currently flagged by this pass.

## Targeted synthesis batch — Magnar through Yngol

Completed in-place consolidation for five saved candidate clusters without creating duplicate dossiers:

- **Magnar / mirrors** — separated Insight, prayer/text, and quest-object evidence; retained as UNSLAAD-local pending independent cross-work Magnar evidence.
- **Mnegmegh / Priest of Jhunal** — added explicit implementation graph, retrieval path, and non-equivalence guardrail.
- **Gral / Mindok / Owl Forest** — linked to the parent Hare/word-rewriting thread while keeping Gral/Mindok identity UNSLAAD-local.
- **Elder Wood** — wired the local relic dossier to the existing parent Elder-Wood continuity thread.
- **Yngol / Tstunal** — wired local provenance to the parent thread and explicitly separated shared external substrate from UNSLAAD/DAc0da adaptations.

The retrieval map now directly exposes Mnegmegh / Priest of Jhunal.

### Next synthesis frontier

Prefer unresolved high-value work that adds new evidence rather than repeating these nodes:

1. remaining external-provenance checks for adapted mythic fragments;
2. source-reliability/contradiction indexing for Khev, Herkel, Hermit, Jhunal/Gray Owl, and Insight narrators;
3. selected alias/script-property resolution where identity transitions are still uncertain;
4. deeper placement analysis only when it can resolve a live ambiguity.

## Final consolidation status

**No active UNSLAAD consolidation backlog remains for the supplied 3.0.6 ESM.**

The previously listed frontier items have been closed as follows:
- provenance: classified, including intentional unknown-provenance cases;
- reliability/contradictions: indexed;
- alias/identity transitions: resolved where implementation evidence exists and explicitly bounded where it does not;
- placement analysis: broad high-value sweep complete; further work is question-driven only;
- cross-VICN seeds: promoted, source-scoped, or rejected as insufficient;
- retrieval: compact map in place.

New work should be triggered by **new source evidence or a concrete research question**, not by re-running general ingestion.
