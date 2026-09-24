# PapyrusUtil Complete PSC API Signatures

Imported: 2026-09-24
Upstream: `eeveelo/PapyrusUtil`
Status: source-derived provider API

## ActorUtil

Source blob: `cff8e7b69c9f9edcb6f8051699c817e7d3d34b37`
Functions: 5

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 13 | `void` | `AddPackageOverride` | `Actor targetActor, Package targetPackage, int priority = 30, int flags = 0` | `global native` |
| 16 | `bool` | `RemovePackageOverride` | `Actor targetActor, Package targetPackage` | `global native` |
| 19 | `int` | `CountPackageOverride` | `Actor targetActor` | `global native` |
| 22 | `int` | `ClearPackageOverride` | `Actor targetActor` | `global native` |
| 25 | `int` | `RemoveAllPackageOverride` | `Package targetPackage` | `global native` |

## JsonUtil

Source blob: `7618e9f385daf60b94cde392015489fd585c6098`
Functions: 135

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 33 | `bool` | `Load` | `string FileName` | `global native` |
| 34 | `bool` | `Save` | `string FileName, bool minify = false` | `global native` |
| 35 | `bool` | `Unload` | `string FileName, bool saveChanges = true, bool minify = false` | `global native` |
| 38 | `bool` | `IsPendingSave` | `string FileName` | `global native` |
| 40 | `bool` | `IsGood` | `string FileName` | `global native` |
| 42 | `string` | `GetErrors` | `string FileName` | `global native` |
| 44 | `string[]` | `JsonInFolder` | `string folderPath` | `global native` |
| 46 | `bool` | `JsonExists` | `string FileName` | `global` |
| 56 | `int` | `SetIntValue` | `string FileName, string KeyName, int value` | `global native` |
| 57 | `float` | `SetFloatValue` | `string FileName, string KeyName, float value` | `global native` |
| 58 | `string` | `SetStringValue` | `string FileName, string KeyName, string value` | `global native` |
| 59 | `form` | `SetFormValue` | `string FileName, string KeyName, form value` | `global native` |
| 61 | `int` | `GetIntValue` | `string FileName, string KeyName, int missing = 0` | `global native` |
| 62 | `float` | `GetFloatValue` | `string FileName, string KeyName, float missing = 0.0` | `global native` |
| 63 | `string` | `GetStringValue` | `string FileName, string KeyName, string missing = ""` | `global native` |
| 64 | `form` | `GetFormValue` | `string FileName, string KeyName, form missing = none` | `global native` |
| 66 | `bool` | `UnsetIntValue` | `string FileName, string KeyName` | `global native` |
| 67 | `bool` | `UnsetFloatValue` | `string FileName, string KeyName` | `global native` |
| 68 | `bool` | `UnsetStringValue` | `string FileName, string KeyName` | `global native` |
| 69 | `bool` | `UnsetFormValue` | `string FileName, string KeyName` | `global native` |
| 71 | `bool` | `HasIntValue` | `string FileName, string KeyName` | `global native` |
| 72 | `bool` | `HasFloatValue` | `string FileName, string KeyName` | `global native` |
| 73 | `bool` | `HasStringValue` | `string FileName, string KeyName` | `global native` |
| 74 | `bool` | `HasFormValue` | `string FileName, string KeyName` | `global native` |
| 76 | `int` | `IntListAdd` | `string FileName, string KeyName, int value, bool allowDuplicate = true` | `global native` |
| 77 | `int` | `FloatListAdd` | `string FileName, string KeyName, float value, bool allowDuplicate = true` | `global native` |
| 78 | `int` | `StringListAdd` | `string FileName, string KeyName, String value, bool allowDuplicate = true` | `global native` |
| 79 | `int` | `FormListAdd` | `string FileName, string KeyName, Form value, bool allowDuplicate = true` | `global native` |
| 81 | `Int` | `IntListGet` | `string FileName, string KeyName, int index` | `global native` |
| 82 | `Float` | `FloatListGet` | `string FileName, string KeyName, int index` | `global native` |
| 83 | `String` | `StringListGet` | `string FileName, string KeyName, int index` | `global native` |
| 84 | `Form` | `FormListGet` | `string FileName, string KeyName, int index` | `global native` |
| 86 | `Int` | `IntListSet` | `string FileName, string KeyName, int index, int value` | `global native` |
| 87 | `Float` | `FloatListSet` | `string FileName, string KeyName, int index, float value` | `global native` |
| 88 | `String` | `StringListSet` | `string FileName, string KeyName, int index, String value` | `global native` |
| 89 | `Form` | `FormListSet` | `string FileName, string KeyName, int index, Form value` | `global native` |
| 91 | `int` | `IntListRemove` | `string FileName, string KeyName, int value, bool allInstances = true` | `global native` |
| 92 | `int` | `FloatListRemove` | `string FileName, string KeyName, float value, bool allInstances = true` | `global native` |
| 93 | `int` | `StringListRemove` | `string FileName, string KeyName, String value, bool allInstances = true` | `global native` |
| 94 | `int` | `FormListRemove` | `string FileName, string KeyName, Form value, bool allInstances = true` | `global native` |
| 96 | `bool` | `IntListInsertAt` | `string FileName, string KeyName, int index, int value` | `global native` |
| 97 | `bool` | `FloatListInsertAt` | `string FileName, string KeyName, int index, float value` | `global native` |
| 98 | `bool` | `StringListInsertAt` | `string FileName, string KeyName, int index, String value` | `global native` |
| 99 | `bool` | `FormListInsertAt` | `string FileName, string KeyName, int index, Form value` | `global native` |
| 101 | `bool` | `IntListRemoveAt` | `string FileName, string KeyName, int index` | `global native` |
| 102 | `bool` | `FloatListRemoveAt` | `string FileName, string KeyName, int index` | `global native` |
| 103 | `bool` | `StringListRemoveAt` | `string FileName, string KeyName, int index` | `global native` |
| 104 | `bool` | `FormListRemoveAt` | `string FileName, string KeyName, int index` | `global native` |
| 106 | `int` | `IntListClear` | `string FileName, string KeyName` | `global native` |
| 107 | `int` | `FloatListClear` | `string FileName, string KeyName` | `global native` |
| 108 | `int` | `StringListClear` | `string FileName, string KeyName` | `global native` |
| 109 | `int` | `FormListClear` | `string FileName, string KeyName` | `global native` |
| 111 | `int` | `IntListCount` | `string FileName, string KeyName` | `global native` |
| 112 | `int` | `FloatListCount` | `string FileName, string KeyName` | `global native` |
| 113 | `int` | `StringListCount` | `string FileName, string KeyName` | `global native` |
| 114 | `int` | `FormListCount` | `string FileName, string KeyName` | `global native` |
| 116 | `int` | `IntListCountValue` | `string FileName, string KeyName, int value, bool exclude = false` | `global native` |
| 117 | `int` | `FloatListCountValue` | `string FileName, string KeyName, float value, bool exclude = false` | `global native` |
| 118 | `int` | `StringListCountValue` | `string FileName, string KeyName, String value, bool exclude = false` | `global native` |
| 119 | `int` | `FormListCountValue` | `string FileName, string KeyName, Form value, bool exclude = false` | `global native` |
| 121 | `int` | `IntListFind` | `string FileName, string KeyName, int value` | `global native` |
| 122 | `int` | `FloatListFind` | `string FileName, string KeyName, float value` | `global native` |
| 123 | `int` | `StringListFind` | `string FileName, string KeyName, String value` | `global native` |
| 124 | `int` | `FormListFind` | `string FileName, string KeyName, Form value` | `global native` |
| 126 | `bool` | `IntListHas` | `string FileName, string KeyName, int value` | `global native` |
| 127 | `bool` | `FloatListHas` | `string FileName, string KeyName, float value` | `global native` |
| 128 | `bool` | `StringListHas` | `string FileName, string KeyName, String value` | `global native` |
| 129 | `bool` | `FormListHas` | `string FileName, string KeyName, Form value` | `global native` |
| 131 | `void` | `IntListSlice` | `string FileName, string KeyName, int[] slice, int startIndex = 0` | `global native` |
| 132 | `void` | `FloatListSlice` | `string FileName, string KeyName, float[] slice, int startIndex = 0` | `global native` |
| 133 | `void` | `StringListSlice` | `string FileName, string KeyName, string[] slice, int startIndex = 0` | `global native` |
| 134 | `void` | `FormListSlice` | `string FileName, string KeyName, Form[] slice, int startIndex = 0` | `global native` |
| 136 | `int` | `IntListResize` | `string FileName, string KeyName, int toLength, int filler = 0` | `global native` |
| 137 | `int` | `FloatListResize` | `string FileName, string KeyName, int toLength, float filler = 0.0` | `global native` |
| 138 | `int` | `StringListResize` | `string FileName, string KeyName, int toLength, string filler = ""` | `global native` |
| 139 | `int` | `FormListResize` | `string FileName, string KeyName, int toLength, Form filler = none` | `global native` |
| 141 | `bool` | `IntListCopy` | `string FileName, string KeyName, int[] copy` | `global native` |
| 142 | `bool` | `FloatListCopy` | `string FileName, string KeyName, float[] copy` | `global native` |
| 143 | `bool` | `StringListCopy` | `string FileName, string KeyName, string[] copy` | `global native` |
| 144 | `bool` | `FormListCopy` | `string FileName, string KeyName, Form[] copy` | `global native` |
| 146 | `int[]` | `IntListToArray` | `string FileName, string KeyName` | `global native` |
| 147 | `float[]` | `FloatListToArray` | `string FileName, string KeyName` | `global native` |
| 148 | `string[]` | `StringListToArray` | `string FileName, string KeyName` | `global native` |
| 149 | `Form[]` | `FormListToArray` | `string FileName, string KeyName` | `global native` |
| 151 | `int` | `AdjustIntValue` | `string FileName, string KeyName, int amount` | `global native` |
| 152 | `float` | `AdjustFloatValue` | `string FileName, string KeyName, float amount` | `global native` |
| 153 | `Int` | `IntListAdjust` | `string FileName, string KeyName, int index, Int amount` | `global native` |
| 154 | `float` | `FloatListAdjust` | `string FileName, string KeyName, int index, float amount` | `global native` |
| 156 | `int` | `IntListRandom` | `string FileName, string KeyName` | `global native` |
| 157 | `float` | `FloatListRandom` | `string FileName, string KeyName` | `global native` |
| 158 | `string` | `StringListRandom` | `string FileName, string KeyName` | `global native` |
| 159 | `Form` | `FormListRandom` | `string FileName, string KeyName` | `global native` |
| 161 | `int` | `CountIntValuePrefix` | `string FileName, string PrefixKey` | `global native` |
| 162 | `int` | `CountFloatValuePrefix` | `string FileName, string PrefixKey` | `global native` |
| 163 | `int` | `CountStringValuePrefix` | `string FileName, string PrefixKey` | `global native` |
| 164 | `int` | `CountFormValuePrefix` | `string FileName, string PrefixKey` | `global native` |
| 166 | `int` | `CountIntListPrefix` | `string FileName, string PrefixKey` | `global native` |
| 167 | `int` | `CountFloatListPrefix` | `string FileName, string PrefixKey` | `global native` |
| 168 | `int` | `CountStringListPrefix` | `string FileName, string PrefixKey` | `global native` |
| 169 | `int` | `CountFormListPrefix` | `string FileName, string PrefixKey` | `global native` |
| 171 | `int` | `CountAllPrefix` | `string FileName, string PrefixKey` | `global native` |
| 183 | `void` | `SetPathIntValue` | `string FileName, string Path, int value` | `global native` |
| 184 | `void` | `SetPathFloatValue` | `string FileName, string Path, float value` | `global native` |
| 185 | `void` | `SetPathStringValue` | `string FileName, string Path, string value` | `global native` |
| 186 | `void` | `SetPathFormValue` | `string FileName, string Path, form value` | `global native` |
| 188 | `bool` | `SetRawPathValue` | `string FileName, string Path, string RawJSON` | `global native` |
| 190 | `int` | `GetPathIntValue` | `string FileName, string Path, int missing = 0` | `global native` |
| 191 | `float` | `GetPathFloatValue` | `string FileName, string Path, float missing = 0.0` | `global native` |
| 192 | `string` | `GetPathStringValue` | `string FileName, string Path, string missing = ""` | `global native` |
| 193 | `form` | `GetPathFormValue` | `string FileName, string Path, form missing = none` | `global native` |
| 194 | `bool` | `GetPathBoolValue` | `string FileName, string Path, bool missing = false` | `global` |
| 198 | `int[]` | `PathIntElements` | `string FileName, string Path, int invalidType = 0` | `global native` |
| 199 | `float[]` | `PathFloatElements` | `string FileName, string Path, float invalidType = 0.0` | `global native` |
| 200 | `string[]` | `PathStringElements` | `string FileName, string Path, string invalidType = ""` | `global native` |
| 201 | `form[]` | `PathFormElements` | `string FileName, string Path, form invalidType = none` | `global native` |
| 203 | `int` | `FindPathIntElement` | `string FileName, string Path, int toFind` | `global native` |
| 204 | `int` | `FindPathFloatElement` | `string FileName, string Path, float toFind` | `global native` |
| 205 | `int` | `FindPathStringElement` | `string FileName, string Path, string toFind` | `global native` |
| 206 | `int` | `FindPathFormElement` | `string FileName, string Path, form toFind` | `global native` |
| 208 | `int` | `PathCount` | `string FileName, string Path` | `global native` |
| 209 | `string[]` | `PathMembers` | `string FileName, string Path` | `global native` |
| 211 | `bool` | `CanResolvePath` | `string FileName, string Path` | `global native` |
| 212 | `bool` | `IsPathString` | `string FileName, string Path` | `global native` |
| 213 | `bool` | `IsPathNumber` | `string FileName, string Path` | `global native` |
| 214 | `bool` | `IsPathForm` | `string FileName, string Path` | `global native` |
| 215 | `bool` | `IsPathBool` | `string FileName, string Path` | `global native` |
| 216 | `bool` | `IsPathArray` | `string FileName, string Path` | `global native` |
| 217 | `bool` | `IsPathObject` | `string FileName, string Path` | `global native` |
| 219 | `void` | `SetPathIntArray` | `string FileName, string Path, int[] arr, bool append = false` | `global native` |
| 220 | `void` | `SetPathFloatArray` | `string FileName, string Path, float[] arr, bool append = false` | `global native` |
| 221 | `void` | `SetPathStringArray` | `string FileName, string Path, string[] arr, bool append = false` | `global native` |
| 222 | `void` | `SetPathFormArray` | `string FileName, string Path, form[] arr, bool append = false` | `global native` |
| 224 | `void` | `ClearPath` | `string FileName, string Path` | `global native` |
| 225 | `void` | `ClearPathIndex` | `string FileName, string Path, int Index` | `global native` |
| 228 | `void` | `ClearAll` | `string FileName` | `global native` |

