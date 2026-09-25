# Skyrim Mod Factory — Agent OS Creation Kit Bridge

Created: 2026-09-24
Status: proposed implementation architecture

## Why a CK bridge is still needed

houseCARL/Mutagen/xEdit can automate a large amount of plugin data safely, but some Skyrim authoring semantics remain editor-owned or far easier to validate inside Creation Kit:

- navmesh authoring/finalization and door links;
- spatial object placement and render-window context;
- landscape editing;
- Room Bounds/Portals;
- complex Quest/Scene/Dialogue authoring bookkeeping;
- FaceGen export;
- editor-generated Papyrus fragments;
- some voice/lip workflows;
- CK-specific warnings/validation.

The goal is **not** to let an AI click arbitrary screen coordinates. The goal is to expose narrowly typed operations over a CKPE-based bridge.

## Preferred architecture

```
Agent OS / MCP
      |
      v
AgentOSCKWorker.exe
      |
 named pipe / localhost
      |
CKPE plugin: AgentOSCKBridge.dll
      |
CreationKit.exe + CKPE
```

The external worker owns:
- job queue;
- schemas;
- timeout/restart policy;
- receipts;
- artifact staging.

The in-process CKPE plugin owns:
- CK main-thread dispatch;
- editor object/record access;
- render-window/editor commands;
- warning/event capture.

## Transaction model

Never open the canonical source plugin as the only writable copy.

For every automated CK job:

1. materialize/copy a staged plugin workspace;
2. hash it;
3. launch CK/CKPE with exact masters;
4. verify active file;
5. execute one typed job;
6. save staged output;
7. close/reload;
8. validate in xEdit/Mutagen;
9. compare intent diff;
10. only then promote the artifact.

## Initial typed operations

### Session
- `ck.session.open`
- `ck.session.status`
- `ck.session.close`
- `ck.active_file.get`
- `ck.warnings.list`
- `ck.save.staged`

### Record/editor verification
- `ck.form.open`
- `ck.form.validate`
- `ck.quest.validate`
- `ck.scene.validate`
- `ck.dialogue.validate`

These should prefer reading/validation; ordinary deterministic field editing should remain in houseCARL/Mutagen.

### FaceGen
- `ck.facegen.export_npc`
- `ck.facegen.export_batch`
- `ck.facegen.verify_paths`

Postconditions:
- FaceGeom exists;
- FaceTint exists;
- filenames/FormID/plugin identity match;
- output wins in VFS;
- houseCARL FaceGen check passes.

### Navmesh
Initial automation should be validation-heavy:
- `ck.navmesh.inspect_cell`
- `ck.navmesh.validate`
- `ck.navmesh.finalize`
- `ck.navmesh.door_links`
- `ck.navmesh.screenshot`

Do **not** initially expose arbitrary automatic triangle rewriting as a safe repair.

A future path may generate candidate navmesh from geometry, but CK finalization + runtime traversal remains required.

### Room Bounds and Portals
- list room bounds/portals;
- identify refs outside expected room;
- validate adjacency/opening;
- render debug screenshot.

Mutating these automatically should remain proposal-only until visual fixtures prove correctness.

### Render-window evidence
- focus/reference lookup;
- fixed camera transform;
- hide/show debug overlays;
- screenshot/render-window capture.

Useful for:
- object placement;
- portal visibility;
- navmesh;
- collision markers;
- landscape seams.

### Quest/dialogue
The agent can generate QUST/DIAL/INFO data through typed plugin tools, but the CK bridge can:
- open/rebuild editor relationships;
- validate alias IDs;
- validate fragment attachment;
- compile fragments;
- enumerate CK warnings;
- export voice metadata.

## CKPE advantage

Creation Kit Platform Extended already provides:
- reverse-engineered CK internals;
- a PluginAPI;
- fixes/stability improvements;
- a maintained codebase for Skyrim SE Creation Kit.

The Agent OS bridge should build against/pin CKPE rather than reverse-engineering CK independently unless a required API is missing.

## GUI automation fallback

If an operation is not exposed through CKPE:

Allowed fallback:
- Windows UI Automation by control identity/name;
- bounded workflow;
- screenshot before/after;
- exact CK version and layout;
- completion marker;
- timeout;
- restart recovery.

Avoid:
- raw coordinates;
- blind keyboard macros;
- accepting a process exit as proof of success.

Every fallback operation remains **supervised/proposal-only** until replay tests show reliability.

## Completion proof

A CK job reports success only if:
- expected CK operation reports completion;
- CK warnings are captured/classified;
- output changed in the expected touch-set;
- xEdit loads it without errors;
- Mutagen reload succeeds where modeled;
- generated assets exist;
- runtime/visual test passes if the semantics require one.

## Long-term AI authoring goal

The agent should be able to say:

> This quest needs a scene and navmesh-aware encounter.

Then:
- create deterministic records via typed tools;
- use CK only for the editor-owned pieces;
- compile fragments;
- finalize navmesh;
- capture CK evidence;
- post-validate;
- run the scenario in DevBench;
- repair deterministic failures.

The user should not need to manually operate CK unless the remaining decision is genuinely spatial/aesthetic.
