# AI Micro-Optimization Registry

These records capture implementation-level knobs that are easy to lose inside prose.

A micro-optimization is not presumed beneficial. Each item contains:
- the exact optimization;
- the mechanism it is intended to change;
- expected effect;
- a minimal A/B or invariant test;
- failure mode;
- prerequisites;
- evidence/source references;
- adoption tier.

Provider-specific knobs remain explicitly provider-scoped. They must not become global Agent OS assumptions.

Adoption tiers:
- `default_candidate` — broadly sensible, still regression-tested;
- `measure_first` — useful only if a local bottleneck exists;
- `provider_specific` — adapter-level optimization;
- `research_only` — experimental;
- `anti_pattern_check` — detect and remove this behavior.

The registry is deliberately redundant with some higher-level AIT entries: the AIT catalog captures concepts, while this registry captures implementation knobs that an optimizer can directly test.
