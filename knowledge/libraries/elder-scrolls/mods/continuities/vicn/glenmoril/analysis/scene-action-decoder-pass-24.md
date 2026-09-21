# Scene action decoder pass 24

The SCEN parser has now been narrowed from generic subrecord discovery to a normalized dialogue-action target.

## Validated behavior

For scene dialogue, the action's Actor ID is the associated quest's reference-alias ID. The quest alias is then filled by a forced reference, unique actor, external alias, conditions or another supported alias mechanism. INFO conditions remain active even after the scene actor has been identified. citeturn0search5

This means speaker resolution is a two-stage operation:

1. **Producer:** scene actor alias determines the actor/reference candidate.
2. **Filter:** INFO conditions determine whether a particular response is eligible.

This distinction prevents a common error: assigning every INFO beneath a scene DIAL to the alias actor without checking conditions.

## Raw parser target

The observed GLENMORIL action blocks contain sequences beginning with `ANAM` and commonly including `NAM0`, `ALID`, `INAM`, `SNAM`, and `ENAM`, with additional action-type-specific fields.

Rather than infer field semantics solely from byte position, the normalized layer records raw evidence alongside interpreted Actor ID and DIAL references.

## Dialogue preservation

The existing INFO→DIAL parent reconstruction remains valid, but final export must preserve effective INFO order. xEdit notes that response ordering affects which INFO the engine selects. citeturn0search2
