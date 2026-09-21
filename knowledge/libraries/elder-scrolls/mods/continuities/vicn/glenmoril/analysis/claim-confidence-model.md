# Claim confidence model

GLENMORIL ingestion should distinguish evidence strength from interpretive confidence.

## Evidence classes

**Direct structural**
Plugin record metadata, quest objectives, explicit parentage, EDIDs, record names.

**Direct textual**
A BOOK or INFO response explicitly states the proposition.

**Attributed textual**
A character or author states a proposition about the world; reliable as evidence of what that speaker believes/says, not automatically of objective truth.

**Cross-record inference**
Multiple records jointly support a relationship that no single record states completely.

**Interpretive hypothesis**
A thematic or symbolic identification suggested by evidence but not established.

## Example

- “Yelem says the first Great Cat was a Rolly-Polly” → direct textual / high confidence.
- “Great Cat and Rolly-Polly are related concepts in Yelem's model” → cross-record synthesis / high confidence.
- “Rolly-Polly is Shezarr” → interpretive hypothesis; do not promote.
- “Ja'cobee's EGG and Yelem's Egg are identical” → unresolved hypothesis; do not promote.

This model should be reusable across Vicn continuity ingestion.
