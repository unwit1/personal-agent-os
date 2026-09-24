# RaceMenu / SKEE NiOverride and CharGen Papyrus API Catalog

Imported: 2026-09-24
Pinned source commit: `9ebcb733e17be695f994cd2e9cc383043446bc02`
Source version marker: 0.4.19.17
Status: source-derived native registration catalog

## Counts

- NiOverride registrations: **175**
- CharGen registrations: **13**

## NiOverride

| Line | Function |
|---:|---|
| 1831 | `GetNumBodyOverlays` |
| 1834 | `GetNumHandOverlays` |
| 1837 | `GetNumFeetOverlays` |
| 1840 | `GetNumFaceOverlays` |
| 1844 | `GetNumSpellBodyOverlays` |
| 1847 | `GetNumSpellHandOverlays` |
| 1850 | `GetNumSpellFeetOverlays` |
| 1853 | `GetNumSpellFaceOverlays` |
| 1858 | `AddOverlays` |
| 1861 | `HasOverlays` |
| 1864 | `RemoveOverlays` |
| 1867 | `RevertOverlays` |
| 1870 | `RevertOverlay` |
| 1873 | `RevertHeadOverlays` |
| 1876 | `RevertHeadOverlay` |
| 1881 | `HasOverride` |
| 1884 | `AddOverrideFloat` |
| 1887 | `AddOverrideInt` |
| 1890 | `AddOverrideBool` |
| 1893 | `AddOverrideString` |
| 1896 | `AddOverrideTextureSet` |
| 1899 | `ApplyOverrides` |
| 1902 | `HasArmorAddonNode` |
| 1906 | `GetOverrideFloat` |
| 1909 | `GetOverrideInt` |
| 1912 | `GetOverrideBool` |
| 1915 | `GetOverrideString` |
| 1918 | `GetOverrideTextureSet` |
| 1922 | `GetPropertyFloat` |
| 1925 | `GetPropertyInt` |
| 1928 | `GetPropertyBool` |
| 1931 | `GetPropertyString` |
| 1935 | `HasNodeOverride` |
| 1938 | `AddNodeOverrideFloat` |
| 1941 | `AddNodeOverrideInt` |
| 1944 | `AddNodeOverrideBool` |
| 1947 | `AddNodeOverrideString` |
| 1950 | `AddNodeOverrideTextureSet` |
| 1953 | `ApplyNodeOverrides` |
| 1957 | `GetNodeOverrideFloat` |
| 1960 | `GetNodeOverrideInt` |
| 1963 | `GetNodeOverrideBool` |
| 1966 | `GetNodeOverrideString` |
| 1969 | `GetNodeOverrideTextureSet` |
| 1973 | `GetNodePropertyFloat` |
| 1976 | `GetNodePropertyInt` |
| 1979 | `GetNodePropertyBool` |
| 1982 | `GetNodePropertyString` |
| 1987 | `HasWeaponOverride` |
| 1990 | `AddWeaponOverrideFloat` |
| 1993 | `AddWeaponOverrideInt` |
| 1996 | `AddWeaponOverrideBool` |
| 1999 | `AddWeaponOverrideString` |
| 2002 | `AddWeaponOverrideTextureSet` |
| 2005 | `ApplyWeaponOverrides` |
| 2008 | `HasWeaponNode` |
| 2012 | `GetWeaponOverrideFloat` |
| 2015 | `GetWeaponOverrideInt` |
| 2018 | `GetWeaponOverrideBool` |
| 2021 | `GetWeaponOverrideString` |
| 2024 | `GetWeaponOverrideTextureSet` |
| 2028 | `GetWeaponPropertyFloat` |
| 2031 | `GetWeaponPropertyInt` |
| 2034 | `GetWeaponPropertyBool` |
| 2037 | `GetWeaponPropertyString` |
| 2042 | `HasSkinOverride` |
| 2045 | `AddSkinOverrideFloat` |
| 2048 | `AddSkinOverrideInt` |
| 2051 | `AddSkinOverrideBool` |
| 2054 | `AddSkinOverrideString` |
| 2057 | `AddSkinOverrideTextureSet` |
| 2060 | `ApplySkinOverrides` |
| 2065 | `GetSkinOverrideFloat` |
| 2068 | `GetSkinOverrideInt` |
| 2071 | `GetSkinOverrideBool` |
| 2074 | `GetSkinOverrideString` |
| 2077 | `GetSkinOverrideTextureSet` |
| 2081 | `GetSkinPropertyFloat` |
| 2084 | `GetSkinPropertyInt` |
| 2087 | `GetSkinPropertyBool` |
| 2090 | `GetSkinPropertyString` |
| 2096 | `RemoveAllOverrides` |
| 2099 | `RemoveAllReferenceOverrides` |
| 2102 | `RemoveAllArmorOverrides` |
| 2105 | `RemoveAllArmorAddonOverrides` |
| 2108 | `RemoveAllArmorAddonNodeOverrides` |
| 2111 | `RemoveOverride` |
| 2115 | `RemoveAllNodeOverrides` |
| 2118 | `RemoveAllReferenceNodeOverrides` |
| 2121 | `RemoveAllNodeNameOverrides` |
| 2124 | `RemoveNodeOverride` |
| 2128 | `RemoveAllWeaponBasedOverrides` |
| 2131 | `RemoveAllReferenceWeaponOverrides` |
| 2134 | `RemoveAllWeaponOverrides` |
| 2137 | `RemoveAllWeaponNodeOverrides` |
| 2140 | `RemoveWeaponOverride` |
| 2145 | `RemoveAllSkinBasedOverrides` |
| 2148 | `RemoveAllReferenceSkinOverrides` |
| 2151 | `RemoveAllSkinOverrides` |
| 2154 | `RemoveSkinOverride` |
| 2159 | `HasBodyMorph` |
| 2162 | `SetBodyMorph` |
| 2165 | `GetBodyMorph` |
| 2168 | `ClearBodyMorph` |
| 2171 | `HasBodyMorphKey` |
| 2174 | `ClearBodyMorphKeys` |
| 2177 | `HasBodyMorphName` |
| 2180 | `ClearBodyMorphNames` |
| 2183 | `ClearMorphs` |
| 2186 | `UpdateModelWeight` |
| 2189 | `GetMorphNames` |
| 2192 | `GetMorphKeys` |
| 2195 | `GetMorphedReferences` |
| 2198 | `ForEachMorphedReference` |
| 2201 | `GetCachedMorphNames` |
| 2206 | `GetItemUniqueID` |
| 2209 | `GetObjectUniqueID` |
| 2212 | `GetFormFromUniqueID` |
| 2215 | `GetOwnerOfUniqueID` |
| 2220 | `SetItemDyeColor` |
| 2223 | `GetItemDyeColor` |
| 2226 | `ClearItemDyeColor` |
| 2229 | `UpdateItemDyeColor` |
| 2234 | `SetItemTextureLayerColor` |
| 2237 | `GetItemTextureLayerColor` |
| 2240 | `ClearItemTextureLayerColor` |
| 2243 | `SetItemTextureLayerType` |
| 2246 | `GetItemTextureLayerType` |
| 2249 | `ClearItemTextureLayerType` |
| 2252 | `SetItemTextureLayerTexture` |
| 2255 | `GetItemTextureLayerTexture` |
| 2258 | `ClearItemTextureLayerTexture` |
| 2261 | `SetItemTextureLayerBlendMode` |
| 2264 | `GetItemTextureLayerBlendMode` |
| 2267 | `ClearItemTextureLayerBlendMode` |
| 2270 | `UpdateItemTextureLayers` |
| 2274 | `EnableTintTextureCache` |
| 2277 | `ReleaseTintTextureCache` |
| 2280 | `IsFormDye` |
| 2283 | `GetFormDyeColor` |
| 2286 | `RegisterFormDyeColor` |
| 2289 | `UnregisterFormDyeColor` |
| 2293 | `HasNodeTransformPosition` |
| 2296 | `AddNodeTransformPosition` |
| 2299 | `GetNodeTransformPosition` |
| 2302 | `RemoveNodeTransformPosition` |
| 2306 | `HasNodeTransformScale` |
| 2309 | `AddNodeTransformScale` |
| 2312 | `GetNodeTransformScale` |
| 2315 | `RemoveNodeTransformScale` |
| 2319 | `HasNodeTransformRotation` |
| 2322 | `AddNodeTransformRotation` |
| 2325 | `GetNodeTransformRotation` |
| 2328 | `RemoveNodeTransformRotation` |
| 2332 | `HasNodeTransformScaleMode` |
| 2335 | `AddNodeTransformScaleMode` |
| 2338 | `GetNodeTransformScaleMode` |
| 2341 | `RemoveNodeTransformScaleMode` |
| 2345 | `UpdateAllReferenceTransforms` |
| 2348 | `UpdateNodeTransform` |
| 2351 | `RemoveAllReferenceTransforms` |
| 2354 | `RemoveAllTransforms` |
| 2357 | `GetInverseTransform` |
| 2360 | `SetNodeDestination` |
| 2363 | `RemoveNodeDestination` |
| 2366 | `GetNodeDestination` |
| 2369 | `GetNodeTransformNames` |
| 2372 | `GetNodeTransformKeys` |
| 2377 | `GetBooleanExtraData` |
| 2380 | `GetIntegerExtraData` |
| 2383 | `GetIntegersExtraData` |
| 2386 | `GetFloatExtraData` |
| 2389 | `GetFloatsExtraData` |
| 2392 | `GetStringExtraData` |
| 2395 | `GetStringsExtraData` |

