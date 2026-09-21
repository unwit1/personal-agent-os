# Jyggalag and Greymarch in VIGILANT

Continuity: `tes.mod.vigilant`

## Official substrate

In *The Elder Scrolls IV: Shivering Isles*, Jyggalag is the Daedric Prince of Order who had been cursed by the other Princes to exist as Sheogorath. Once per era he emerged during the **Greymarch**, destroyed/reordered the Shivering Isles, and was then forced back into the Sheogorath identity.

At the end of that story, the Hero defeats Jyggalag and breaks the recurring curse. Jyggalag explicitly says he is now free to roam the voids of Oblivion.

This establishes two pieces of licensed substrate that VIGILANT uses:

1. Jyggalag is the Prince of Order associated with the Forces/Knights of Order and Greymarch.
2. By the Fourth Era, the old Jyggalag↔Sheogorath curse cycle has already been broken.

## VIGILANT continuation

In `zzzCHMQ00` / **Coldharbour**, Inquisitor Pepe describes Jyggalag as the Prince of Order whose immense power led the other Daedra to imprison/curse him with madness. Pepe then adds that **"some fool freed him"** and says Jyggalag is now marching through the VIGILANT wasteland.

That line is naturally compatible with the ending of *Shivering Isles*: VIGILANT is treating the released Jyggalag as an active independent Prince again.

### The new Greymarch

This is where VIGILANT becomes an extension rather than a retelling.

Pepe says an infinite Army of Order invaded decades earlier and conquered almost the entire continent/Empire represented in this Coldharbour layer. He describes a catastrophic **Battle of Weye**, a brilliant silver cocoon through which Jyggalag manifested, and an Order advance that leaves only the Imperial City region protected.

Molag Bal is said to consume souls to sustain a barrier against the Army of Order. The barrier is failing, and Pepe repeatedly warns that **Greymarch** will break through.

The ESM supports this as more than dialogue:

- `QUST 0213AEE3` — `zzzCHGreymarchQuest`
- `zzzCHMQ00` has a VMAD property pointing directly to the Greymarch quest.
- the main quest owns Order aliases, an Order target, an Order explosion, barrier/collision references, and an obelisk enabler.
- the Coldharbour topology contains a **Throne of Order** and a Silver Cocoon route.
- Order-aligned NPCs, bosses, cores, priests, knights, and summons are widespread in the plugin.

## What is licensed and what is VIGILANT-specific?

### Established TES tradition

- Jyggalag is the Daedric Prince of Order.
- the other Princes feared his power and cursed him into Sheogorath.
- the recurring Greymarch was the periodic return of Jyggalag and Forces of Order.
- the Hero of Kvatch broke the curse at the end of *Shivering Isles*, leaving Jyggalag free.

### VIGILANT extension

- Jyggalag using that freedom to invade **Coldharbour**.
- a decades-long Greymarch across VIGILANT's Coldharbour civilization.
- the Battle of Weye and the silver-cocoon manifestation described by Pepe.
- Molag Bal consuming souls to hold a barrier against Jyggalag.
- Order mining/singularity activity described by Saklas.
- the specific Silver Cocoon / Throne of Order geography and Act 4 war.

## Reliability

Pepe's history of the invasion is character testimony, though the ESM's extensive Order implementation strongly corroborates the **current conflict**. Exact historical details such as casualties, chronology, and the Battle of Weye still depend on testimony unless independently represented elsewhere.

Saklas adds that the Forces of Order are mining for something, that the process stopped in the First Era because of past Dragon Breaks, and that Jyggalag has not yet descended from his ship. Those metaphysical details remain Saklas's account.

## Evidence anchors

- `INFO 0212F2F9` — Pepe: Jyggalag's curse/freedom account.
- `INFO 0212F2F7` — Pepe: Army of Order, Battle of Weye, barrier, approaching Greymarch.
- `INFO 0212F2FB` — Pepe: silver cocoon/Jyggalag manifestation.
- `INFO 02130416` — Pepe: Order breaks the barrier / Greymarch begins.
- `INFO 02531D0F` — Saklas on Order mining and Jyggalag's library/ship.
- `QUST 0213AEE3` — Greymarch implementation quest.
- `QUST 0212F24E` — main Coldharbour quest and Order/Greymarch VMAD links.
- `CELL 02125B35` — Throne of Order.
- `CELL 02123F84` → `02125336` → `02253895` → `02125B35` — Silver Cocoon / Order traversal chain.

## Canon-comparison classification

**Jyggalag freed after the old Greymarch cycle:** established licensed continuation point.

**Jyggalag invading Coldharbour after his release:** VIGILANT-specific sequel/extension.

This distinction lets Lorekeeper use VIGILANT as a coherent post-*Shivering Isles* mod continuity without silently importing its Coldharbour war into Bethesda continuity.
