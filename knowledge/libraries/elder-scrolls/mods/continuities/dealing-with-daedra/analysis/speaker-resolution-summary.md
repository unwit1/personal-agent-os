# Speaker resolution — pass 01

Method: an INFO record is assigned to an NPC only when it contains exactly one GetIsID CTDA condition that resolves to a known actor FormID.

Coverage:
- INFO records: 1,809 total
- Explicit single-NPC resolutions: 1,469
- Dialogue response strings: 2,674 total
- Responses covered by these resolutions: 2,188
- Approximate response coverage: 82%

High-volume resolved speakers include Grados, Thaer, the Herald, Beldam Annes, Lysara Carius, Sadren Sarethi, Talmeth Dres, Carsten, Arincine, the Hooded Figure associated with the Dagon cell, and Vigilant Toruld.

This is intentionally conservative. Records governed by aliases, quests, scenes, broad faction conditions, multiple candidate actors, or no explicit actor condition remain unresolved rather than being guessed.
