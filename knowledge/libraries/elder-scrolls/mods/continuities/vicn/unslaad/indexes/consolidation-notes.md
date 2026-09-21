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
