# Decoder Schema Provenance

Raw plugin bytes remain canonical evidence. Exact field projections are added only when backed by a stable record definition.

Current schema references:

- xEdit TES5 definitions, branch dev-4.1.6
- Core/wbDefinitionsTES5.pas
- Core/wbDefinitionsCommon.pas
- https://github.com/TES5Edit/TES5Edit/blob/dev-4.1.6/Core/wbDefinitionsTES5.pas
- https://github.com/TES5Edit/TES5Edit/blob/dev-4.1.6/Core/wbDefinitionsCommon.pas

## MGEF / DATA

All 1,648 152-byte MGEF DATA blocks decode successfully, including flags, base cost, magic skill/resistance, minimum skill, archetype, actor values, casting/delivery, taper data, references, dual-cast data, skill-use multiplier, and script AI values.

## CTDA

All 8,229 32-byte conditions decode successfully. The projection retains comparison operators/flags, values or globals, function IDs/names, parameter types/values/references, run-on mode/reference, parameter 3, and CIS strings.

## PERK effects

All 625 perks and 1,006 effect entries decode successfully:

- PRKE effect type/rank/priority
- quest/stage effects
- ability effects
- entry-point ID/function
- condition-tab structure
- EPFT/EPFD parameters
- actor-value parameters
- spell/leveled-list parameters
- PRKC-scoped conditions
- EPF3 script flags/fragment indexes

No semantic decoder deletes or replaces the underlying raw subrecord payload.
