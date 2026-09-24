# powerofthree Papyrus Extender Provider Manifest

Snapshot date: 2026-09-24
Upstream: `powerof3/PapyrusExtenderSSE`
Source directory: `Papyrus/Source/scripts/`
PSC files: 8
Status: provider manifest

## Source files

| PSC | Blob SHA |
|---|---|
| `Debris.psc` | `13e8cdba871e316bcbc3e77bcc0c34197e8c6a77` |
| `FootstepSet.psc` | `9ac46dc3cbcf265a1f5c7b176bbf157f50657ad4` |
| `LightingTemplate.psc` | `422342b36d0e829e82321e8779bf5e1c4ce67c4f` |
| `MaterialObject.psc` | `d289af8cef6492a608f8bb0d4032af011d03a386` |
| `PO3_Events_Alias.psc` | `84c66be7d52c1a156ff43521f2bd31ce3c3f3eee` |
| `PO3_Events_AME.psc` | `1c7690d0404e5f0cff5475a25955522106efdfe4` |
| `PO3_Events_Form.psc` | `ec1cbca8a226177d72c70a22642e4f1080275e17` |
| `PO3_SKSEFunctions.psc` | `87fcdd7c399801c92449c59ddb46090b2cc93214` |

## Provider structure

Four source files define Form-derived script object types:
- `Debris.psc`
- `FootstepSet.psc`
- `LightingTemplate.psc`
- `MaterialObject.psc`

The main callable API surface is `PO3_SKSEFunctions.psc`. Event registration/callback surfaces are split by receiver family:
- `PO3_Events_Form.psc`
- `PO3_Events_Alias.psc`
- `PO3_Events_AME.psc`

## Promotion rule

Use exact declaration/provider/version provenance. Do not describe a po3 function as vanilla SKSE or vanilla Papyrus merely because its signature resembles an engine API.

## Source-count reconciliation

At the 2026-09-24 master snapshot:
- upstream README blob `297a3129f6a4903ee4e2843dcc02a19d3e411c95` states **374 functions, 37 events, and 4 script objects**;
- `PO3_SKSEFunctions.psc` blob `87fcdd7c399801c92449c59ddb46090b2cc93214` contains **379 unique function declarations**;
- all 379 are declared `global native`;
- no duplicate function names were found;
- the three event receiver scripts expose 111 callback declarations = 37 logical event names × three receiver families.

Treat the README's 374 as a documentation-summary value that lags or uses a different counting scope unless the upstream project clarifies otherwise. The source declaration count is canonical for this exact blob snapshot.
