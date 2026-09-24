# Wheels of Lull book provenance — pass 05 retrieval-path and historical-metadata audit

Continuity: `tes.mod.wheels-of-lull`  
Audit date: 2026-09-24  
Scope: continue the pass-04 archive-materialization branch without repeating generic title searches; test alternate retrieval paths and preserve genuinely new pre-Wheels historical metadata.

## Result

No BOOK relation is promoted in this pass.

The original Aethernautics and Sotha Sil Expanded package witnesses remain located and externally downloadable, but the current execution environment still cannot materialize the RAR response bodies for deterministic hash verification and plugin/text extraction. The blocker is therefore still **binary acquisition**, not source discovery.

This pass did, however, locate a new **contemporaneous third-party Nexus metadata witness from September 2012** that materially strengthens the historical-development record around Aethernautics harquebuses and provides a cautious pre-Wheels clue for Chronographer terminology.

## Archive retrieval path re-check

The ModDB download-start pages for the already-known package witnesses remain live:

- `Aethernautics.rar` — 7,995,338 bytes — published MD5 `ea6e4206bd1485571ba54de32ba902a3`
- `SothaSilExpanded.rar` — 135,490,464 bytes — published MD5 `38ae4da28fc17168b5258789ae8ec6a5`
- `SothaSilExpanded2_0.rar` — 157,456,777 bytes — published MD5 `b8bda83b188e9e89603345eb01964a53`

The download handoff currently resolves to temporary DBolical CDN endpoints, confirming that the archive objects still exist behind the ModDB download flow. Those temporary binary URLs are intentionally **not persisted** because they are expiring transport tokens, not durable provenance.

The current web parser rejects the binary response and the current container download path cannot acquire it. No local MD5 was therefore computed, and no claim is made that the archive bytes were inspected.

A search of the currently connected ChatGPT file library also returned no exact Aethernautics/Sotha Sil Expanded archive or plugin package. This is recorded only as a negative search state for the current accessible library, not proof that the user has never possessed the files elsewhere.

## New pre-Wheels historical witness: Aethernautics Weaponry Tweaks

A preserved Nexus metadata record in `metherul/NMDB` captures **Aethernautics Weaponry Tweaks** (Nexus mod 23569), authored by `pickel5857`.

Machine timestamps in that snapshot:

- created: **2012-09-03 08:07:05 UTC**
- last updated in the captured record: **2012-09-06 04:48:20 UTC**
- referenced original Aethernautics Nexus mod: **23260**
- referenced original author: **Trainwiz**

This predates the Nexus original upload of *The Wheels of Lull* on **2014-10-03**.

The snapshot explicitly describes its subject as the harquebuses from Trainwiz's Aethernautics and discusses the original Aethernautics harquebus designs. It also names several weapon variants already associated with that source ecosystem, including basic, Heavy, Ohmic, and Magmatic harquebuses.

### What this proves

- Aethernautics harquebus technology and multiple named harquebus variants were publicly documented by September 2012.
- The existing Wheels classification for BOOK `0537158D` (*Harquebuses*) as a **strong-indirect legacy Trainwiz candidate** remains well supported at the technology/concept level.
- The underlying harquebus design lineage clearly predates Wheels.

### What this does not prove

- It does **not** contain or identify the exact Wheels treatise text *On the Propulsion of Matter, Mind, and Mathematics via Magickal Means...*.
- It therefore does not justify promoting BOOK `0537158D` to verified prior-text reuse.
- It is a third-party mod page, not an original Trainwiz source record.

## Chronographer development-history clue

The same September 2012 third-party metadata says the author was planning an Aethernautics expansion in which the player would be hunted by and later join the **"Cronographers"**, with a planned Cronographer fortress on **Sotha Sil**.

This is historically interesting because it predates Wheels by more than two years, but the evidence boundary is strict:

- the statements describe the **third-party author's future plans**;
- they are not proof that those planned quests shipped;
- they are not proof that Trainwiz authored that exact Chronographer/Sotha Sil concept at that date;
- they are not imported as in-universe Aethernautics or Wheels lore.

The correct classification is **pre-Wheels community-adjacent development-history witness**, not canonical/source-text evidence.

## Author-confirmed Aethernautics/Wheels continuity relation

A later Trainwiz post on the Oldrim Aethernautics Nexus page, dated **2015-04-17**, explicitly states that Aethernautics and Wheels of Lull take place in the same canon while describing a fan integration version.

That post also distinguishes the two mods' harquebus implementations and describes changes made to align Aethernautics's Chronographer robes, harquebuses, and merchant content with Wheels.

Because this post is after Wheels released, it cannot establish that any specific Wheels BOOK was published earlier. It is nevertheless strong author-attributed evidence for the intended **shared Trainwiz continuity** and should be used as a continuity-relationship witness, not as prior-text provenance.

## Current provenance classification

Unchanged:

- Wheels BOOK records: **33**
- verified prior/external text reuses: **3**
- strong-indirect legacy candidate: **1** (*Harquebuses*)
- origin unresolved: **29**
- unresolved named works: **10**
- pre-Wheels package families located: **2**
- package families materialized and hash-verified locally: **0**

## Resume boundary

Do not repeat generic title searches, ModDB package rediscovery, or the September-2012 Aethernautics Weaponry Tweaks metadata discovery.

Highest-value next step remains:

1. acquire one of the already-located original RARs through a binary-capable environment;
2. verify its published MD5;
3. extract/inventory without mutating the archive;
4. parse every BOOK/note/journal/readme text record;
5. compare normalized fingerprints against all 33 Wheels BOOKs;
6. preserve variants and source chronology;
7. promote only exact or demonstrably variant prior-source relationships.

If an archive cannot be acquired, the next genuinely new source class worth checking is a preserved **record-level dump, translation string table, xEdit export, or plugin-derived BOOK inventory** for the historical Aethernautics/Sotha Sil Expanded versions.
