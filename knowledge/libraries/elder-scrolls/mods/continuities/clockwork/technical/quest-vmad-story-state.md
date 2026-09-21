# Quest VMAD story-state wiring

Continuity: `tes.mod.clockwork`

Quest fragments expose runtime state that the journal does not spell out. This layer is deliberately technical: it records which quest owns which trigger, global, alias, scene, door, collision, or enable parent.

## Foot Of The Mountain

The quest fragment directly references:
- the **Velothi Mountain Tunnels** map marker (`0505FC3A`);
- a stage-40 trigger (`050632CB`);
- Isidor as alias 8.

This confirms that Isidor is part of the runtime quest structure, not only the addressee of Camilla's notes.

## Shadow Under The Mountain

The quest directly references `CLWRandomQuakeActive01GLOB`, the tunnel door alias, and the escape marker. The cave-in/escape sequence is therefore coupled to explicit environmental-state control rather than being journal-only narration.

## Steam-Powered

The quest fragment owns the mod's first major systems-state transition:

- ten pipe aliases (`Pipe01`–`Pipe10`);
- `CLWSQ02Machines01EnableParentREF` for castle machinery;
- a stage-controlled light enable parent;
- a siren reference;
- Travel Machine recall/autoload state;
- the collision and trigger used by the can't-leave sequence;
- Shadow plus multiple Shadow/Lamashtu stage markers;
- door references connecting most major castle rooms.

The journal says “repair steam power”; the VMAD wiring shows that this quest is literally the state coordinator for reactivating the castle.

## Crystalline Heart

The fragment exposes:
- `CLWSQ03LamCrazed01GLOB` for Lamashtu's impaired state;
- the speaker-horn trigger network;
- Amalgam encounter enablement;
- the lever, lever base, lever handle, and heart aliases;
- two Lamashtu-heart aliases;
- inactive-Lamashtu enable parents;
- the stage-140 heart-transfer scene;
- music-box references used during the search.

This makes Lamashtu's breakdown/heart replacement a concrete state-machine transition, not only a dialogue event.

## I Against I

The final quest owns:
- a concrete Shadow ambush actor;
- Shadow aliases and stage markers;
- mausoleum and Animoculotory sirens;
- two Animoculotory portcullis/trap linkers plus stage-40 collision;
- the same can't-leave collision/trigger used by the earlier Travel Machine sequence;
- the Travel Room portal/door reference;
- a post-quest dress enable parent;
- references back to the heart-transfer apparatus.

The reuse of the can't-leave trigger/collision is especially useful: the quest that resolves Shadow also directly owns the infrastructure that previously enforced the player's inability to leave.

## MCM / configurable state

The MCM quest exposes globals for:
- fast-travel checks;
- garden respawn settings;
- Gilded downed/reanimation settings.

Those are implementation/configuration features. They are relevant for technical mod analysis but should not be read as in-world lore.

## Retrieval rule

VMAD evidence is excellent for questions such as “what actually controls this event?” or “is this behavior scripted?” It is secondary support for lore questions and must not override dialogue/book provenance.
