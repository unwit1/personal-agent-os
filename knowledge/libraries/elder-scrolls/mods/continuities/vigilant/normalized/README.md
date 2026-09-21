# VIGILANT normalization status

This layer records deterministic speaker/scene normalization performed directly against the user-provided `Vigilant.esm`.

## Dialogue coverage

- INFO records analyzed: **1,225**
- uniquely resolved to one NPC: **1,136** (**92.7%**)
- structurally ambiguous: **10**
- unresolved: **79**
- explicit INFO `ANAM` speakers: **26**
- subject `GetIsID` evidence: **308**
- subject `GetIsAliasRef` evidence: **702**
- subject `GetIsVoiceType` evidence: **12**
- INFO topics used by scenes: **202**

## Structural support

- **78** SCEN records parsed
- **225** SCEN dialogue actions parsed
- **550** quest aliases parsed across the 120 QUST records

Speaker resolution prioritizes explicit INFO speakers, positive subject conditions (`GetIsID`, `GetIsAliasRef`), and scene actor aliases. Voice/faction/class restrictions are used conservatively to narrow candidates. Multi-candidate results remain ambiguous rather than choosing a character from prose alone.

## Interpretation boundary

Record structure can establish that a character speaks a line, participates in a scene, or fills a quest role. It cannot by itself establish that the character's testimony is objectively true. This is especially important for VIGILANT's Coldharbour memories and its representations of Alessia, Pelinal, Morihaus, Marukh, Belharza, Lamae, and Molag Bal.

The remaining 89 ambiguous/unresolved records are retained as an explicit follow-up set rather than semantically guessed.
