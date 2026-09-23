# Candidate Review Model

A Simonrim Balancer candidate is evaluated on separate axes.

## Evidence strength

**Question:** How well established is the scoped proposition in the supplied sources?

Evidence strength increases with repeated observations, exact typed profiles, direct author statements, and independent implementation corroboration. A high score can mean “this behavior definitely exists” without implying that it should be generalized.

## Generalizability

**Question:** How safe is it to infer a broader design convention from the scoped fact?

Generalizability is lower when evidence comes from optional modules, compatibility patches, reversion plugins, highly specific mechanics, incomplete external baselines, or a domain with many alternative profiles.

## Promotion readiness

Promotion readiness combines evidence strength and generalizability, then applies explicit risk penalties. It is a review-priority signal only. It never auto-promotes a rule.

Current corpus:

- 273 candidates.
- 38 have high evidence strength.
- 9 have medium generalizability; 264 remain low.
- 50 reach medium promotion readiness; 223 remain low.
- 38 are specifically **high-evidence / low-generalizability** cases.
- Approved rules remain 0.

This split prevents a common failure mode: treating a strongly demonstrated one-off or reversion behavior as a suite-wide design law.
