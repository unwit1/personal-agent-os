# Eraamion

Form ID: `0534DF62`
Editor ID: `dealsmagevendor`
Continuity: `tes.mod.dealing-with-daedra`
Primary hub: Witch-Hunter's Guild

Eraamion is an Altmer member of the College of Winterhold who specializes in wards, magic cancellation, and anti-magic, but works with the Witch-Hunter's Guild because hunting rogue warlocks pays better.

This dossier is based on six explicitly resolved INFO records plus the implementation of the Recall scroll he distributes.

## Mysticism / anti-magic theory

Eraamion describes **Anti-Magic** as a subset of the old Mysticism school, with Mysticism defined as manipulation of Magicka itself.

His historical model is:

- Mysticism was pioneered in Alinor by the Psijics and associated with the "Old Way".
- The Psijics withdrew from ordinary recruitment after political problems and wayward pupils such as Mannimarco, then disappeared.
- Other magical traditions gradually absorbed pieces of Mysticism:
  - wards into Restoration;
  - shock magic into Destruction;
  - soul trapping into Conjuration.
- spatial-temporal manipulation also belongs to Mysticism;
- true temporal-control knowledge is now lost;
- Mark and Recall survive as usable techniques.

These statements are Eraamion's scholarly model, not neutral adjudication of Elder Scrolls magical taxonomy.

## Recall business

Eraamion refuses to sell Mark/Recall spell tomes because repeat scroll sales finance his research.

He recommends Recall as emergency insurance for hunters trapped in crypts or cornered by werewolves.

For hunters who cannot afford his normal scrolls, he offers a "free" version whose destination was selected by a Dunmer associate.

He explicitly warns the player to read House Dres history if they do not understand the implication, says "they will probably let you go eventually", and elsewhere says he receives a substantial cut whenever someone uses one of these free scrolls.

## Implementation confirms deliberate trafficking

Both INFO `059BC98E` and `059BC98F` directly add **SCRL 059BC982**, `dealsrecallscroll`.

That scroll uses MGEF `059BC97E`, `dealsinitialiseslaveryefferecall`, running `dealsrecallscrollsc`.

The script:
- shows recall/transition messages;
- moves the player to `traffickplayermarkerwhoreroom`;
- removes all player inventory into trafficking storage;
- resets trafficking debt/track globals;
- enables and positions the trafficking Madam;
- enters the same slave-brothel sequence documented elsewhere in this continuity.

Eraamion therefore knowingly monetizes a House-Dres-coded trafficking trap while framing it as emergency magical assistance.

This is direct implementation evidence plus explicit character admission, not inference from an unfortunate teleport destination.
