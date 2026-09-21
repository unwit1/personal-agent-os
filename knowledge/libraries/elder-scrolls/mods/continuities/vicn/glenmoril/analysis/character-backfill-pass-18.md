# Character backfill pass 18

This pass closes several character-page gaps left by the earlier quest-first ingestion.

Added/normalized:
- Hela the Druidess
- Ulrik
- Forgotten Vessel / Jhunal
- Wise Woman Tabiah
- Magni the Iron Fist
- Anem

The most important structural finding is the **Forgotten Vessel/Jhunal** record: the displayed name is Forgotten Vessel while the EDID explicitly contains Jhunal, and St. Bazura dialogue independently raises Jhunal alongside an inability of others to remember him.

Anem is deliberately represented as two source records rather than silently merged, because the ESM contains both **Anem, Witch of the Cradle** and **Anem of the Uterine Sea**.

Next character work should be driven by deterministic INFO speaker resolution so relevance can be measured from actual spoken-line counts and quest/scene participation.
