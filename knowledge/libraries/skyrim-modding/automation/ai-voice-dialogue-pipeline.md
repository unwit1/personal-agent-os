# Skyrim Mod Factory — AI Voice, Lip Sync, and Dialogue Packaging Pipeline

Created: 2026-09-24
Status: canonical AI-assisted voice workflow

## Objective

Automate dialogue audio from finalized INFO/text through generated voice, lip data, FUZ packaging, correct plugin/VoiceType paths and in-game validation.

## Canonical source manifest

Every voiced line should have a machine-readable record containing:
- quest/topic/INFO identity;
- final plugin identity;
- response index;
- speaker/NPC;
- VoiceType;
- raw subtitle text;
- spoken text after substitutions;
- pronunciation hints;
- voice/model/backend;
- generation settings/seed if applicable;
- source WAV hash;
- XWM/LIP/FUZ hashes;
- expected Data-relative output path;
- rights/provenance;
- QA state.

Never treat the generated FUZ directory itself as the source of truth.

## AI synthesis backends

### VOSpeaker
Strong batch/project candidate:
- mass line generation;
- pronunciation substitutions;
- arbitrary imported audio;
- conversion;
- LIP/XWM/FUZ generation;
- project separation;
- DBVO/FOMOD/loose exports.

### xVASynth
Game-character-oriented ML TTS backend with established Skyrim ecosystem integrations.

### Other TTS
Piper/XTTS/ElevenLabs/etc. can be adapters if the project rights/privacy/cost policy permits them.

Provider-specific audio quality does not alter the deterministic Skyrim packaging requirements.

## Spoken-text normalization

Before TTS:
- strip non-spoken stage directions when intended;
- expand/normalize symbols;
- preserve canonical subtitle separately;
- add pronunciation substitutions without changing displayed lore text;
- record every transformation.

The user should be able to audit:
**subtitle -> normalized spoken text -> synthesized WAV**.

## Audio QA

Automated:
- sample rate/channels/bit depth;
- silence at start/end;
- clipping/peak level;
- duration;
- empty/corrupt audio;
- unexpected extreme loudness;
- duplicate hash;
- missing line.

AI/audio analysis:
- pronunciation;
- intelligibility;
- emotion consistency;
- name/lore pronunciation;
- artifacts.

Human review remains required for release-critical character performance unless the project explicitly accepts automated-only quality.

## XWM/FUZ

Use a deterministic audio adapter such as Spooky's toolkit/known Bethesda tools to:
- normalize WAV;
- encode XWM;
- package XWM + LIP into FUZ;
- inspect FUZ after creation.

Round-trip where possible:
FUZ -> component extraction -> hash/metadata verification.

## Lip generation

### Bethesda/established FaceFX path
Prefer the known-good Creation Kit/FaceFX toolchain when available for release-quality Skyrim LIP.

### OpenFaceFX
OpenFaceFX is an interesting open-source alternative and provides:
- audio+transcript -> viseme curves;
- a FaceFXWrapper-compatible shim;
- an experimental Skyrim LIP writer.

As of the 2026-09-24 upstream snapshot, the project explicitly says its Skyrim LIP writer/shim is **not yet verified in game**.

Therefore:
- adapter status: experimental;
- allowed for research/cross-checks;
- not a sole release authority until Agent OS builds an in-game fixture corpus proving compatibility.

## Voice asset identity

Final path depends on the finalized dialogue/plugin identity.

Any operation that changes:
- plugin filename;
- INFO FormID;
- ESL compaction;
- merge identity;
- VoiceType;
- response numbering;

must invalidate affected generated voice outputs.

The build graph should automatically regenerate/repath those lines.

## Runtime test

For a representative or complete test set:
1. load fixture;
2. make line eligible;
3. assert INFO fires;
4. assert expected FUZ resolves;
5. capture playback start/end if runtime API exposes it;
6. screenshot/video lip animation for selected lines;
7. ensure subtitle/spoken content identity is correct;
8. inspect logs for missing voice resource.

## Rights gate

Before public packaging record:
- whose voice/model is represented;
- model training/use policy when relevant;
- permission basis for source voice assets;
- redistribution rights;
- platform/Nexus disclosure requirements;
- whether synthetic impersonation is appropriate for that project.

Agent OS must not infer legal permission from technical ability.

## Regeneration strategy

Dialogue text edit:
- invalidate TTS + LIP + XWM/FUZ.

Pronunciation-only edit:
- invalidate spoken WAV onward, keep subtitle.

Plugin/FormID/VoiceType change:
- regenerate/repath package identity; audio content may be reusable if unchanged.

TTS backend update:
- do not silently regenerate released voices; produce a candidate diff/listen set.

## Preferred tool chain

Finalized INFO manifest
-> voice synthesis (VOSpeaker/xVASynth/approved TTS)
-> audio QA
-> release-proven LIP generator
-> XWM/FUZ packaging
-> identity/path check
-> VFS resolution
-> in-game line fixture
-> human listening QA
