# Wheels of Lull book variant analysis — pass 01

Continuity: `tes.mod.wheels-of-lull`  
Scope: edition-level comparison for verified externally reused BOOK records.

## KINMUNE — `0537158E`

### Compared witnesses

**Wheels witness**
- FormID: `0537158E`
- Editor ID: `_Lull_Book2`
- Raw-text SHA-256: `e0e5bc8540d5ace7c57b63c84e498d9abeb47f1a45b8b344436c9dc914e9524d`
- Normalized-text SHA-256: `58fd4261a7abfe7ac6b7fe55c2abf5ea2e60e58e03d37a415553b91a594302f5`
- Comparison-text SHA-256: `7a28bb0a9531239b3bb051d3ac005af3679ddb38d387a1a7a65f58cb838a7759`

**Central witness**
- Path: `knowledge/libraries/elder-scrolls/sources/apocryphal-library/books/040008F1-anon-anu-anui-el.txt`
- Git blob SHA: `edecd6f81ba984ae7cd3f643cfa6d41cf2bc5259`
- Source role: central compilation witness for KINMUNE source-history/edition comparison.

### Deterministic similarity

Using lowercase comparison-normalized word tokens and unique contiguous 5-token shingles:

- Wheels tokens: **615**
- Central tokens: **736**
- Wheels 5-shingles: **610**
- Central 5-shingles: **719**
- Shared 5-shingles: **561**
- Wheels-shingle containment in central witness: **91.97%**
- 5-shingle Jaccard similarity: **73.05%**
- Longest exact contiguous token run: **191 tokens**

### Edition findings

This is decisively the same underlying work, but **not the same edition/text witness**.

Material differences include:

- the central witness contains a Dominion / Queen Ayrenn framing layer that is absent from the Wheels BOOK;
- the expansion of the KINMUNE acronym differs between the witnesses;
- the central witness contains additional ending/framing material and title strings that Wheels omits;
- the final Cyrod passage is substantively reworded in Wheels rather than merely reformatted;
- several small spelling, punctuation, and copy-edit differences occur throughout;
- at least one duplicated phrase/typing defect in the central witness is cleaned in the Wheels version;
- the Varliance notation differs by one plus sign.

### Classification

- Work identity: **same**
- Exact-text identity: **different**
- Wheels relation: **embedded abridged/edited variant**
- Safe to deduplicate full text: **no**
- Safe to centralize source history/work identity: **yes**
- Required storage model: central work + multiple source/edition witnesses + continuity-local embedding relation.

This is exactly the case the central lore repository must preserve rather than collapsing by title.

## Tatterdemalion and Xal-Gosleigh status

Both works now have central Imperial Library catalog records, but their complete external text witnesses are not mirrored in the repository yet. Their Wheels relationships are verified at the work/section level; deterministic full-edition diffing remains pending until a local source witness is ingested.

## Next variant pass

1. Ingest or reference a durable full-text witness for *Tatterdemalion*.
2. Ingest the relevant Xal **Day of the Power/Knowledge** letter as a section-level source witness.
3. Run the same comparison-normalization and shingle/diff method.
4. Record additions, omissions, substitutions, and excerpt boundaries without replacing the raw Wheels records.
