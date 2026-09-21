# Raw Clockwork corpus

These files are direct text extractions from the user-provided `Clockwork.esp` and are retained as source evidence for later Lorekeeper normalization.

- `dialogue-transcript.txt.gz` — gzip-compressed UTF-8 transcript containing all 520 extracted `NAM1` response strings from 888 `INFO` records, grouped beneath their 242 `DIAL` topic records.
- `quest-records.txt.gz` — gzip-compressed UTF-8 extraction of all 12 `QUST` records, including discovered objectives and journal-stage text.
- `record_counts.json` — plugin record inventory.

The gzip files are compressed only to keep the raw archival layer compact. They expand to ordinary UTF-8 `.txt` files and should be indexed after decompression. Speaker attribution, conditions, scene ownership, and master-record resolution remain a later normalization pass; the raw text itself is preserved here first.
