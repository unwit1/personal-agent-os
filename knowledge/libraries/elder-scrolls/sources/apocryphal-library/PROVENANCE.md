# Apocryphal Library provenance triage

This ledger separates **text extraction** from **origin verification** for the 784 `BOOK` records imported from `LB_ApocryphaBooks.esp`.

## Current pass

| Status | Count | Meaning |
|---|---:|---|
| Verified official game text | 2 | Independently matched to an existing normalized catalog record with external source provenance. |
| Editor-ID hint: ESO | 80 | The plugin's editor ID explicitly contains `_ESO`; useful for discovery, not proof. |
| Editor-ID hint: Oblivion | 10 | Editor ID contains `_OBL`; useful for discovery, not proof. |
| Editor-ID hint: Morrowind | 3 | Editor ID contains `_MW`; useful for discovery, not proof. |
| Editor-ID hint: MK/developer | 3 | Editor ID contains `_MK`; possible developer-text attribution hint, not proof. |
| Unresolved | 686 | No safe origin classification from the current deterministic pass. |

Total: **784** records.

## Verified normalized-catalog links

- [Daedric Worship and the Dark Elves](../../../books/catalog/daedric-worship-and-the-dark-elves.md) — existing catalog provenance identifies it as official `Elder Scrolls Online — Necrom` text; the compilation now supplies a full-text copy.
- [Parables of Saint Vorys](../../../books/catalog/parables-of-saint-vorys.md) — existing catalog provenance identifies it as official `Elder Scrolls Online — Necrom` text; the compilation now supplies a full-text copy.

## Rules for later promotion

1. Do not promote a record to official canon merely because its editor ID contains a game abbreviation.
2. Prefer direct game/plugin evidence, then a reliable transcript/index such as UESP or The Imperial Library.
3. Keep developer/obscure texts distinct from in-game primary sources.
4. Keep mod/community originals distinct from Bethesda/ZeniMax material.
5. Preserve the compilation path and FormID even after the original source is identified, so provenance remains traceable.

Machine-readable per-record statuses are in [`provenance-triage.json`](./provenance-triage.json).
