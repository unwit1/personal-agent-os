# powerofthree's Papyrus Extender — v6.5.2 Provider Manifest

Snapshot date: 2026-09-24
Release: `v6.5.2`
Published: 2026-09-05
Upstream: `powerof3/PapyrusExtenderSSE`
README blob: `297a3129f6a4903ee4e2843dcc02a19d3e411c95`
Manager blob: `87ae9722db593307f7e06c0760d8ca9ad0395923`
ObjectTypes blob: `b193da04325a16ec9bb64ac255819b542bd5c61e`
Status: pinned provider snapshot

## Upstream advertised surface

The v6.5.2 README describes the plugin as an SKSE64/VR plugin with:

- **374 functions**;
- **37 events**;
- **4 script objects**.

User requirements listed upstream:
- Address Library for SKSE for SSE/AE;
- VR Address Library for SKSEVR for VR.

## Papyrus source files

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

## Native binding architecture

`src/Papyrus/Manager.cpp` binds the function/event modules below:

- `Papyrus/Functions/ActiveMagicEffect/Events.h`
- `Papyrus/Functions/ActiveMagicEffect/Functions.h`
- `Papyrus/Functions/Actor.h`
- `Papyrus/Functions/ActorBase.h`
- `Papyrus/Functions/Alias/Events.h`
- `Papyrus/Functions/Alias/Functions.h`
- `Papyrus/Functions/Ammo.h`
- `Papyrus/Functions/ArmorAddon.h`
- `Papyrus/Functions/Array.h`
- `Papyrus/Functions/Book.h`
- `Papyrus/Functions/Cell.h`
- `Papyrus/Functions/Debug.h`
- `Papyrus/Functions/Detection.h`
- `Papyrus/Functions/EffectShader.h`
- `Papyrus/Functions/Enchantment.h`
- `Papyrus/Functions/Faction.h`
- `Papyrus/Functions/Form/Events.h`
- `Papyrus/Functions/Form/Functions.h`
- `Papyrus/Functions/Furniture.h`
- `Papyrus/Functions/Game.h`
- `Papyrus/Functions/Graphics.h`
- `Papyrus/Functions/Hazard.h`
- `Papyrus/Functions/Idle.h`
- `Papyrus/Functions/LeveledList.h`
- `Papyrus/Functions/Light.h`
- `Papyrus/Functions/Location.h`
- `Papyrus/Functions/MagicEffect.h`
- `Papyrus/Functions/ObjectReference.h`
- `Papyrus/Functions/Package.h`
- `Papyrus/Functions/Potion.h`
- `Papyrus/Functions/Projectile.h`
- `Papyrus/Functions/Quest.h`
- `Papyrus/Functions/Scene.h`
- `Papyrus/Functions/Scroll.h`
- `Papyrus/Functions/Sound.h`
- `Papyrus/Functions/Spell.h`
- `Papyrus/Functions/Strings.h`
- `Papyrus/Functions/UI.h`
- `Papyrus/Functions/Utility.h`
- `Papyrus/Functions/VisualEffect.h`
- `Papyrus/Functions/Weather.h`

## Added Papyrus object types

`src/Papyrus/ObjectTypes.cpp` extends four native FormTypes into Papyrus script object types:

| Native FormType | Papyrus script object |
|---|---|
| FootstepSet | `FootstepSet` |
| LightingMaster | `LightingTemplate` |
| Debris | `Debris` |
| MaterialObject | `MaterialObject` |

These correspond to the four PSC files whose purpose is type exposure rather than a large function body.

## Count semantics

Do not collapse these counts into one number:

- **README advertised functions**: product-facing current surface claim.
- **PSC declarations**: declarations present in source, including deprecated compatibility functions.
- **C++ registered functions**: functions actually bound by the native plugin.
- **event registration functions**: Register/Unregister helpers are functions but serve the event system.
- **script objects**: added Papyrus-native types, not ordinary functions.

The source snapshot should be re-counted from the C++ Bind calls if an exact runtime registration total is needed.

## Version policy

Pin facts to v6.5.2. Future releases should be diffed by:
- PSC declaration;
- C++ registration;
- event name/signature;
- object type;
- runtime support;
- Address Library/VR requirements.
