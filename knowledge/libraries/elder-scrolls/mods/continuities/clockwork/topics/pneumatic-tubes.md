# Pneumatic tube system

Continuity: `tes.mod.clockwork`  
Topic type: castle technology

Ludwig builds a pressure-driven transport network through Clockwork Castle, inspired by the Travel Machine's transportation concept. Terminals move items quickly around the keep.

Lahar later uses and explains the system. In Ludwig's final years, its convenience also enables his isolation: food and books can reach his room without face-to-face contact.

## Core evidence

- `BOOK 05332EAA` — Ludwig designs/expands the pneumatic network in 4E 24.
- `INFO 05314725` — terminal receptacles, control columns, routing, sorting.
- `INFO 05347329` — Ludwig received food/books through the tubes after withdrawing.

## Exact implemented network

The ESP contains `Pneumatic Tube Receptacle` endpoints in the Mage's Study, Work Room, Hall/Kitchen, Travel Room, Armoury, and Master Bedroom. VMAD on the placed controls names the source and destination receptacles directly.

The active network supports room-to-room transfer plus filtered sorting. Local station scripts separately sort alchemical ingredients, soul gems, food, books, and smithing materials into specialized storage. The Master Bedroom terminal is intentionally broken: it still points toward the Hall/Kitchen receptacle, but its placed script replaces the live machinery-state check with a constant-zero global and a broken-button message.

The remote network is gated by the same `CLWSQ02Machines01GLOB` machinery state used by the restored castle systems.

See `../technical/pneumatic-network.md` for exact receptacle refs and routing edges.
