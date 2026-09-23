# Contradictions, revisions, and epistemic conflicts

Continuity: `tes.mod.wheels-of-lull`

## Apparent Fyr -> Archeron

Early Brass Forest material presents NPC form `0500592E` as Divayth Fyr. Later:

- `INFO 0503E18F` has Archeron explicitly say he disguised himself as Fyr.
- MQ06 quest narration revises the player's understanding.
- `SCEN 0503E180` carries separate actor aliases/forms for the reveal.

**Resolution:** retain pre-reveal "Fyr" lines as the Fyr persona/apparent Fyr. Do not silently attribute them to the canonical Divayth Fyr after the reveal.

## Numinar's saboteur accusation

Numinar's evidence leads him to accuse the player. Yagrum's trace correctly narrows the saboteur to a recent outsider without fabricant signatures, but Archeron's disguise means Numinar chooses the wrong outsider.

**Resolution:** Numinar's accusation is a story-state conclusion superseded by the Archeron reveal, not a contradiction to delete.

## Hammar versus Yagrum on the Dwemer disappearance

Hammar confidently says the Dwemer merged into Numidium. Yagrum, a Dwemer witness absent during Red Mountain, explicitly says he does not know for sure what happened.

**Resolution:** store this as an epistemic conflict. Hammar provides a theory; Yagrum preserves uncertainty. Do not use Hammar's confidence to erase Yagrum's stated lack of knowledge.

## Shared voices are not shared identities

Several voice types are reused:

- Archeron / apparent Fyr.
- Watchman-215 / Cartwright / Analyst.
- Belarus / Second Atlantan.
- Masscroft / Yagrum / Thalmor Experiment forms.
- female guard / mining guards.
- FRF proxy roles.

**Resolution:** use direct GetIsID/GetIsAliasRef/SCEN evidence where available; otherwise preserve candidate sets.

## Wailway history versus Wailway literature

The locomotive gives first-person testimony about the Diolkos and its transformation. *Thomas the Screaming Tank Engine...* is framed as a fairy-tale/satirical source.

**Resolution:** the literary text can corroborate cultural awareness of Wailways but does not override the witness layer.

## Forged Thalmor Orders

The source title itself says the orders are forged.

**Resolution:** useful evidence for a forgery existing in the plot, not evidence that Elenwen or the Thalmor actually issued the contents.

## Prophecy and external apocrypha

Memory and Llavados reference Landfall, c0da, Digitals, and related motifs that also occur in other mod/apocryphal continuities.

**Resolution:** do not merge continuities because vocabulary overlaps. Crosslink by provenance; require explicit evidence before treating separate uses as the same event/model.
