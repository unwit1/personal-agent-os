# The Agent

**Continuity:** `tes.mod.vicn.dac0da`  
**Status:** structural multi-form dossier

DAc0da uses several closely related NPC forms under the **Agent** identity/role during **The Sea of Causality**.

## Shared base/template

`DAc0da.esm:0043F6`

- Editor ID: `zDcdBossCyborgAgent01`
- FULL: **Yaghra Chimera - The Agent**
- short name: **The Agent**

This is the common template behind later Agent forms.

## Ambient bioborg form

`DAc0da.esm:00458C`

- Editor ID: `zDcdUqCyborgAgent`
- FULL: **Yaghra Bioborg - The Agent**
- template: `zDcdBossCyborgAgent01`

This actor is bound to the support quest **Agent Event**, where it:

- feeds at a dedicated Dreugh/feeding marker;
- notices the player;
- retreats.

See `technical/agent-event.md`.

## MQ01 boss/encounter form

`DAc0da.esm:004410`

- Editor ID: `zDcdBossCyborgAgent02`
- FULL: **The Agent**
- template: `zDcdBossCyborgAgent01`

MQ01 alias 9, `Agent`, points directly to this form.

## Interpretation

Because both the bioborg and boss forms derive from the same **Yaghra Chimera - The Agent** template and occupy coordinated MQ01/support-quest roles, they should be retrieved as **states/forms of one Agent encounter identity**.

The ESM structure does not by itself establish whether this represents:

- literal metamorphosis of one individual;
- cloned/instantiated bodies;
- multiple equivalent Agent bodies;
- or another Sload/Yaghra reconstruction process.

That mechanism remains open until scripts/scenes or explicit dialogue resolve it.

The broader DAc0da corpus's use of **Agent** and **Prisoner** terminology should also remain distinct: this Yaghra/cyborg Agent is a concrete MQ01 encounter actor, while MQ04/Ghost Choir material uses "Agent" in a wider Daggerfall/possibility/Prisoner context.
