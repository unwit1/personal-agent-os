# Clockwork Castle service-state map

Continuity: `tes.mod.clockwork`

Clockwork Castle does not become fully functional in one step. Dialogue conditions, globals, quest stages, enable refs, and optional upgrade wiring define a sequence of increasingly capable home states.

## State 0 — stranded / machinery unavailable

Before `CLWSQ02Machines01GLOB` reaches the restored state, Lahar says:

- the Travel Machine cannot be used for outside supply runs,
- additional food/supplies cannot be procured,
- the Glass Garden will not grow in the cold,
- damaged/unsafe castle systems remain unavailable.

Relevant dialogue: `INFO 052D78B4`, `052D78B5`, `052D78CD`, `052EBD5B`.

The pre/post dialogue variants explicitly test `GLOB 052A9E1F` / `CLWSQ02Machines01GLOB` against value 1.

## State 1 — steam and core domestic systems restored

At *Steam-Powered* stage 110, Lahar force-greets the player in `INFO 054E8522` and reports several changes as one restoration milestone:

- he has used the Travel Machine to obtain outside supplies,
- food has been laid out for the player,
- merchant trading can now be arranged,
- exhaust fans make the Work Room safe,
- dangerous material has been cleared from the Work Room,
- the Glass Garden has been replanted with useful alchemical plants,
- the Travel Machine is mechanically usable again.

After stage 120, `INFO 054ED63A` exposes the direct trade service.

This state is specifically **mechanical/domestic restoration**. It does not solve the player's Shadow-based inability to leave; the main quest immediately distinguishes those two problems.

## Trade and investment

Lahar's trade dialogue becomes available at/after *Steam-Powered* stage 120.

An investment topic (`INFO 054F2750`) additionally requires:
- stage ≥ 120,
- the vanilla Investor perk,
- at least 500 gold,
- the Lahar investment global `054F274D` / `CLWPerkInvestorLahar` at its configured pre-investment value.

The record proves an investment-capable merchant path exists. Lorekeeper should not invent merchant-stock details unless inventory/faction/container records are separately mapped.

## State 2 — Mage's Study restored after Crystalline Heart

After *Crystalline Heart* progresses beyond stage 150, Lahar's one-shot end comment (`INFO 056985DB`–`056985E1`) reports:

- replacement glasswork was found,
- the **Alchemy** and **Enchanting** stations in the Mage's Study were repaired,
- Glass Garden regrowth is far enough along that harvest may be possible.

The dialogue is gated by `GLOB 056985D6` / `CLWSQ03EndLaharCommentGLOB`; the final dialogue fragment references that global, supporting one-time delivery of the restoration update.

## State 3 — post-I Against I Armoury/memento system

After *I Against I* stage 200, `INFO 0579C7AA` tells the player that Lahar can begin adding mementos of the player's achievements to the Armoury.

The line is gated by:
- `GetStageDone(0508DA63, 200)`
- `GLOB 057B0BFF` / `CLWLaharPostQuestArmouryLine01GLOB = 0`

Its result fragment references that global, again supporting a one-shot post-quest unlock announcement.

This establishes a post-main-quest **museum/memento role** for the Armoury without yet cataloging every possible display.

## Optional upgrade — Staff Enchanter and blank-staff trade

The *Staff Enchanting* side quest adds a separate optional upgrade:

- 1 Heart Stone
- 3 empty Greater Soul Gems
- Staff Enchanter enable ref `050299D9` in the Mage's Study
- blank-staff state global `057A69D1` / `CLWLaharBlankStaffSpawn01`

The delivery fragment explicitly references both the station and blank-staff global. Lahar's dialogue states that blank-staff trades can be arranged afterward.

See `../events/optional-quest-runtime.md`.

## State-machine interpretation

A useful Lorekeeper abstraction is:

1. **Trapped/underpowered castle**
2. **Steam restored:** Travel Machine hardware, supplies, trading, Work Room, Glass Garden
3. **Lamashtu restored:** Mage's Study Alchemy/Enchanting stations repaired; garden mature
4. **Shadow resolved:** Armoury achievement mementos begin
5. **Optional upgrade:** Staff Enchanter + blank-staff supply path

These states should be used for spoiler-aware retrieval and home-function questions. They are not separate historical eras; they are player-progression-dependent castle states.
