# Dialogue field validation

Fields to preserve in the deterministic export:

- DIAL FormID / EDID
- INFO FormID / EDID
- response text
- response number
- INFO conditions
- RNAM prompt override
- PNAM previous INFO
- original/effective order
- scene Actor ID
- quest alias resolution

Independent xEdit-based dialogue exporters expose INFO conditions and RNAM because they materially affect dialogue selection/presentation. xEdit documentation also states that INFO ordering is significant to engine selection.

This validates the corpus design before bulk extraction.
