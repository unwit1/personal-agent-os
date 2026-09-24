# Trainwiz ChronoC0da continuity lineage

Continuity: `tes.mod.wheels-of-lull`  
Analysis date: 2026-09-24  
Evidence class: external/current project metadata and author-attributed post; **not** evidence extracted from the supplied `WheelsOfLull.esp`.

## Why this exists

The Wheels import previously modeled the supplied plugin as its own continuity overlay and handled individual reused texts carefully, but it did not yet preserve the larger project-to-project lineage that the official/current mod pages describe.

This record adds that relationship layer without collapsing separate mods into one source corpus.

## Root / predecessor relationship

The current Wheels of Lull Special Edition page describes Wheels as a **sequel to Sotha Sil Expanded** and says it ties together almost all of Trainwiz's previous Skyrim quest mods, including Aethernautics, Mzark, and Brhuce Hammar.

The current Aethernautics and Wheels pages both label the broader sequence **"The Trainwiz ChronoC0da"** and state that the overarching series begins with **Sotha Sil Expanded for Morrowind**.

Sotha Sil Expanded should therefore be modeled as a related predecessor/root continuity, not silently merged into Wheels.

## Published Skyrim sequence

The current Aethernautics and Wheels pages publish the same ordered Skyrim list:

1. **Blackreach Railroad**
2. **Brhuce Hammar: Legacy**
3. **Aethernautics: A Space Travel Mod**
4. **The Lost Wonders of Mzark**
5. **Fyr Manor**
6. **Dwemer Spectres**
7. **The Wheels of Lull**

This is a **continuity-order relationship**, not a claim that every record in every plugin has identical authority or that later edits retroactively existed in earlier releases.

## Aethernautics relationship

A Trainwiz post on the Oldrim Aethernautics page dated **2015-04-17** explicitly says Aethernautics and Wheels of Lull "take place in the same canon" while discussing a fan integration build.

That direct author-attributed statement is stronger evidence for the relationship than thematic similarity alone.

The same post describes differences between the two releases' Chronographer robes and harquebuses. Those differences are evidence **against** naive asset/text deduplication: related continuities can contain distinct editions or implementations even when they share a canon.

## Lorekeeper modeling rules

- Keep each mod as its own continuity/source package.
- Add explicit directed lineage/related-continuity edges rather than merging raw records.
- Allow central works/entities to be referenced by multiple continuities only when identity is verified.
- Preserve edition/variant differences between earlier and later appearances.
- Treat current mod-page chronology as project metadata, not as proof that a specific line of dialogue or BOOK text existed in an older package.
- Treat third-party patches/integration builds as derivative witnesses unless separately adopted by the original author/source.
- Do not promote ChronoC0da material into Bethesda canon; it remains a Trainwiz continuity layer.

## Recommended graph relationships

```text
Sotha Sil Expanded
  -> predecessor/root-of -> Trainwiz ChronoC0da

Trainwiz ChronoC0da ordered Skyrim sequence:
Blackreach Railroad
  -> Brhuce Hammar: Legacy
  -> Aethernautics
  -> The Lost Wonders of Mzark
  -> Fyr Manor
  -> Dwemer Spectres
  -> The Wheels of Lull

Aethernautics
  -> same-canon / earlier-work -> The Wheels of Lull

The Wheels of Lull
  -> sequel-to -> Sotha Sil Expanded
  -> convergence/ties-together -> earlier Skyrim quest mods in the published sequence
```

## Source witnesses

- Current Aethernautics Special Edition Nexus description: `https://www.nexusmods.com/skyrimspecialedition/mods/436`
- Current Wheels of Lull - Unwound Edition Nexus description: `https://www.nexusmods.com/skyrimspecialedition/mods/748`
- Trainwiz Oldrim Aethernautics post, 2015-04-17: `https://www.nexusmods.com/skyrim/mods/41754?tab=posts`

## Boundary

This lineage record improves cross-mod retrieval and provenance routing. It does **not** change the Wheels BOOK provenance counts, does not import unseen Aethernautics/Sotha Sil Expanded text, and does not justify any exact-text reuse claim without source-level comparison.