## MiscUtil

Source blob: `ccbf5e6b59f7954ae525ba1c978d08900a2e03b3`
Functions: 18

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 11 | `ObjectReference[]` | `ScanCellObjects` | `int formType, ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none` | `global native` |
| 18 | `Actor[]` | `ScanCellNPCs` | `ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none, bool IgnoreDead = true` | `global native` |
| 22 | `Actor[]` | `ScanCellNPCsByFaction` | `Faction FindFaction, ObjectReference CenterOn, float radius = 0.0, int minRank = 0, int maxRank = 127, bool IgnoreDead = true` | `global native` |
| 30 | `void` | `ToggleFreeCamera` | `bool stopTime = false` | `global native` |
| 32 | `void` | `SetFreeCameraSpeed` | `float speed` | `global native` |
| 35 | `void` | `SetFreeCameraState` | `bool enable, float speed = 10.0` | `global native` |
| 47 | `string[]` | `FilesInFolder` | `string directory, string extension="*"` | `global native` |
| 51 | `string[]` | `FoldersInFolder` | `string directory` | `global native` |
| 54 | `bool` | `FileExists` | `string fileName` | `global native` |
| 58 | `string` | `ReadFromFile` | `string fileName` | `global native` |
| 61 | `bool` | `WriteToFile` | `string fileName, string text, bool append = true, bool timestamp = false` | `global native` |
| 69 | `void` | `PrintConsole` | `string text` | `global native` |
| 72 | `string` | `GetRaceEditorID` | `Race raceForm` | `global native` |
| 75 | `string` | `GetActorRaceEditorID` | `Actor actorRef` | `global native` |
| 78 | `void` | `SetMenus` | `bool enabled` | `global native` |
| 85 | `float` | `GetNodeRotation` | `ObjectReference obj, string nodeName, bool firstPerson, int rotationIndex` | `global` |
| 92 | `void` | `ExecuteBat` | `string fileName` | `global` |
| 97 | `Actor[]` | `ScanCellActors` | `ObjectReference CenterOn, float radius = 5000.0, Keyword HasKeyword = none` | `global` |

