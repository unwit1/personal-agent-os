# AVIF Perk-Tree / Actor-Value Decoder

## Scope

This checkpoint decodes all 25 supplied AVIF skill records and their repeated perk-tree sections.

Skill-wide evidence includes record-level skill category and AVSK progression coefficients. Node evidence includes perk FormID, raw flags, grid coordinates, fractional positions, owning skill, outgoing graphical connections, and node index.

## Results

- 25 / 25 AVIF records decoded; 0 failures.
- 297 perk-tree nodes, including 25 root placeholders.
- 283 directed graphical edges.
- 0 missing edge targets.
- 0 nodes unreachable from a root placeholder.
- 0 detected cycles.
- 18 Adamant main-tree records have external Skyrim.esm baselines not present here.
- 7 add-on records have exact imported Adamant baselines and deterministic graph deltas.

## Exact add-on delta summary

Every one of the seven exact-baseline add-on AVIF overrides changes its graph and adds at least one node. Four also remove at least one Adamant node.

- AdamantBlade: Two-handed adds 1 node / 1 edge; Block adds 1 node / 1 edge; Light Armor replaces one node/edge.
- AdamantCrossbows: Archery adds 2 nodes and 2 edges, removes 1 edge, and repositions one shared node.
- Hand to Hand: Pickpocket, Lockpicking, and Alteration substantially rewrite their trees. Pickpocket changes Skill Use Mult; Lockpicking changes all four AVSK skill-progression fields; Alteration leaves AVSK unchanged while adding/removing/repositioning nodes.

Exact canonical Form identities and edge differences are retained in the compact checkpoint and full local perk_tree_deltas.csv.

## Critical semantic distinction

**AVIF graph lines are not perk prerequisites.** Changing graphical connections does not itself change perk requirements. Actual prerequisite/gating logic lives in PERK CTDA conditions.

The architecture therefore stores UI graph topology and prerequisite logic as separate evidence layers. A future progression model should overlay decoded PERK conditions onto the AVIF graph rather than treating graph adjacency as gameplay gating.

## Root placeholders

Every supplied tree contains a zero-PNAM root placeholder. Some root placeholder flag/grid values look like non-semantic legacy data. The decoder preserves those values but excludes root geometry from normal grid-bound calculations.

## Rule status

No AVIF layout or add-on delta is an approved Simonrim rule. These are deterministic implementation facts only.
