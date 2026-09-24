# Wheels of Lull book provenance — pass 05 retrieval-path and historical-metadata audit

Continuity: `tes.mod.wheels-of-lull`  
Audit date: 2026-09-24  
Scope: continue the pass-04 archive-materialization branch without repeating generic title searches; test alternate retrieval paths and extract additional historical-development evidence from already-known and newly mirrored source metadata.

## Result

No BOOK relation is promoted in this pass.

The original Aethernautics and Sotha Sil Expanded package witnesses remain located and externally downloadable, but the current execution environment still cannot materialize the RAR response bodies for deterministic hash verification and plugin/text extraction. The blocker is therefore still **binary acquisition**, not source discovery.

Pass 03 had already identified the September 2012 **Aethernautics Weaponry Tweaks** Nexus page as a harquebus-history witness. Pass 05 does **not** count rediscovering that page as new work. The added value here is:

- exact preservation of its upload/update chronology;
- a second, machine-readable preserved Nexus-metadata snapshot in `metherul/NMDB`;
- extraction of previously unrecorded development-history detail about a planned "Cronographer" / Sotha Sil expansion;
- a separately classified Trainwiz statement from 2015 explicitly linking Aethernautics and Wheels as the same canon;
- a re-tested binary acquisition path that narrows the remaining blocker.

## Archive retrieval path re-check

The ModDB download-start pages for the already-known package witnesses remain live:

- `Aethernautics.rar` — 7,995,338 bytes — published MD5 `ea6e4206bd1485571ba54de32ba902a3`
- `SothaSilExpanded.rar` — 135,490,464 bytes — published MD5 `38ae4da28fc17168b5258789ae8ec6a5`
- `SothaSilExpanded2_0.rar` — 157,456,777 bytes — published MD5 `b8bda83b188e9e89603345eb01964a53`

The download handoff currently resolves to temporary DBolical CDN endpoints, confirming that the archive objects still exist behind the ModDB download flow. Those temporary binary URLs are intentionally **not persisted** because they are expiring transport tokens, not durable provenance.

The current web parser rejects the binary response and the current container download path cannot acquire it. No local MD5 was therefore computed, and no claim is made that the archive bytes were inspected.

A search of the currently connected ChatGPT file library also returned no exact Aethernautics/Sotha Sil Expanded archive or plugin package. This is recorded only as a negative search state for the current accessible library, not proof that the user has never possessed the files elsewhere.

## Deeper extraction from the September 2012 Aethernautics witness

The already-known Nexus page for **Aethernautics Weaponry Tweaks** (mod 23569, author `pickel5857`) currently exposes:

- original upload: **2012-09-03 08:07 UTC**
- last update: **2012-09-06 04:48 UTC**
- direct attribution of the underlying Aethernautics mod to **Trainwiz**
- an explicit description of its subject as the harquebuses from Trainwiz's Aethernautics
- references to basic, Heavy, Ohmic, and Magmatic harquebuses
- credits stating that Aethernautics contains Trainwiz's original harquebus designs

A preserved machine-readable copy of the same Nexus metadata also exists in `metherul/NMDB` at:

`skyrim/23569 - Aethernautics Weaponry Tweaks.json`

snapshot commit:

`b13b73f739202271ef763febb1b0420b3f65922c`

The mirror is useful as an independent durable metadata corpus, but it does not raise the evidence above what the contemporaneous Nexus page itself establishes.

This material predates the Nexus original upload of *The Wheels of Lull* on **2014-10-03**.

### What this proves

- Aethernautics harquebus technology and multiple named harquebus variants were publicly documented by September 2012.
- The existing Wheels classification for BOOK `0537158D` (*Harquebuses*) as a **strong-indirect legacy Trainwiz candidate** remains well supported at the technology/concept level.
- The underlying harquebus design lineage clearly predates Wheels.

### What this does not prove

- It does **not** contain or identify the exact Wheels treatise text *On the Propulsion of Matter, Mind, and Mathematics via Magickal Means...*.
- It therefore does not justify promoting BOOK `0537158D` to verified prior-text reuse.
- The Weaponry Tweaks page is third-party commentary/add-on documentation, not an original Trainwiz source record.

## Newly extracted Chronographer development-history detail

The September 2012 Weaponry Tweaks description contains a section that had not been preserved in the previous Wheels provenance notes. Its author says they were planning an Aethernautics expansion in which the player would be hunted by and later join the **"Cronographers"**, with a planned Cronographer fortress on **Sotha Sil**.

This is historically interesting because it predates Wheels by more than two years, but the evidence boundary is strict:

- the statements describe the **third-party author's future plans**;
- they are not proof that those planned quests shipped;
- they are not proof that Trainwiz authored that exact Chronographer/Sotha Sil concept at that date;
- they are not imported as in-universe Aethernautics or Wheels lore.

The correct classification is **pre-Wheels community-adjacent development-history evidence**, not canonical/source-text evidence.

## Author-confirmed Aethernautics/Wheels continuity relation

A Trainwiz post on the Oldrim Aethernautics Nexus page, dated **2015-04-17**, explicitly states that Aethernautics and Wheels of Lull take place in the same canon while describing a fan integration version.

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

Do not repeat generic title searches, ModDB package rediscovery, the basic September-2012 Aethernautics Weaponry Tweaks harquebus finding from pass 03, or the pass-05 deeper extraction recorded here.

Highest-value next step remains:

1. acquire one of the already-located original RARs through a binary-capable environment;
2. verify its published MD5;
3. extract/inventory without mutating the archive;
4. parse every BOOK/note/journal/readme text record;
5. compare normalized fingerprints against all 33 Wheels BOOKs;
6. preserve variants and source chronology;
7. promote only exact or demonstrably variant prior-source relationships.

If an archive cannot be acquired, the next genuinely new source class worth checking is a preserved **record-level dump, translation string table, xEdit export, or plugin-derived BOOK inventory** for the historical Aethernautics/Sotha Sil Expanded versions.
