# Ebonwall — Mq02 Generic dialogue

Quest: `Glenmoril.esm:00EDEA zzzGHMq02Gen`
Title: **Mq02 Generic**
Responses: **15 exact**

This small quest stores generic/post-Ebonwall dialogue that was missed by the sequential quest pass.

## Speaker totals

- Wise Woman Tabiah: 6
- Traitor: 3
- Cruviah: 3
- Ambarys: 3

## Tabiah

The sole SCEN record has **Tabiah singing/humming five lines**.

A separate generic hello response from Tabiah is silence:
> “................”

This fits the reduced/withdrawn state shown in the Embers branch without adding new interpretation.

## Traitor

A character named **Traitor** repeatedly insists:
- they are not evil;
- “that woman” is evil;
- the conflict was “just for that stone”;
- the Thalmor, Nords, and Dunmer are all evil;
- everyone else caused what happened.

The dialogue strongly belongs to the Ebonwall aftermath, but the exact identity of “that woman” and the Traitor's precise role should remain unresolved unless a direct record joins them.

## Cruviah

Cruviah says:
- “Alma belig. All like before. Os no cry.”
- “Os guard alma. Until all like before.”
- after receiving 30 gold: “Juohn. Juohn ascif.”

Keep this vocabulary untranslated unless the mod provides a glossary/context strong enough to resolve it.

## Ambarys

An external base-game speaker at FormID `0001413E` is used for three responses in the Grey Quarter branch.

The dialogue says:
- an old customer recently appeared and asked for help with a woman;
- the woman was drunk/in poor condition;
- people in the Grey Quarter are taking turns caring for her;
- with the child present, the woman may improve.

This reinforces the **Tabiah + Cruviah + Grey Quarter** Embers outcome.

Speaker resolution:
- SCEN Actor ID → quest alias for Tabiah scene rows.
- INFO `GetIsID` for Traitor, Cruviah, Tabiah, and the external Grey-Quarter speaker.
