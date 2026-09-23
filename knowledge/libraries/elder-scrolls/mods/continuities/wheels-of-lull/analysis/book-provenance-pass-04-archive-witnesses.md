# Wheels of Lull book provenance — pass 04 archive witnesses

Continuity: `tes.mod.wheels-of-lull`  
Audit date: 2026-09-23  
Scope: locate dated pre-Wheels Trainwiz source packages identified by pass 03, without promoting any BOOK relation until exact source text is inspected.

## Result

The two highest-value historical package families are no longer merely hypothetical or unavailable. Public archive metadata identifies original pre-Wheels packages for both **Aethernautics** and **Sotha Sil Expanded**.

This pass changes the source-discovery state, but **does not change any BOOK provenance classification**. Package existence, authorship, and date are evidence that a source corpus predates Wheels; they are not evidence that a specific Wheels BOOK text occurs inside that package.

## Aethernautics

Original package witness:

- title: **Aethernautics Main File**
- archive: ModDB
- uploader/creator: **Trainwiz**
- added: **2012-12-21**
- filename: `Aethernautics.rar`
- size: **7,995,338 bytes**
- MD5: `ea6e4206bd1485571ba54de32ba902a3`
- source page: https://www.moddb.com/mods/aethernautics-a-space-travel-mod/downloads/aethernautics-main-file

The dated package is a direct pre-Wheels source witness. Existing public descriptions and earlier audit evidence continue to verify that Aethernautics used Trainwiz's harquebus technology before Wheels of Lull.

However, exact-title and distinctive-phrase searches still do not establish that Wheels BOOK `0537158D` (*Harquebuses* / *On the Propulsion of Matter, Mind, and Mathematics via Magickal Means...*) existed verbatim in the 2012 package.

Current classification therefore remains:

- harquebus technology/terminology predates Wheels: **verified**
- exact Wheels treatise predates Wheels: **unverified**
- provenance class: **probable legacy Trainwiz material / strong indirect**
- promotion to exact external-text reuse: **not permitted without package-text comparison**

## Sotha Sil Expanded

Two original package witnesses are now located:

### Full Release

- title: **Sotha Sil Expanded Full Release**
- uploader/creator: **Trainwiz**
- added: **2012-12-25**
- filename: `SothaSilExpanded.rar`
- size: **135,490,464 bytes**
- MD5: `38ae4da28fc17168b5258789ae8ec6a5`
- source page: https://www.moddb.com/mods/sotha-sil-expanded/downloads/sotha-sil-expanded-full-release

### Version 2.0 full package

- title: **Sotha Sil Expanded 2.0**
- uploader/creator: **Trainwiz**
- added: **2014-03-08**
- filename: `SothaSilExpanded2_0.rar`
- size: **157,456,777 bytes**
- MD5: `b8bda83b188e9e89603345eb01964a53`
- source page: https://www.moddb.com/mods/sotha-sil-expanded/downloads/sotha-sil-expanded-20

Both packages predate Wheels of Lull and are therefore valid historical witness targets for exact text comparison. The archive metadata describes Sotha Sil Expanded as a large Clockwork City expansion with hundreds of cells and dozens of quests, making it a materially relevant prior Trainwiz corpus rather than a generic title match.

No one of the ten unresolved Wheels named works is promoted on this basis alone.

## Materialization attempt

The archive download handoff was tested during this pass. ModDB resolves the downloads through temporary DBolical mirror URLs, but the current retrieval environment does not materialize those binary RAR responses. The source pages and package metadata are reachable; the archive bytes are not currently available to the parser.

This is now a **binary materialization blocker**, not a source-discovery blocker.

When either archive is materialized, the next deterministic procedure is:

1. verify the archive against the published MD5;
2. inventory every plugin/text/readme asset without modifying the archive;
3. parse the source plugin records using the correct game format;
4. normalize all book/note/journal text with a source-specific comparison layer;
5. compare exact and near-exact text against the 33 Wheels BOOK comparison fingerprints;
6. preserve edition differences rather than collapsing variants;
7. promote only evidence-backed prior-source relationships into `normalized/book-source-relations.json`;
8. store package filename, hash, source date, source record identity, and exact/variant relation as provenance.

## Search boundary after pass 04

Generic exact-title web searches remain exhausted and should not be repeated without a new archive/index corpus.

The remaining named works stay unresolved:

1. *Wind Up and Wound Down*
2. *Musings On Power*
3. *De Rerum Mutabilitatis*
4. *How To Moon*
5. *Chronography, Volume I*
6. *Chronography, Volume II*
7. *Chronography, Volume III*
8. *Trademarks*
9. *Sybandis*
10. *Journeys Through Sybandis*

## Provenance totals after pass 04

- Wheels BOOK records: **33**
- verified prior/external reuse: **3**
- strong-indirect legacy candidate: **1**
- origin unresolved: **29**
- archived pre-Wheels Trainwiz package families now located: **2**
- package families text-materialized in the current environment: **0**

No provenance count changes are justified until the archive contents themselves are inspected.
