# Contextual speaker-role index

This index covers positive Subject-level faction conditions found in Dealing with Daedra INFO records.

The faction condition identifies a **role/class of possible speakers**, not necessarily one individual.

| Faction/FormID | Resolved role | Conditioned INFO count | Main use |
|---|---|---:|---|
| 0005C84E | Current Follower | 47 | custom hireling/follower interaction and location commentary |
| 00050922 | Steward | 11 | School of Julianos hold-record collection; Riften influence branch |
| 000BCC9A | Potential Hireling | 8 | hireling recruitment/rehire dialogue |
| 000B3292 | Vigilants of Stendarr | 6 | Book-of-Curses confession/penance, Toruld logistics, recruitment |
| 0005091D | Blacksmith | 6 | construction-material services |
| 0597F36F | dealsexilevendorfaction2 / exile-selling-candles role | 6 | precursor occult mage/candle merchant history |
| 0401DC61 | Dragonborn-master faction; context = Frostmoon/Hircine werewolf role | 5 | Solstheim wolf/bear Great Hunt branch |
| 05641FF9 | dealscavesyndiefaction | 3 | restricted Syndicate operation guards |
| 056DAF95 | dealsfleshraidingfaction | 3 | Family/Kolskeggr raid participants |
| 0005091C | Apothecary | 2 | Mageblight outbreak/cure witnesses |
| 040195AD | Raven Rock Guard | 2 | High Tide/captain complaint and Veleth pointer |
| 00089977 | Kynesgrove Braidwood Innkeeper role | 2 | local researcher/fishing-shack pointer |
| 00050920 | Jarl | 1 | School archive record handoff |
| 000BD738 | Current Hireling | 1 | hireling autobiographical conversation gate |
| 000F8A5F | Morthal Jarl role | 1 | covert Alva-house investigation permission |
| 000656EA | Markarth Temple of Dibella | 1 | distinguishes temple from southern "fine establishment" |
| 00035D42 | Riverwood Trader | 1 | delivery handoff |
| 0005091B | Innkeeper | 1 | bank/safe-storage pointer |
| 00060028 | Beggar | 1 | generic identity branch |

## Policy

When a role-conditioned INFO lacks a unique positive Subject GetIsID:
- cite the role/faction as speaker;
- do not assign it to a named NPC based solely on proximity;
- named attribution may be added later only when quest aliases, scene ownership, voice files, or another deterministic source resolves it.

The Dragonborn-master FormID 0401DC61 is retained by ID because the exact master editor ID is not present in the Dealing with Daedra plugin; its Frostmoon/Hircine role is established by the dialogue context.
