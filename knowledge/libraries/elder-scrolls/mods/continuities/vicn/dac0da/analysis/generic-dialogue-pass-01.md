# DAc0da Generic Dialogue pass 01

**Quest:** `DAc0da.esm:00491D` / `zDcdGen` — Generic Dialogue  
**Continuity:** `tes.mod.vicn.dac0da`

The generic-dialogue quest is not merely combat filler. It contains two unique dialogue branches plus voice-type-gated cultural combat lines.

## Unique speaker: Crabbimarco

INFO conditions resolve the Crabbimarco branches to:

- `DAc0da.esm:0048A0` / `zDcdUqKannimarco`
- FULL: **Crabbimarco**

High-value material:

- claims to be the strongest necromancer in Lyg;
- describes duel with sea-cucumber mage **Anus Falerion**;
- says Grabbers stole the name of the King of Dreugh from his memory;
- names **Xero-Lyg** and her son in a slave revolt;
- says he is unstable but will eventually be attached to this kalpa.

Evidence: `004925`, `004928`, `00492C`.

## Unique speaker: Mecha-Kanra

INFO conditions resolve the Kanra branch to:

- `DAc0da.esm:00D024` / `zDcdDweKanra`
- FULL: **Mecha-Kanra**

High-value material:

- "Uncle Yagrum" as Kagrenac's apprentice;
- Sotha Sil sent Kanra to inspect the Prisoner's memory modules;
- **Brain-Billies** are spirits that sting memories so forgotten things return;
- "1 and 1 equal 11."

Evidence: `00D04E`, `00D051`, `00D053`, `00D056`.

## Voice-type-gated cultural barks

Other INFO records are gated by shared voice types rather than one unique named actor.

### Atmoran/Yngol voice family

Lines invoke:

- Kyne's frozen tears;
- the Owl;
- Mother Moth;
- Goat That Walks Upright;
- Ysmir the Forefather;
- Ysgramor and his companions;
- Tsun;
- Harakk;
- the Serpent.

These are useful cultural-vocabulary seeds but should not be assigned wholesale to Yngol personally.

### Hahd/Dreugh voice family

Lines invoke:

- Maztiak;
- Mankar-hul;
- Black Star;
- Djaf;
- the hero Dervish;
- the sea remembering defeat.

These corroborate the Hahd vocabulary from Yu'qbar while remaining generic Templar/Dreugh combat speech.

### Arcanist voice family

Lines invoke:

- Mora's many eyes;
- fate/divergence points;
- enlightenment/progress;
- intellect;
- choice;
- tea.

These are generic Arcanist voice-family barks and should not automatically be quoted as the unique boss Arcanist's biography.

## Evidence rule

For `zDcdGen`:

- unique actor CTDA -> character-specific evidence;
- voice-type CTDA -> culture/faction/archetype evidence;
- combat/death bark alone -> low-weight semantic evidence unless reinforced elsewhere.
