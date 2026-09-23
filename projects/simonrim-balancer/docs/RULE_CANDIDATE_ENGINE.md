# Rule Candidate Engine

The Simonrim Balancer separates observed implementation facts from reviewed design rules.

## Stages

1. **Raw evidence** — plugin bytes, source text, configs, installer metadata.
2. **Decoded evidence** — typed records, conditions, script properties, deltas and relationships.
3. **Observed pattern** — repeated implementation profile with an explicit scope and sample count.
4. **Rule candidate** — a review unit that proposes a possible design convention and carries provenance, confidence and contamination metadata.
5. **Approved rule** — a human-reviewed convention with explicit scope, exceptions and evidence. The current corpus contains zero approved rules.

## Candidate requirements

Each candidate stores:

- stable candidate ID;
- domain and source kind;
- plugin/mod scope;
- module roles;
- proposition;
- sample count;
- evidence IDs / evidence basis;
- baseline availability;
- counterexample or alternative-profile status;
- optional/reversion/compatibility contamination flags;
- confidence score and label;
- review status;
- rule-approval flag.

## Guardrails

- A repeated value is not automatically a design law.
- Main-file evidence is favored over optional/reversion/compatibility modules.
- Reversion descriptions may provide strong evidence about the behavior they revert, but still require implementation corroboration.
- Missing Skyrim/DLC baselines reduce confidence instead of being guessed.
- AVIF graphical edges are not perk prerequisites; PERK CTDA is authoritative for gating.
- Presentation-only records cannot independently create balance rules.
- Candidate promotion must check counterexamples, exceptions, version scope and module contamination.
- `approved_rule` remains false until a review process explicitly promotes a candidate.

## Initial candidate corpus

The first deterministic pass creates candidates from:

- recurring spell numeric profiles;
- recurring perk entry-point profiles;
- weapon numeric profiles;
- enchantment numeric profiles;
- combat-style profiles;
- movement profiles;
- projectile/explosion/hazard delivery profiles;
- explicit FOMOD design statements.

Further passes can attach corroborating deltas, Papyrus behavior, runtime configuration, and prerequisite/tree topology evidence to existing candidates instead of creating duplicate rules.
