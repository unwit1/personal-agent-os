# Skyrim Mod Factory — Implementation Question Preemption Catalog

Created: 2026-09-24

The agent should internally answer these before asking the user implementation questions. Ask only when the answer materially changes behavior, compatibility, licensing, save safety, or creative intent.

## Product intent

- What does the player observe?
- What triggers it?
- What should never happen?
- Is it configurable?
- Does it affect player, NPCs, world, UI, visuals, combat, quests, economy, or progression?
- Is it global or scoped?
- Does it need to work on existing saves?
- Does removing it need to be supported?

## Target/runtime

- Skyrim SE/AE executable version?
- Steam/GOG/VR?
- Is 1.5.97 support required?
- Is the feature inherently flat-screen or VR-specific?
- Does it require SKSE?
- Address Library?
- BEES/current header support?

## Plugin architecture

- Does it need a plugin at all?
- ESP vs ESL/light vs ESM?
- New forms or overrides?
- New masters?
- Can existing records be distributed at runtime instead?
- Does the mod need OnAM/ONAM/large-ref/navmesh handling?
- Can FormIDs ever be compacted safely?

## Data records

- Which record signatures are touched?
- Which exact fields?
- Which fields are authoritative if another overhaul conflicts?
- Are leveled lists involved?
- Perks/Entry Points?
- MGEF archetypes?
- ActorBase/template inheritance?
- CELL water/lighting?
- Quest aliases/fragments?
- DOBJ slots?
- keywords/FormLists?

## Runtime distribution

Could SPID/KID/BOS/FLM/SkyPatcher replace static edits?

If yes:
- what grammar/version?
- when does mutation occur?
- base NPC vs actor instance?
- static xEdit result vs final runtime result?
- how are overlapping configs ordered?
- what log proves application?

## Papyrus

- Can this be done without polling?
- Which events exist?
- Which host object owns the script?
- Does it need aliases?
- Does state persist?
- Which properties bake into saves?
- Does it register for updates/mod events/keys/menus?
- How are registrations cleaned up?
- Are latent calls safe here?
- Is po3 Papyrus Extender/PapyrusUtil/JContainers required?
- Can native code remove a heavy Papyrus loop?

## Native SKSE

- Is native code actually necessary?
- Which engine subsystem/class?
- Hook or event sink?
- Can CommonLib expose it directly?
- Is relocation required?
- What runtimes have matching layouts?
- How will serialization be versioned?
- Is the plugin safe across load/save/new game?
- Can it fail closed if dependency/API unavailable?
- What license does linked CommonLib version require?

## UI

- Existing SkyUI/MCM or custom menu?
- Scaleform or native/PrismaUI?
- Exact menu identifiers?
- controller/keyboard/VR interaction?
- text-input suppression?
- localization?
- accessibility/scaling?

## Animation

- replacement only -> OAR?
- behavior state change -> Pandora?
- root motion -> AMR?
- hitbox/contact -> Precision?
- combo AI -> SCAR/MCO family?
- payload/event annotations?
- skeleton nodes?
- first-person and third-person variants?
- creatures?
- VR?

## Mesh/texture

- Skyrim SE BSTriShape target?
- skinned?
- partitions?
- body slots?
- skeleton?
- _0/_1?
- TRI morph?
- collision?
- shader type?
- texture slots?
- alpha?
- cubemap?
- parallax/PBR?
- BodySlide project?
- can PyNifly script the transformation?

## Physics

- Havok rigid-body collision?
- CBPC/FSMP cloth/body?
- collision layer/material?
- skeleton nodes?
- constraints?
- VR hand/PLANCK/HIGGS interaction?

## World edits

- exterior/interior?
- landscape?
- navmesh?
- doors?
- persistence?
- Room Bounds/Portals?
- location/LocationRefType?
- encounter zone?
- water flow?
- occlusion?
- LOD?
- seasons/grass?

## Quests/dialogue

- Story Manager start?
- aliases and fill rules?
- stages/objectives?
- scenes?
- package overrides?
- INFO conditions?
- voice?
- subtitles/localization?
- mid-quest update policy?

## Audio/voice

- VoiceType?
- INFO identity/plugin path?
- WAV/XWM/FUZ/LIP?
- custom SoundDescriptor?
- 2D/3D attenuation?
- localization?
- generated voice licensing?