## ObjectUtil

Source blob: `5f7be6a55a1b060efc4c58da7f56c905c7ba65f6`
Functions: 0

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|

## PapyrusUtil

Source blob: `9f8c370b3f2a170d9ddd9d627f47df9850bf1f50`
Functions: 97

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 4 | `int` | `GetVersion` | `` | `global native` |
| 7 | `int` | `GetScriptVersion` | `` | `global` |
| 16 | `Actor[]` | `ActorArray` | `int size, Actor filler = none` | `global native` |
| 17 | `Actor[]` | `ResizeActorArray` | `Actor[] ArrayValues, int toSize, Actor filler = none` | `global native` |
| 18 | `ObjectReference[]` | `ObjRefArray` | `int size, ObjectReference filler = none` | `global native` |
| 19 | `ObjectReference[]` | `ResizeObjRefArray` | `ObjectReference[] ArrayValues, int toSize, ObjectReference filler = none` | `global native` |
| 24 | `float[]` | `PushFloat` | `float[] ArrayValues, float push` | `global native` |
| 25 | `int[]` | `PushInt` | `int[] ArrayValues, int push` | `global native` |
| 27 | `string[]` | `PushString` | `string[] ArrayValues, string push` | `global native` |
| 28 | `Form[]` | `PushForm` | `Form[] ArrayValues, Form push` | `global native` |
| 29 | `Alias[]` | `PushAlias` | `Alias[] ArrayValues, Alias push` | `global native` |
| 30 | `Actor[]` | `PushActor` | `Actor[] ArrayValues, Actor push` | `global native` |
| 31 | `ObjectReference[]` | `PushObjRef` | `ObjectReference[] ArrayValues, ObjectReference push` | `global native` |
| 34 | `float[]` | `RemoveFloat` | `float[] ArrayValues, float ToRemove` | `global native` |
| 35 | `int[]` | `RemoveInt` | `int[] ArrayValues, int ToRemove` | `global native` |
| 37 | `string[]` | `RemoveString` | `string[] ArrayValues, string ToRemove` | `global native` |
| 38 | `Form[]` | `RemoveForm` | `Form[] ArrayValues, Form ToRemove` | `global native` |
| 39 | `Alias[]` | `RemoveAlias` | `Alias[] ArrayValues, Alias ToRemove` | `global native` |
| 40 | `Actor[]` | `RemoveActor` | `Actor[] ArrayValues, Actor ToRemove` | `global native` |
| 41 | `ObjectReference[]` | `RemoveObjRef` | `ObjectReference[] ArrayValues, ObjectReference ToRemove` | `global native` |
| 44 | `float[]` | `RemoveDupeFloat` | `float[] ArrayValues` | `global native` |
| 45 | `int[]` | `RemoveDupeInt` | `int[] ArrayValues` | `global native` |
| 46 | `string[]` | `RemoveDupeString` | `string[] ArrayValues` | `global native` |
| 47 | `Form[]` | `RemoveDupeForm` | `Form[] ArrayValues` | `global native` |
| 48 | `Alias[]` | `RemoveDupeAlias` | `Alias[] ArrayValues` | `global native` |
| 49 | `Actor[]` | `RemoveDupeActor` | `Actor[] ArrayValues` | `global native` |
| 50 | `ObjectReference[]` | `RemoveDupeObjRef` | `ObjectReference[] ArrayValues` | `global native` |
| 55 | `float[]` | `GetDiffFloat` | `float[] ArrayValues1, float[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 56 | `int[]` | `GetDiffInt` | `int[] ArrayValues1, int[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 57 | `string[]` | `GetDiffString` | `string[] ArrayValues1, string[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 58 | `Form[]` | `GetDiffForm` | `Form[] ArrayValues1, Form[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 59 | `Alias[]` | `GetDiffAlias` | `Alias[] ArrayValues1, Alias[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 60 | `Actor[]` | `GetDiffActor` | `Actor[] ArrayValues1, Actor[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 61 | `ObjectReference[]` | `GetDiffObjRef` | `ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false` | `global native` |
| 64 | `float[]` | `GetMatchingFloat` | `float[] ArrayValues1, float[] ArrayValues2` | `global native` |
| 65 | `int[]` | `GetMatchingInt` | `int[] ArrayValues1, int[] ArrayValues2` | `global native` |
| 66 | `string[]` | `GetMatchingString` | `string[] ArrayValues1, string[] ArrayValues2` | `global native` |
| 67 | `Form[]` | `GetMatchingForm` | `Form[] ArrayValues1, Form[] ArrayValues2` | `global native` |
| 68 | `Alias[]` | `GetMatchingAlias` | `Alias[] ArrayValues1, Alias[] ArrayValues2` | `global native` |
| 69 | `Actor[]` | `GetMatchingActor` | `Actor[] ArrayValues1, Actor[] ArrayValues2` | `global native` |
| 70 | `ObjectReference[]` | `GetMatchingObjRef` | `ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2` | `global native` |
| 73 | `int` | `CountFloat` | `float[] ArrayValues, float EqualTo` | `global native` |
| 74 | `int` | `CountInt` | `int[] ArrayValues, int EqualTo` | `global native` |
| 75 | `int` | `CountBool` | `bool[] ArrayValues, bool EqualTo` | `global native` |
| 76 | `int` | `CountString` | `string[] ArrayValues, string EqualTo` | `global native` |
| 77 | `int` | `CountForm` | `Form[] ArrayValues, Form EqualTo` | `global native` |
| 78 | `int` | `CountAlias` | `Alias[] ArrayValues, Alias EqualTo` | `global native` |
| 79 | `int` | `CountActor` | `Actor[] ArrayValues, Actor EqualTo` | `global native` |
| 80 | `int` | `CountObjRef` | `ObjectReference[] ArrayValues, ObjectReference EqualTo` | `global native` |
| 83 | `float[]` | `MergeFloatArray` | `float[] ArrayValues1, float[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 84 | `int[]` | `MergeIntArray` | `int[] ArrayValues1, int[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 86 | `string[]` | `MergeStringArray` | `string[] ArrayValues1, string[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 87 | `Form[]` | `MergeFormArray` | `Form[] ArrayValues1, Form[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 88 | `Alias[]` | `MergeAliasArray` | `Alias[] ArrayValues1, Alias[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 89 | `Actor[]` | `MergeActorArray` | `Actor[] ArrayValues1, Actor[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 90 | `ObjectReference[]` | `MergeObjRefArray` | `ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool RemoveDupes = false` | `global native` |
| 94 | `float[]` | `SliceFloatArray` | `float[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 95 | `int[]` | `SliceIntArray` | `int[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 97 | `string[]` | `SliceStringArray` | `string[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 98 | `Form[]` | `SliceFormArray` | `Form[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 99 | `Alias[]` | `SliceAliasArray` | `Alias[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 100 | `Actor[]` | `SliceActorArray` | `Actor[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 101 | `ObjectReference[]` | `SliceObjRefArray` | `ObjectReference[] ArrayValues, int StartIndex, int EndIndex = -1` | `global native` |
| 105 | `void` | `SortIntArray` | `int[] ArrayValues, bool descending = false` | `global native` |
| 106 | `void` | `SortFloatArray` | `float[] ArrayValues, bool descending = false` | `global native` |
| 107 | `void` | `SortStringArray` | `string[] ArrayValues, bool descending = false` | `global native` |
| 113 | `string[]` | `ClearEmpty` | `string[] ArrayValues` | `global` |
| 116 | `Form[]` | `ClearNone` | `Form[] ArrayValues` | `global` |
| 120 | `int` | `CountFalse` | `bool[] ArrayValues` | `global` |
| 123 | `int` | `CountTrue` | `bool[] ArrayValues` | `global` |
| 126 | `int` | `CountNone` | `Form[] ArrayValues` | `global` |
| 135 | `string[]` | `StringSplit` | `string ArgString, string Delimiter = ","` | `global native` |
| 138 | `string` | `StringJoin` | `string[] Values, string Delimiter = ","` | `global native` |
| 147 | `int` | `AddIntValues` | `int[] Values` | `global native` |
| 148 | `float` | `AddFloatValues` | `float[] Values` | `global native` |
| 151 | `int` | `ClampInt` | `int value, int min, int max` | `global native` |
| 152 | `float` | `ClampFloat` | `float value, float min, float max` | `global native` |
| 157 | `int` | `WrapInt` | `int value, int end, int start = 0` | `global native` |
| 158 | `float` | `WrapFloat` | `float value, float end, float start = 0.0` | `global native` |
| 161 | `int` | `SignInt` | `bool doSign, int value` | `global native` |
| 162 | `float` | `SignFloat` | `bool doSign, float value` | `global native` |
| 169 | `bool[]` | `ResizeBoolArray` | `bool[] ArrayValues, int toSize, bool filler = false` | `global` |
| 182 | `bool[]` | `PushBool` | `bool[] ArrayValues, bool push` | `global` |
| 186 | `bool[]` | `RemoveBool` | `bool[] ArrayValues, bool ToRemove` | `global` |
| 191 | `bool[]` | `MergeBoolArray` | `bool[] ArrayValues1, bool[] ArrayValues2, bool RemoveDupes = false` | `global` |
| 223 | `bool[]` | `SliceBoolArray` | `bool[] ArrayValues, int StartIndex, int EndIndex = -1` | `global` |
| 254 | `float[]` | `FloatArray` | `int size, float filler = 0.0` | `global` |
| 257 | `int[]` | `IntArray` | `int size, int filler = 0` | `global` |
| 260 | `bool[]` | `BoolArray` | `int size, bool filler = false` | `global` |
| 263 | `string[]` | `StringArray` | `int size, string filler = ""` | `global` |
| 266 | `Form[]` | `FormArray` | `int size, Form filler = none` | `global` |
| 269 | `Alias[]` | `AliasArray` | `int size, Alias filler = none` | `global` |
| 273 | `float[]` | `ResizeFloatArray` | `float[] ArrayValues, int toSize, float filler = 0.0` | `global` |
| 276 | `int[]` | `ResizeIntArray` | `int[] ArrayValues, int toSize, int filler = 0` | `global` |
| 279 | `string[]` | `ResizeStringArray` | `string[] ArrayValues, int toSize, string filler = ""` | `global` |
| 282 | `Form[]` | `ResizeFormArray` | `Form[] ArrayValues, int toSize, Form filler = none` | `global` |
| 285 | `Alias[]` | `ResizeAliasArray` | `Alias[] ArrayValues, int toSize, Alias filler = none` | `global` |

## StorageUtil

Source blob: `c309fef20cf56342c5ee0ed53f5d146af51bc940`
Functions: 282

| Line | Return | Function | Arguments | Modifiers |
|---:|---|---|---|---|
| 77 | `int` | `SetIntValue` | `Form ObjKey, string KeyName, int value` | `global native` |
| 78 | `float` | `SetFloatValue` | `Form ObjKey, string KeyName, float value` | `global native` |
| 79 | `string` | `SetStringValue` | `Form ObjKey, string KeyName, string value` | `global native` |
| 80 | `Form` | `SetFormValue` | `Form ObjKey, string KeyName, Form value` | `global native` |
| 89 | `bool` | `UnsetIntValue` | `Form ObjKey, string KeyName` | `global native` |
| 90 | `bool` | `UnsetFloatValue` | `Form ObjKey, string KeyName` | `global native` |
| 91 | `bool` | `UnsetStringValue` | `Form ObjKey, string KeyName` | `global native` |
| 92 | `bool` | `UnsetFormValue` | `Form ObjKey, string KeyName` | `global native` |
| 100 | `bool` | `HasIntValue` | `Form ObjKey, string KeyName` | `global native` |
| 101 | `bool` | `HasFloatValue` | `Form ObjKey, string KeyName` | `global native` |
| 102 | `bool` | `HasStringValue` | `Form ObjKey, string KeyName` | `global native` |
| 103 | `bool` | `HasFormValue` | `Form ObjKey, string KeyName` | `global native` |
| 112 | `int` | `GetIntValue` | `Form ObjKey, string KeyName, int missing = 0` | `global native` |
| 113 | `float` | `GetFloatValue` | `Form ObjKey, string KeyName, float missing = 0.0` | `global native` |
| 114 | `string` | `GetStringValue` | `Form ObjKey, string KeyName, string missing = ""` | `global native` |
| 115 | `Form` | `GetFormValue` | `Form ObjKey, string KeyName, Form missing = none` | `global native` |
| 124 | `int` | `PluckIntValue` | `Form ObjKey, string KeyName, int missing = 0` | `global native` |
| 125 | `float` | `PluckFloatValue` | `Form ObjKey, string KeyName, float missing = 0.0` | `global native` |
| 126 | `string` | `PluckStringValue` | `Form ObjKey, string KeyName, string missing = ""` | `global native` |
| 127 | `Form` | `PluckFormValue` | `Form ObjKey, string KeyName, Form missing = none` | `global native` |
| 137 | `int` | `AdjustIntValue` | `Form ObjKey, string KeyName, int amount` | `global native` |
| 138 | `float` | `AdjustFloatValue` | `Form ObjKey, string KeyName, float amount` | `global native` |
| 150 | `int` | `IntListAdd` | `Form ObjKey, string KeyName, int value, bool allowDuplicate = true` | `global native` |
| 151 | `int` | `FloatListAdd` | `Form ObjKey, string KeyName, float value, bool allowDuplicate = true` | `global native` |
| 152 | `int` | `StringListAdd` | `Form ObjKey, string KeyName, string value, bool allowDuplicate = true` | `global native` |
| 153 | `int` | `FormListAdd` | `Form ObjKey, string KeyName, Form value, bool allowDuplicate = true` | `global native` |
| 162 | `int` | `IntListGet` | `Form ObjKey, string KeyName, int index` | `global native` |
| 163 | `float` | `FloatListGet` | `Form ObjKey, string KeyName, int index` | `global native` |
| 164 | `string` | `StringListGet` | `Form ObjKey, string KeyName, int index` | `global native` |
| 165 | `Form` | `FormListGet` | `Form ObjKey, string KeyName, int index` | `global native` |
| 175 | `int` | `IntListSet` | `Form ObjKey, string KeyName, int index, int value` | `global native` |
| 176 | `float` | `FloatListSet` | `Form ObjKey, string KeyName, int index, float value` | `global native` |
| 177 | `string` | `StringListSet` | `Form ObjKey, string KeyName, int index, string value` | `global native` |
| 178 | `Form` | `FormListSet` | `Form ObjKey, string KeyName, int index, Form value` | `global native` |
| 188 | `int` | `IntListPluck` | `Form ObjKey, string KeyName, int index, int missing` | `global native` |
| 189 | `float` | `FloatListPluck` | `Form ObjKey, string KeyName, int index, float missing` | `global native` |
| 190 | `string` | `StringListPluck` | `Form ObjKey, string KeyName, int index, string missing` | `global native` |
| 191 | `Form` | `FormListPluck` | `Form ObjKey, string KeyName, int index, Form missing` | `global native` |
| 198 | `int` | `IntListShift` | `Form ObjKey, string KeyName` | `global native` |
| 199 | `float` | `FloatListShift` | `Form ObjKey, string KeyName` | `global native` |
| 200 | `string` | `StringListShift` | `Form ObjKey, string KeyName` | `global native` |
| 201 | `Form` | `FormListShift` | `Form ObjKey, string KeyName` | `global native` |
| 208 | `int` | `IntListPop` | `Form ObjKey, string KeyName` | `global native` |
| 209 | `float` | `FloatListPop` | `Form ObjKey, string KeyName` | `global native` |
| 210 | `string` | `StringListPop` | `Form ObjKey, string KeyName` | `global native` |
| 211 | `Form` | `FormListPop` | `Form ObjKey, string KeyName` | `global native` |
| 222 | `int` | `IntListAdjust` | `Form ObjKey, string KeyName, int index, int amount` | `global native` |
| 223 | `float` | `FloatListAdjust` | `Form ObjKey, string KeyName, int index, float amount` | `global native` |
| 233 | `bool` | `IntListInsert` | `Form ObjKey, string KeyName, int index, int value` | `global native` |
| 234 | `bool` | `FloatListInsert` | `Form ObjKey, string KeyName, int index, float value` | `global native` |
| 235 | `bool` | `StringListInsert` | `Form ObjKey, string KeyName, int index, string value` | `global native` |
| 236 | `bool` | `FormListInsert` | `Form ObjKey, string KeyName, int index, Form value` | `global native` |
| 247 | `int` | `IntListRemove` | `Form ObjKey, string KeyName, int value, bool allInstances = false` | `global native` |
| 248 | `int` | `FloatListRemove` | `Form ObjKey, string KeyName, float value, bool allInstances = false` | `global native` |
| 249 | `int` | `StringListRemove` | `Form ObjKey, string KeyName, string value, bool allInstances = false` | `global native` |
| 250 | `int` | `FormListRemove` | `Form ObjKey, string KeyName, Form value, bool allInstances = false` | `global native` |
| 259 | `int` | `IntListClear` | `Form ObjKey, string KeyName` | `global native` |
| 260 | `int` | `FloatListClear` | `Form ObjKey, string KeyName` | `global native` |
| 261 | `int` | `StringListClear` | `Form ObjKey, string KeyName` | `global native` |
| 262 | `int` | `FormListClear` | `Form ObjKey, string KeyName` | `global native` |
| 271 | `bool` | `IntListRemoveAt` | `Form ObjKey, string KeyName, int index` | `global native` |
| 272 | `bool` | `FloatListRemoveAt` | `Form ObjKey, string KeyName, int index` | `global native` |
| 273 | `bool` | `StringListRemoveAt` | `Form ObjKey, string KeyName, int index` | `global native` |
| 274 | `bool` | `FormListRemoveAt` | `Form ObjKey, string KeyName, int index` | `global native` |
| 281 | `int` | `IntListCount` | `Form ObjKey, string KeyName` | `global native` |
| 282 | `int` | `FloatListCount` | `Form ObjKey, string KeyName` | `global native` |
| 283 | `int` | `StringListCount` | `Form ObjKey, string KeyName` | `global native` |
| 284 | `int` | `FormListCount` | `Form ObjKey, string KeyName` | `global native` |
| 293 | `int` | `IntListCountValue` | `Form ObjKey, string KeyName, int value, bool exclude = false` | `global native` |
| 294 | `int` | `FloatListCountValue` | `Form ObjKey, string KeyName, float value, bool exclude = false` | `global native` |
| 295 | `int` | `StringListCountValue` | `Form ObjKey, string KeyName, string value, bool exclude = false` | `global native` |
| 296 | `int` | `FormListCountValue` | `Form ObjKey, string KeyName, Form value, bool exclude = false` | `global native` |
| 305 | `int` | `IntListFind` | `Form ObjKey, string KeyName, int value` | `global native` |
| 306 | `int` | `FloatListFind` | `Form ObjKey, string KeyName, float value` | `global native` |
| 307 | `int` | `StringListFind` | `Form ObjKey, string KeyName, string value` | `global native` |
| 308 | `int` | `FormListFind` | `Form ObjKey, string KeyName, Form value` | `global native` |
| 317 | `bool` | `IntListHas` | `Form ObjKey, string KeyName, int value` | `global native` |
| 318 | `bool` | `FloatListHas` | `Form ObjKey, string KeyName, float value` | `global native` |
| 319 | `bool` | `StringListHas` | `Form ObjKey, string KeyName, string value` | `global native` |
| 320 | `bool` | `FormListHas` | `Form ObjKey, string KeyName, Form value` | `global native` |
| 327 | `void` | `IntListSort` | `Form ObjKey, string KeyName` | `global native` |
| 328 | `void` | `FloatListSort` | `Form ObjKey, string KeyName` | `global native` |
| 329 | `void` | `StringListSort` | `Form ObjKey, string KeyName` | `global native` |
| 330 | `void` | `FormListSort` | `Form ObjKey, string KeyName` | `global native` |
| 341 | `void` | `IntListSlice` | `Form ObjKey, string KeyName, int[] slice, int startIndex = 0` | `global native` |
| 342 | `void` | `FloatListSlice` | `Form ObjKey, string KeyName, float[] slice, int startIndex = 0` | `global native` |
| 343 | `void` | `StringListSlice` | `Form ObjKey, string KeyName, string[] slice, int startIndex = 0` | `global native` |
| 344 | `void` | `FormListSlice` | `Form ObjKey, string KeyName, Form[] slice, int startIndex = 0` | `global native` |
| 358 | `int` | `IntListResize` | `Form ObjKey, string KeyName, int toLength, int filler = 0` | `global native` |
| 359 | `int` | `FloatListResize` | `Form ObjKey, string KeyName, int toLength, float filler = 0.0` | `global native` |
| 360 | `int` | `StringListResize` | `Form ObjKey, string KeyName, int toLength, string filler = ""` | `global native` |
| 361 | `int` | `FormListResize` | `Form ObjKey, string KeyName, int toLength, Form filler = none` | `global native` |
| 373 | `bool` | `IntListCopy` | `Form ObjKey, string KeyName, int[] copy` | `global native` |
| 374 | `bool` | `FloatListCopy` | `Form ObjKey, string KeyName, float[] copy` | `global native` |
| 375 | `bool` | `StringListCopy` | `Form ObjKey, string KeyName, string[] copy` | `global native` |
| 376 | `bool` | `FormListCopy` | `Form ObjKey, string KeyName, Form[] copy` | `global native` |
| 385 | `int[]` | `IntListToArray` | `Form ObjKey, string KeyName` | `global native` |
| 386 | `float[]` | `FloatListToArray` | `Form ObjKey, string KeyName` | `global native` |
| 387 | `string[]` | `StringListToArray` | `Form ObjKey, string KeyName` | `global native` |
| 388 | `Form[]` | `FormListToArray` | `Form ObjKey, string KeyName` | `global native` |
| 398 | `int` | `IntListRandom` | `Form ObjKey, string KeyName` | `global native` |
| 399 | `float` | `FloatListRandom` | `Form ObjKey, string KeyName` | `global native` |
| 400 | `string` | `StringListRandom` | `Form ObjKey, string KeyName` | `global native` |
| 401 | `Form` | `FormListRandom` | `Form ObjKey, string KeyName` | `global native` |
| 412 | `Form[]` | `FormListFilterByTypes` | `Form ObjKey, string KeyName, int[] FormTypeIDs, bool ReturnMatching = true` | `global native` |
| 414 | `Form[]` | `FormListFilterByType` | `Form ObjKey, string KeyName, int FormTypeID, bool ReturnMatching = true` | `global` |
| 424 | `int` | `CountIntValuePrefix` | `string PrefixKey` | `global native` |
| 425 | `int` | `CountFloatValuePrefix` | `string PrefixKey` | `global native` |
| 426 | `int` | `CountStringValuePrefix` | `string PrefixKey` | `global native` |
| 427 | `int` | `CountFormValuePrefix` | `string PrefixKey` | `global native` |
| 429 | `int` | `CountIntListPrefix` | `string PrefixKey` | `global native` |
| 430 | `int` | `CountFloatListPrefix` | `string PrefixKey` | `global native` |
| 431 | `int` | `CountStringListPrefix` | `string PrefixKey` | `global native` |
| 432 | `int` | `CountFormListPrefix` | `string PrefixKey` | `global native` |
| 435 | `int` | `CountAllPrefix` | `string PrefixKey` | `global native` |
| 442 | `int` | `CountObjIntValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 443 | `int` | `CountObjFloatValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 444 | `int` | `CountObjStringValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 445 | `int` | `CountObjFormValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 447 | `int` | `CountObjIntListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 448 | `int` | `CountObjFloatListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 449 | `int` | `CountObjStringListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 450 | `int` | `CountObjFormListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 453 | `int` | `CountAllObjPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 461 | `int` | `ClearIntValuePrefix` | `string PrefixKey` | `global native` |
| 462 | `int` | `ClearFloatValuePrefix` | `string PrefixKey` | `global native` |
| 463 | `int` | `ClearStringValuePrefix` | `string PrefixKey` | `global native` |
| 464 | `int` | `ClearFormValuePrefix` | `string PrefixKey` | `global native` |
| 466 | `int` | `ClearIntListPrefix` | `string PrefixKey` | `global native` |
| 467 | `int` | `ClearFloatListPrefix` | `string PrefixKey` | `global native` |
| 468 | `int` | `ClearStringListPrefix` | `string PrefixKey` | `global native` |
| 469 | `int` | `ClearFormListPrefix` | `string PrefixKey` | `global native` |
| 472 | `int` | `ClearAllPrefix` | `string PrefixKey` | `global native` |
| 481 | `int` | `ClearObjIntValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 482 | `int` | `ClearObjFloatValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 483 | `int` | `ClearObjStringValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 484 | `int` | `ClearObjFormValuePrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 486 | `int` | `ClearObjIntListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 487 | `int` | `ClearObjFloatListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 488 | `int` | `ClearObjStringListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 489 | `int` | `ClearObjFormListPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 492 | `int` | `ClearAllObjPrefix` | `Form ObjKey, string PrefixKey` | `global native` |
| 498 | `void` | `debug_DeleteValues` | `Form ObjKey` | `global native` |
| 499 | `void` | `debug_DeleteAllValues` | `` | `global native` |
| 501 | `int` | `debug_Cleanup` | `` | `global native` |
| 503 | `Form[]` | `debug_AllIntObjs` | `` | `global native` |
| 504 | `Form[]` | `debug_AllFloatObjs` | `` | `global native` |
| 505 | `Form[]` | `debug_AllStringObjs` | `` | `global native` |
| 506 | `Form[]` | `debug_AllFormObjs` | `` | `global native` |
| 507 | `Form[]` | `debug_AllIntListObjs` | `` | `global native` |
| 508 | `Form[]` | `debug_AllFloatListObjs` | `` | `global native` |
| 509 | `Form[]` | `debug_AllStringListObjs` | `` | `global native` |
| 510 | `Form[]` | `debug_AllFormListObjs` | `` | `global native` |
| 512 | `string[]` | `debug_AllObjIntKeys` | `Form ObjKey` | `global native` |
| 513 | `string[]` | `debug_AllObjFloatKeys` | `Form ObjKey` | `global native` |
| 514 | `string[]` | `debug_AllObjStringKeys` | `Form ObjKey` | `global native` |
| 515 | `string[]` | `debug_AllObjFormKeys` | `Form ObjKey` | `global native` |
| 516 | `string[]` | `debug_AllObjIntListKeys` | `Form ObjKey` | `global native` |
| 517 | `string[]` | `debug_AllObjFloatListKeys` | `Form ObjKey` | `global native` |
| 518 | `string[]` | `debug_AllObjStringListKeys` | `Form ObjKey` | `global native` |
| 519 | `string[]` | `debug_AllObjFormListKeys` | `Form ObjKey` | `global native` |
| 521 | `int` | `debug_GetIntObjectCount` | `` | `global native` |
| 522 | `int` | `debug_GetFloatObjectCount` | `` | `global native` |
| 523 | `int` | `debug_GetStringObjectCount` | `` | `global native` |
| 524 | `int` | `debug_GetFormObjectCount` | `` | `global native` |
| 525 | `int` | `debug_GetIntListObjectCount` | `` | `global native` |
| 526 | `int` | `debug_GetFloatListObjectCount` | `` | `global native` |
| 527 | `int` | `debug_GetStringListObjectCount` | `` | `global native` |
| 528 | `int` | `debug_GetFormListObjectCount` | `` | `global native` |
| 530 | `Form` | `debug_GetIntObject` | `int index` | `global native` |
| 531 | `Form` | `debug_GetFloatObject` | `int index` | `global native` |
| 532 | `Form` | `debug_GetStringObject` | `int index` | `global native` |
| 533 | `Form` | `debug_GetFormObject` | `int index` | `global native` |
| 534 | `Form` | `debug_GetIntListObject` | `int index` | `global native` |
| 535 | `Form` | `debug_GetFloatListObject` | `int index` | `global native` |
| 536 | `Form` | `debug_GetStringListObject` | `int index` | `global native` |
| 537 | `Form` | `debug_GetFormListObject` | `int index` | `global native` |
| 539 | `int` | `debug_GetIntKeysCount` | `Form ObjKey` | `global native` |
| 540 | `int` | `debug_GetFloatKeysCount` | `Form ObjKey` | `global native` |
| 541 | `int` | `debug_GetStringKeysCount` | `Form ObjKey` | `global native` |
| 542 | `int` | `debug_GetFormKeysCount` | `Form ObjKey` | `global native` |
| 543 | `int` | `debug_GetIntListKeysCount` | `Form ObjKey` | `global native` |
| 544 | `int` | `debug_GetFloatListKeysCount` | `Form ObjKey` | `global native` |
| 545 | `int` | `debug_GetStringListKeysCount` | `Form ObjKey` | `global native` |
| 546 | `int` | `debug_GetFormListKeysCount` | `Form ObjKey` | `global native` |
| 548 | `string` | `debug_GetIntKey` | `Form ObjKey, int index` | `global native` |
| 549 | `string` | `debug_GetFloatKey` | `Form ObjKey, int index` | `global native` |
| 550 | `string` | `debug_GetStringKey` | `Form ObjKey, int index` | `global native` |
| 551 | `string` | `debug_GetFormKey` | `Form ObjKey, int index` | `global native` |
| 552 | `string` | `debug_GetIntListKey` | `Form ObjKey, int index` | `global native` |
| 553 | `string` | `debug_GetFloatListKey` | `Form ObjKey, int index` | `global native` |
| 554 | `string` | `debug_GetStringListKey` | `Form ObjKey, int index` | `global native` |
| 555 | `string` | `debug_GetFormListKey` | `Form ObjKey, int index` | `global native` |
| 568 | `int` | `FileSetIntValue` | `string KeyName, int value` | `global` |
| 571 | `float` | `FileSetFloatValue` | `string KeyName, float value` | `global` |
| 574 | `string` | `FileSetStringValue` | `string KeyName, string value` | `global` |
| 577 | `form` | `FileSetFormValue` | `string KeyName, Form value` | `global` |
| 581 | `int` | `FileAdjustIntValue` | `string KeyName, int amount` | `global` |
| 584 | `float` | `FileAdjustFloatValue` | `string KeyName, float amount` | `global` |
| 588 | `bool` | `FileUnsetIntValue` | `string KeyName` | `global` |
| 591 | `bool` | `FileUnsetFloatValue` | `string KeyName` | `global` |
| 594 | `bool` | `FileUnsetStringValue` | `string KeyName` | `global` |
| 597 | `bool` | `FileUnsetFormValue` | `string KeyName` | `global` |
| 601 | `bool` | `FileHasIntValue` | `string KeyName` | `global` |
| 604 | `bool` | `FileHasFloatValue` | `string KeyName` | `global` |
| 607 | `bool` | `FileHasStringValue` | `string KeyName` | `global` |
| 610 | `bool` | `FileHasFormValue` | `string KeyName` | `global` |
| 614 | `int` | `FileGetIntValue` | `string KeyName, int missing = 0` | `global` |
| 617 | `float` | `FileGetFloatValue` | `string KeyName, float missing = 0.0` | `global` |
| 620 | `string` | `FileGetStringValue` | `string KeyName, string missing = ""` | `global` |
| 623 | `Form` | `FileGetFormValue` | `string KeyName, Form missing = none` | `global` |
| 627 | `int` | `FileIntListAdd` | `string KeyName, int value, bool allowDuplicate = true` | `global` |
| 630 | `int` | `FileFloatListAdd` | `string KeyName, float value, bool allowDuplicate = true` | `global` |
| 633 | `int` | `FileStringListAdd` | `string KeyName, string value, bool allowDuplicate = true` | `global` |
| 636 | `int` | `FileFormListAdd` | `string KeyName, Form value, bool allowDuplicate = true` | `global` |
| 640 | `int` | `FileIntListAdjust` | `string KeyName, int index, int amount` | `global` |
| 643 | `float` | `FileFloatListAdjust` | `string KeyName, int index, float amount` | `global` |
| 647 | `int` | `FileIntListRemove` | `string KeyName, int value, bool allInstances = false` | `global` |
| 650 | `int` | `FileFloatListRemove` | `string KeyName, float value, bool allInstances = false` | `global` |
| 653 | `int` | `FileStringListRemove` | `string KeyName, string value, bool allInstances = false` | `global` |
| 656 | `int` | `FileFormListRemove` | `string KeyName, Form value, bool allInstances = false` | `global` |
| 660 | `int` | `FileIntListGet` | `string KeyName, int index` | `global` |
| 663 | `float` | `FileFloatListGet` | `string KeyName, int index` | `global` |
| 666 | `string` | `FileStringListGet` | `string KeyName, int index` | `global` |
| 669 | `Form` | `FileFormListGet` | `string KeyName, int index` | `global` |
| 673 | `int` | `FileIntListSet` | `string KeyName, int index, int value` | `global` |
| 676 | `float` | `FileFloatListSet` | `string KeyName, int index, float value` | `global` |
| 679 | `string` | `FileStringListSet` | `string KeyName, int index, string value` | `global` |
| 682 | `Form` | `FileFormListSet` | `string KeyName, int index, Form value` | `global` |
| 686 | `int` | `FileIntListClear` | `string KeyName` | `global` |
| 689 | `int` | `FileFloatListClear` | `string KeyName` | `global` |
| 692 | `int` | `FileStringListClear` | `string KeyName` | `global` |
| 695 | `int` | `FileFormListClear` | `string KeyName` | `global` |
| 699 | `bool` | `FileIntListRemoveAt` | `string KeyName, int index` | `global` |
| 702 | `bool` | `FileFloatListRemoveAt` | `string KeyName, int index` | `global` |
| 705 | `bool` | `FileStringListRemoveAt` | `string KeyName, int index` | `global` |
| 708 | `bool` | `FileFormListRemoveAt` | `string KeyName, int index` | `global` |
| 712 | `bool` | `FileIntListInsert` | `string KeyName, int index, int value` | `global` |
| 715 | `bool` | `FileFloatListInsert` | `string KeyName, int index, float value` | `global` |
| 718 | `bool` | `FileStringListInsert` | `string KeyName, int index, string value` | `global` |
| 721 | `bool` | `FileFormListInsert` | `string KeyName, int index, Form value` | `global` |
| 725 | `int` | `FileIntListCount` | `string KeyName` | `global` |
| 728 | `int` | `FileFloatListCount` | `string KeyName` | `global` |
| 731 | `int` | `FileStringListCount` | `string KeyName` | `global` |
| 734 | `int` | `FileFormListCount` | `string KeyName` | `global` |
| 738 | `int` | `FileIntListFind` | `string KeyName, int value` | `global` |
| 741 | `int` | `FileFloatListFind` | `string KeyName, float value` | `global` |
| 744 | `int` | `FileStringListFind` | `string KeyName, string value` | `global` |
| 747 | `int` | `FileFormListFind` | `string KeyName, Form value` | `global` |
| 751 | `bool` | `FileIntListHas` | `string KeyName, int value` | `global` |
| 754 | `bool` | `FileFloatListHas` | `string KeyName, float value` | `global` |
| 757 | `bool` | `FileStringListHas` | `string KeyName, string value` | `global` |
| 760 | `bool` | `FileFormListHas` | `string KeyName, Form value` | `global` |
| 764 | `void` | `FileIntListSlice` | `string KeyName, int[] slice, int startIndex = 0` | `global` |
| 767 | `void` | `FileFloatListSlice` | `string KeyName, float[] slice, int startIndex = 0` | `global` |
| 770 | `void` | `FileStringListSlice` | `string KeyName, string[] slice, int startIndex = 0` | `global` |
| 773 | `void` | `FileFormListSlice` | `string KeyName, Form[] slice, int startIndex = 0` | `global` |
| 777 | `int` | `FileIntListResize` | `string KeyName, int toLength, int filler = 0` | `global` |
| 780 | `int` | `FileFloatListResize` | `string KeyName, int toLength, float filler = 0.0` | `global` |
| 783 | `int` | `FileStringListResize` | `string KeyName, int toLength, string filler = ""` | `global` |
| 786 | `int` | `FileFormListResize` | `string KeyName, int toLength, Form filler = none` | `global` |
| 791 | `bool` | `FileIntListCopy` | `string KeyName, int[] copy` | `global` |
| 794 | `bool` | `FileFloatListCopy` | `string KeyName, float[] copy` | `global` |
| 797 | `bool` | `FileStringListCopy` | `string KeyName, string[] copy` | `global` |
| 800 | `bool` | `FileFormListCopy` | `string KeyName, Form[] copy` | `global` |
| 804 | `void` | `debug_SaveFile` | `` | `global` |
| 812 | `int` | `debug_FileGetIntKeysCount` | `` | `global` |
| 816 | `int` | `debug_FileGetFloatKeysCount` | `` | `global` |
| 820 | `int` | `debug_FileGetStringKeysCount` | `` | `global` |
| 824 | `int` | `debug_FileGetIntListKeysCount` | `` | `global` |
| 828 | `int` | `debug_FileGetFloatListKeysCount` | `` | `global` |
| 832 | `int` | `debug_FileGetStringListKeysCount` | `` | `global` |
| 836 | `string` | `debug_FileGetIntKey` | `int index` | `global` |
| 840 | `string` | `debug_FileGetFloatKey` | `int index` | `global` |
| 844 | `string` | `debug_FileGetStringKey` | `int index` | `global` |
| 848 | `string` | `debug_FileGetIntListKey` | `int index` | `global` |
| 852 | `string` | `debug_FileGetFloatListKey` | `int index` | `global` |
| 856 | `string` | `debug_FileGetStringListKey` | `int index` | `global` |
| 860 | `void` | `debug_FileDeleteAllValues` | `` | `global` |
| 863 | `void` | `debug_SetDebugMode` | `bool enabled` | `global` |
| 866 | `bool` | `ImportFile` | `string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false` | `global` |
| 869 | `bool` | `ExportFile` | `string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false, bool append = true` | `global` |

## Extracted total

**537 function declarations** across 6 PSC providers in this source snapshot.

## Persistence interpretation

- `StorageUtil` state and `JsonUtil` files have different persistence/ownership semantics.
- External JSON can outlive an ESS/new game.
- Dynamic list APIs are provider-managed collections, not native fixed Papyrus arrays.
- Durable consuming mods should version their storage/config schema and namespace keys.