## CharGen

| Line | Function |
|---:|---|
| 362 | `SaveCharacter` |
| 365 | `LoadCharacterEx` |
| 368 | `DeleteCharacter` |
| 371 | `DeleteFaceGenData` |
| 374 | `SaveExternalCharacter` |
| 377 | `LoadExternalCharacterEx` |
| 380 | `ClearPreset` |
| 383 | `ClearPresets` |
| 386 | `IsExternalEnabled` |
| 389 | `ExportHead` |
| 392 | `ExportSlot` |
| 395 | `LoadCharacterPresetEx` |
| 398 | `SaveCharacterPreset` |

## Functional families

### Overlay management
Get overlay capacities; add/remove/revert body/head overlays.

### Armor/addon overrides
Typed property overrides for armor-addon nodes, plus application/query/removal.

### Node overrides
Typed arbitrary node property override state.

### Weapon overrides
Typed weapon/node property state.

### Skin overrides
Typed skin-slot property state with first-person/sex distinctions.

### Body morphs
Set/get/clear one morph+key; clear by key/name/all; enumerate morphed references; update model weight.

### Unique item identity and dye
Query item/object unique IDs, resolve owner/form, set/get/clear dye colors and texture-layer properties.

### Node transforms
Position/rotation/scale/scale-mode state and destination/attachment operations.

### NiExtraData queries
Read boolean/integer/float/string node ExtraData.

### CharGen/preset/export
Character/preset save/load, external character support, head/slot export and preset clearing.

## Key design distinction

NiOverride function names expose several independent state stores under one Papyrus script. Do not treat “NiOverride” as a single override table.

For troubleshooting, identify the family:
- armor override;
- node override;
- weapon override;
- skin override;
- BodyMorph;
- NiTransform;
- item/dye data;
- overlay.

## Source-version caution

The current public GitHub source marker is 0.4.19.17, while current public RaceMenu distribution is newer. Function availability in a particular installed RaceMenu build must be checked against that binary/version, not assumed solely from this source snapshot.