## Compatibility

- likely overlapping popular mods?
- Simonrim interaction?
- runtime patchers touching same field?
- asset overwrite?
- native hook overlap?
- animation priority?
- UI menu replacement?
- generated-patch order?
- save state?

## Performance

- number of actors/forms scanned?
- event-driven or polling?
- initialization cost?
- memory allocation?
- render GPU pass?
- Papyrus budget?
- does work happen every frame?
- can results be cached?

## Testing

- minimal reproducible profile?
- negative test?
- new game?
- established save?
- update from prior version?
- VR test?
- combat stress?
- cell transition?
- death/resurrection?
- save/load?
- fast travel?
- main menu -> load?
- repeated install/reload?

## Distribution/release

- dependencies?
- optional integration patches?
- FOMOD choices?
- source/license?
- Nexus requirements?
- generated-output redistribution permissions?
- versioning?
- changelog?
- compatibility matrix?
- debug symbols/log level?

## Agent behavior

Before implementing, Agent OS should produce:
1. chosen architecture;
2. rejected alternatives and why;
3. artifacts to create;
4. tools/adapters;
5. validation gates;
6. test matrix;
7. likely conflicts;
8. save/update implications;
9. remaining genuinely creative decisions.

The goal is to make the user answer design questions, not low-level questions the repository can answer itself.


## Questions the agent must resolve with tools before asking the user

These are **not user questions** when the relevant data/tool is available.

### Current project/load-order facts
Resolve automatically:
- active MO2 profile;
- enabled plugins and priority;
- winning record;
- complete override chain;
- asset winner/VFS chain;
- plugin masters;
- current FormIDs/EditorIDs;
- current runtime/SKSE/Address Library;
- installed framework versions;
- current generated-output freshness.

Preferred sources:
houseCARL/MO2/xEdit/static adapters.

### API/schema facts
Resolve automatically:
- whether a record field exists;
- field type/cardinality;
- valid enum values;
- CTDA function/parameter schema;
- Papyrus function/provider/signature;
- CommonLib class/member/relocation availability;
- SPID/KID/BOS/OAR/SkyPatcher grammar;
- NIF block/shader/texture-slot structure.

Preferred sources:
generated schema corpora, xEdit definitions, Papyrus provider index, CommonLib source, pinned framework docs.

### Feasibility/tool choice
Resolve automatically:
- can a static record do it?
- can a runtime distributor avoid a conflict?
- does Papyrus expose the needed event?
- does OAR avoid a behavior edit?
- does Pandora need to patch the graph?
- does PyNifly support the required NIF operation?
- can DevBench observe/assert the result?

Use `implementation-patterns-core.json` and `tool-capability-registry.json`.

### Validation facts
Resolve automatically:
- binary parses;
- references resolve;
- output matches schema;
- source/output hashes;
- missing assets;
- stale generated artifacts;
- runtime assertion result;
- new owned errors/warnings;
- tool coverage denominator.

### Ask the user only when

A question materially changes:
- player-facing creative intent;
- desired balance/feel;
- aesthetic direction;
- target support policy when no prior project policy exists;
- whether an incompatible alternative should be chosen;
- save-breaking migration promise;
- public redistribution/licensing decision;
- use of generated voice/visual identity with rights implications;
- a consequential action the project's approval policy reserves for the user.

## Automatic research before implementation

If the selected implementation depends on a framework/tool not already pinned in the project:

1. inspect current upstream source/release;
2. record license;
3. record latest supported runtime matrix;
4. ingest syntax/API docs;
5. identify known breaking changes;
6. add/update adapter manifest;
7. build a minimal fixture;
8. mutation-test the validator;
9. only then use it as an autonomous dependency.

## Unknown implementation mechanism

If the user asks for behavior not covered by any current pattern:

1. decompose observable behavior into engine systems;
2. search the knowledge repository;
3. query actual game/master records for analogous vanilla behavior;
4. search current frameworks/tools;
5. inspect upstream source if docs are insufficient;
6. create candidate implementation patterns;
7. rank by invasiveness, compatibility surface and testability;
8. implement a minimal proof fixture;
9. promote the validated pattern to the registry.

The default response to an unfamiliar implementation problem is **research + prototype**, not asking the user to choose among low-level technologies they should not need to know.
