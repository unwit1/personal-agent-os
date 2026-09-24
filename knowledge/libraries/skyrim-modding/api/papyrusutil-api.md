# PapyrusUtil — Complete PSC API Catalog

Imported: 2026-09-24
Source: https://github.com/eeveelo/PapyrusUtil · ref `master`
Scripts: **6**
Declarations: **538** (537 functions, 0 events, 1 properties)
Native declarations: **420**
Global declarations: **537**
Status: generated source-derived API catalog

## ActorUtil

Source: `Scripts/Source/ActorUtil.psc` · blob `cff8e7b69c9f9edcb6f8051699c817e7d3d34b37`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `AddPackageOverride` | `function AddPackageOverride(Actor targetActor, Package targetPackage, int priority = 30, int flags = 0) global native` | 13 |
| function | `RemovePackageOverride` | `bool function RemovePackageOverride(Actor targetActor, Package targetPackage) global native` | 16 |
| function | `CountPackageOverride` | `int function CountPackageOverride(Actor targetActor) global native` | 19 |
| function | `ClearPackageOverride` | `int function ClearPackageOverride(Actor targetActor) global native` | 22 |
| function | `RemoveAllPackageOverride` | `int function RemoveAllPackageOverride(Package targetPackage) global native` | 25 |

## JsonUtil

Source: `Scripts/Source/JsonUtil.psc` · blob `7618e9f385daf60b94cde392015489fd585c6098`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `Load` | `bool function Load(string FileName) global native` | 33 |
| function | `Save` | `bool function Save(string FileName, bool minify = false) global native` | 34 |
| function | `Unload` | `bool function Unload(string FileName, bool saveChanges = true, bool minify = false) global native` | 35 |
| function | `IsPendingSave` | `bool function IsPendingSave(string FileName) global native` | 38 |
| function | `IsGood` | `bool function IsGood(string FileName) global native` | 40 |
| function | `GetErrors` | `string function GetErrors(string FileName) global native` | 42 |
| function | `JsonInFolder` | `string[] function JsonInFolder(string folderPath) global native` | 44 |
| function | `JsonExists` | `bool function JsonExists(string FileName) global` | 46 |
| function | `SetIntValue` | `int function SetIntValue(string FileName, string KeyName, int value) global native` | 56 |
| function | `SetFloatValue` | `float function SetFloatValue(string FileName, string KeyName, float value) global native` | 57 |
| function | `SetStringValue` | `string function SetStringValue(string FileName, string KeyName, string value) global native` | 58 |
| function | `SetFormValue` | `form function SetFormValue(string FileName, string KeyName, form value) global native` | 59 |
| function | `GetIntValue` | `int function GetIntValue(string FileName, string KeyName, int missing = 0) global native` | 61 |
| function | `GetFloatValue` | `float function GetFloatValue(string FileName, string KeyName, float missing = 0.0) global native` | 62 |
| function | `GetStringValue` | `string function GetStringValue(string FileName, string KeyName, string missing = "") global native` | 63 |
| function | `GetFormValue` | `form function GetFormValue(string FileName, string KeyName, form missing = none) global native` | 64 |
| function | `UnsetIntValue` | `bool function UnsetIntValue(string FileName, string KeyName) global native` | 66 |
| function | `UnsetFloatValue` | `bool function UnsetFloatValue(string FileName, string KeyName) global native` | 67 |
| function | `UnsetStringValue` | `bool function UnsetStringValue(string FileName, string KeyName) global native` | 68 |
| function | `UnsetFormValue` | `bool function UnsetFormValue(string FileName, string KeyName) global native` | 69 |
| function | `HasIntValue` | `bool function HasIntValue(string FileName, string KeyName) global native` | 71 |
| function | `HasFloatValue` | `bool function HasFloatValue(string FileName, string KeyName) global native` | 72 |
| function | `HasStringValue` | `bool function HasStringValue(string FileName, string KeyName) global native` | 73 |
| function | `HasFormValue` | `bool function HasFormValue(string FileName, string KeyName) global native` | 74 |
| function | `IntListAdd` | `int function IntListAdd(string FileName, string KeyName, int value, bool allowDuplicate = true) global native` | 76 |
| function | `FloatListAdd` | `int function FloatListAdd(string FileName, string KeyName, float value, bool allowDuplicate = true) global native` | 77 |
| function | `StringListAdd` | `int function StringListAdd(string FileName, string KeyName, String value, bool allowDuplicate = true) global native` | 78 |
| function | `FormListAdd` | `int function FormListAdd(string FileName, string KeyName, Form value, bool allowDuplicate = true) global native` | 79 |
| function | `IntListGet` | `Int function IntListGet(string FileName, string KeyName, int index) global native` | 81 |
| function | `FloatListGet` | `Float function FloatListGet(string FileName, string KeyName, int index) global native` | 82 |
| function | `StringListGet` | `String function StringListGet(string FileName, string KeyName, int index) global native` | 83 |
| function | `FormListGet` | `Form function FormListGet(string FileName, string KeyName, int index) global native` | 84 |
| function | `IntListSet` | `Int function IntListSet(string FileName, string KeyName, int index, int value) global native` | 86 |
| function | `FloatListSet` | `Float function FloatListSet(string FileName, string KeyName, int index, float value) global native` | 87 |
| function | `StringListSet` | `String function StringListSet(string FileName, string KeyName, int index, String value) global native` | 88 |
| function | `FormListSet` | `Form function FormListSet(string FileName, string KeyName, int index, Form value) global native` | 89 |
| function | `IntListRemove` | `int function IntListRemove(string FileName, string KeyName, int value, bool allInstances = true) global native` | 91 |
| function | `FloatListRemove` | `int function FloatListRemove(string FileName, string KeyName, float value, bool allInstances = true) global native` | 92 |
| function | `StringListRemove` | `int function StringListRemove(string FileName, string KeyName, String value, bool allInstances = true) global native` | 93 |
| function | `FormListRemove` | `int function FormListRemove(string FileName, string KeyName, Form value, bool allInstances = true) global native` | 94 |
| function | `IntListInsertAt` | `bool function IntListInsertAt(string FileName, string KeyName, int index, int value) global native` | 96 |
| function | `FloatListInsertAt` | `bool function FloatListInsertAt(string FileName, string KeyName, int index, float value) global native` | 97 |
| function | `StringListInsertAt` | `bool function StringListInsertAt(string FileName, string KeyName, int index, String value) global native` | 98 |
| function | `FormListInsertAt` | `bool function FormListInsertAt(string FileName, string KeyName, int index, Form value) global native` | 99 |
| function | `IntListRemoveAt` | `bool function IntListRemoveAt(string FileName, string KeyName, int index) global native` | 101 |
| function | `FloatListRemoveAt` | `bool function FloatListRemoveAt(string FileName, string KeyName, int index) global native` | 102 |
| function | `StringListRemoveAt` | `bool function StringListRemoveAt(string FileName, string KeyName, int index) global native` | 103 |
| function | `FormListRemoveAt` | `bool function FormListRemoveAt(string FileName, string KeyName, int index) global native` | 104 |
| function | `IntListClear` | `int function IntListClear(string FileName, string KeyName) global native` | 106 |
| function | `FloatListClear` | `int function FloatListClear(string FileName, string KeyName) global native` | 107 |
| function | `StringListClear` | `int function StringListClear(string FileName, string KeyName) global native` | 108 |
| function | `FormListClear` | `int function FormListClear(string FileName, string KeyName) global native` | 109 |
| function | `IntListCount` | `int function IntListCount(string FileName, string KeyName) global native` | 111 |
| function | `FloatListCount` | `int function FloatListCount(string FileName, string KeyName) global native` | 112 |
| function | `StringListCount` | `int function StringListCount(string FileName, string KeyName) global native` | 113 |
| function | `FormListCount` | `int function FormListCount(string FileName, string KeyName) global native` | 114 |
| function | `IntListCountValue` | `int function IntListCountValue(string FileName, string KeyName, int value, bool exclude = false) global native` | 116 |
| function | `FloatListCountValue` | `int function FloatListCountValue(string FileName, string KeyName, float value, bool exclude = false) global native` | 117 |
| function | `StringListCountValue` | `int function StringListCountValue(string FileName, string KeyName, String value, bool exclude = false) global native` | 118 |
| function | `FormListCountValue` | `int function FormListCountValue(string FileName, string KeyName, Form value, bool exclude = false) global native` | 119 |
| function | `IntListFind` | `int function IntListFind(string FileName, string KeyName, int value) global native` | 121 |
| function | `FloatListFind` | `int function FloatListFind(string FileName, string KeyName, float value) global native` | 122 |
| function | `StringListFind` | `int function StringListFind(string FileName, string KeyName, String value) global native` | 123 |
| function | `FormListFind` | `int function FormListFind(string FileName, string KeyName, Form value) global native` | 124 |
| function | `IntListHas` | `bool function IntListHas(string FileName, string KeyName, int value) global native` | 126 |
| function | `FloatListHas` | `bool function FloatListHas(string FileName, string KeyName, float value) global native` | 127 |
| function | `StringListHas` | `bool function StringListHas(string FileName, string KeyName, String value) global native` | 128 |
| function | `FormListHas` | `bool function FormListHas(string FileName, string KeyName, Form value) global native` | 129 |
| function | `IntListSlice` | `function IntListSlice(string FileName, string KeyName, int[] slice, int startIndex = 0) global native` | 131 |
| function | `FloatListSlice` | `function FloatListSlice(string FileName, string KeyName, float[] slice, int startIndex = 0) global native` | 132 |
| function | `StringListSlice` | `function StringListSlice(string FileName, string KeyName, string[] slice, int startIndex = 0) global native` | 133 |
| function | `FormListSlice` | `function FormListSlice(string FileName, string KeyName, Form[] slice, int startIndex = 0) global native` | 134 |
| function | `IntListResize` | `int function IntListResize(string FileName, string KeyName, int toLength, int filler = 0) global native` | 136 |
| function | `FloatListResize` | `int function FloatListResize(string FileName, string KeyName, int toLength, float filler = 0.0) global native` | 137 |
| function | `StringListResize` | `int function StringListResize(string FileName, string KeyName, int toLength, string filler = "") global native` | 138 |
| function | `FormListResize` | `int function FormListResize(string FileName, string KeyName, int toLength, Form filler = none) global native` | 139 |
| function | `IntListCopy` | `bool function IntListCopy(string FileName, string KeyName, int[] copy) global native` | 141 |
| function | `FloatListCopy` | `bool function FloatListCopy(string FileName, string KeyName, float[] copy) global native` | 142 |
| function | `StringListCopy` | `bool function StringListCopy(string FileName, string KeyName, string[] copy) global native` | 143 |
| function | `FormListCopy` | `bool function FormListCopy(string FileName, string KeyName, Form[] copy) global native` | 144 |
| function | `IntListToArray` | `int[] function IntListToArray(string FileName, string KeyName) global native` | 146 |
| function | `FloatListToArray` | `float[] function FloatListToArray(string FileName, string KeyName) global native` | 147 |
| function | `StringListToArray` | `string[] function StringListToArray(string FileName, string KeyName) global native` | 148 |
| function | `FormListToArray` | `Form[] function FormListToArray(string FileName, string KeyName) global native` | 149 |
| function | `AdjustIntValue` | `int function AdjustIntValue(string FileName, string KeyName, int amount) global native` | 151 |
| function | `AdjustFloatValue` | `float function AdjustFloatValue(string FileName, string KeyName, float amount) global native` | 152 |
| function | `IntListAdjust` | `Int function IntListAdjust(string FileName, string KeyName, int index, Int amount) global native` | 153 |
| function | `FloatListAdjust` | `float function FloatListAdjust(string FileName, string KeyName, int index, float amount) global native` | 154 |
| function | `IntListRandom` | `int function IntListRandom(string FileName, string KeyName) global native` | 156 |
| function | `FloatListRandom` | `float function FloatListRandom(string FileName, string KeyName) global native` | 157 |
| function | `StringListRandom` | `string function StringListRandom(string FileName, string KeyName) global native` | 158 |
| function | `FormListRandom` | `Form function FormListRandom(string FileName, string KeyName) global native` | 159 |
| function | `CountIntValuePrefix` | `int function CountIntValuePrefix(string FileName, string PrefixKey) global native` | 161 |
| function | `CountFloatValuePrefix` | `int function CountFloatValuePrefix(string FileName, string PrefixKey) global native` | 162 |
| function | `CountStringValuePrefix` | `int function CountStringValuePrefix(string FileName, string PrefixKey) global native` | 163 |
| function | `CountFormValuePrefix` | `int function CountFormValuePrefix(string FileName, string PrefixKey) global native` | 164 |
| function | `CountIntListPrefix` | `int function CountIntListPrefix(string FileName, string PrefixKey) global native` | 166 |
| function | `CountFloatListPrefix` | `int function CountFloatListPrefix(string FileName, string PrefixKey) global native` | 167 |
| function | `CountStringListPrefix` | `int function CountStringListPrefix(string FileName, string PrefixKey) global native` | 168 |
| function | `CountFormListPrefix` | `int function CountFormListPrefix(string FileName, string PrefixKey) global native` | 169 |
| function | `CountAllPrefix` | `int function CountAllPrefix(string FileName, string PrefixKey) global native` | 171 |
| function | `SetPathIntValue` | `function SetPathIntValue(string FileName, string Path, int value) global native` | 183 |
| function | `SetPathFloatValue` | `function SetPathFloatValue(string FileName, string Path, float value) global native` | 184 |
| function | `SetPathStringValue` | `function SetPathStringValue(string FileName, string Path, string value) global native` | 185 |
| function | `SetPathFormValue` | `function SetPathFormValue(string FileName, string Path, form value) global native` | 186 |
| function | `SetRawPathValue` | `bool function SetRawPathValue(string FileName, string Path, string RawJSON) global native` | 188 |
| function | `GetPathIntValue` | `int function GetPathIntValue(string FileName, string Path, int missing = 0) global native` | 190 |
| function | `GetPathFloatValue` | `float function GetPathFloatValue(string FileName, string Path, float missing = 0.0) global native` | 191 |
| function | `GetPathStringValue` | `string function GetPathStringValue(string FileName, string Path, string missing = "") global native` | 192 |
| function | `GetPathFormValue` | `form function GetPathFormValue(string FileName, string Path, form missing = none) global native` | 193 |
| function | `GetPathBoolValue` | `bool function GetPathBoolValue(string FileName, string Path, bool missing = false) global` | 194 |
| function | `PathIntElements` | `int[] function PathIntElements(string FileName, string Path, int invalidType = 0) global native` | 198 |
| function | `PathFloatElements` | `float[] function PathFloatElements(string FileName, string Path, float invalidType = 0.0) global native` | 199 |
| function | `PathStringElements` | `string[] function PathStringElements(string FileName, string Path, string invalidType = "") global native` | 200 |
| function | `PathFormElements` | `form[] function PathFormElements(string FileName, string Path, form invalidType = none) global native` | 201 |
| function | `FindPathIntElement` | `int function FindPathIntElement(string FileName, string Path, int toFind) global native` | 203 |
| function | `FindPathFloatElement` | `int function FindPathFloatElement(string FileName, string Path, float toFind) global native` | 204 |
| function | `FindPathStringElement` | `int function FindPathStringElement(string FileName, string Path, string toFind) global native` | 205 |
| function | `FindPathFormElement` | `int function FindPathFormElement(string FileName, string Path, form toFind) global native` | 206 |
| function | `PathCount` | `int function PathCount(string FileName, string Path) global native` | 208 |
| function | `PathMembers` | `string[] function PathMembers(string FileName, string Path) global native` | 209 |
| function | `CanResolvePath` | `bool function CanResolvePath(string FileName, string Path) global native` | 211 |
| function | `IsPathString` | `bool function IsPathString(string FileName, string Path) global native` | 212 |
| function | `IsPathNumber` | `bool function IsPathNumber(string FileName, string Path) global native` | 213 |
| function | `IsPathForm` | `bool function IsPathForm(string FileName, string Path) global native` | 214 |
| function | `IsPathBool` | `bool function IsPathBool(string FileName, string Path) global native` | 215 |
| function | `IsPathArray` | `bool function IsPathArray(string FileName, string Path) global native` | 216 |
| function | `IsPathObject` | `bool function IsPathObject(string FileName, string Path) global native` | 217 |
| function | `SetPathIntArray` | `function SetPathIntArray(string FileName, string Path, int[] arr, bool append = false) global native` | 219 |
| function | `SetPathFloatArray` | `function SetPathFloatArray(string FileName, string Path, float[] arr, bool append = false) global native` | 220 |
| function | `SetPathStringArray` | `function SetPathStringArray(string FileName, string Path, string[] arr, bool append = false) global native` | 221 |
| function | `SetPathFormArray` | `function SetPathFormArray(string FileName, string Path, form[] arr, bool append = false) global native` | 222 |
| function | `ClearPath` | `function ClearPath(string FileName, string Path) global native` | 224 |
| function | `ClearPathIndex` | `function ClearPathIndex(string FileName, string Path, int Index) global native` | 225 |
| function | `ClearAll` | `function ClearAll(string FileName) global native` | 228 |

## MiscUtil

Source: `Scripts/Source/MiscUtil.psc` · blob `ccbf5e6b59f7954ae525ba1c978d08900a2e03b3`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `ScanCellObjects` | `ObjectReference[] function ScanCellObjects(int formType, ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none) global native` | 11 |
| function | `ScanCellNPCs` | `Actor[] function ScanCellNPCs(ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none, bool IgnoreDead = true) global native` | 18 |
| function | `ScanCellNPCsByFaction` | `Actor[] function ScanCellNPCsByFaction(Faction FindFaction, ObjectReference CenterOn, float radius = 0.0, int minRank = 0, int maxRank = 127, bool IgnoreDead = true) global native` | 22 |
| function | `ToggleFreeCamera` | `function ToggleFreeCamera(bool stopTime = false) global native` | 30 |
| function | `SetFreeCameraSpeed` | `function SetFreeCameraSpeed(float speed) global native` | 32 |
| function | `SetFreeCameraState` | `function SetFreeCameraState(bool enable, float speed = 10.0) global native` | 35 |
| function | `FilesInFolder` | `string[] function FilesInFolder(string directory, string extension="*") global native` | 47 |
| function | `FoldersInFolder` | `string[] function FoldersInFolder(string directory) global native` | 51 |
| function | `FileExists` | `bool function FileExists(string fileName) global native` | 54 |
| function | `ReadFromFile` | `string function ReadFromFile(string fileName) global native` | 58 |
| function | `WriteToFile` | `bool function WriteToFile(string fileName, string text, bool append = true, bool timestamp = false) global native` | 61 |
| function | `PrintConsole` | `function PrintConsole(string text) global native` | 69 |
| function | `GetRaceEditorID` | `string function GetRaceEditorID(Race raceForm) global native` | 72 |
| function | `GetActorRaceEditorID` | `string function GetActorRaceEditorID(Actor actorRef) global native` | 75 |
| function | `SetMenus` | `function SetMenus(bool enabled) global native` | 78 |
| function | `GetNodeRotation` | `float function GetNodeRotation(ObjectReference obj, string nodeName, bool firstPerson, int rotationIndex) global` | 85 |
| function | `ExecuteBat` | `function ExecuteBat(string fileName) global` | 92 |
| function | `ScanCellActors` | `Actor[] function ScanCellActors(ObjectReference CenterOn, float radius = 5000.0, Keyword HasKeyword = none) global` | 97 |

## ObjectUtil

Source: `Scripts/Source/ObjectUtil.psc` · blob `5f7be6a55a1b060efc4c58da7f56c905c7ba65f6`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| property | `laughIdle` | `Idle Property laughIdle Auto` | 8 |

## PapyrusUtil

Source: `Scripts/Source/PapyrusUtil.psc` · blob `9f8c370b3f2a170d9ddd9d627f47df9850bf1f50`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `GetVersion` | `int function GetVersion() global native` | 4 |
| function | `GetScriptVersion` | `int function GetScriptVersion() global` | 7 |
| function | `ActorArray` | `Actor[] function ActorArray(int size, Actor filler = none) global native` | 16 |
| function | `ResizeActorArray` | `Actor[] function ResizeActorArray(Actor[] ArrayValues, int toSize, Actor filler = none) global native` | 17 |
| function | `ObjRefArray` | `ObjectReference[] function ObjRefArray(int size, ObjectReference filler = none) global native` | 18 |
| function | `ResizeObjRefArray` | `ObjectReference[] function ResizeObjRefArray(ObjectReference[] ArrayValues, int toSize, ObjectReference filler = none) global native` | 19 |
| function | `PushFloat` | `float[] function PushFloat(float[] ArrayValues, float push) global native` | 24 |
| function | `PushInt` | `int[] function PushInt(int[] ArrayValues, int push) global native` | 25 |
| function | `PushString` | `string[] function PushString(string[] ArrayValues, string push) global native` | 27 |
| function | `PushForm` | `Form[] function PushForm(Form[] ArrayValues, Form push) global native` | 28 |
| function | `PushAlias` | `Alias[] function PushAlias(Alias[] ArrayValues, Alias push) global native` | 29 |
| function | `PushActor` | `Actor[] function PushActor(Actor[] ArrayValues, Actor push) global native` | 30 |
| function | `PushObjRef` | `ObjectReference[] function PushObjRef(ObjectReference[] ArrayValues, ObjectReference push) global native` | 31 |
| function | `RemoveFloat` | `float[] function RemoveFloat(float[] ArrayValues, float ToRemove) global native` | 34 |
| function | `RemoveInt` | `int[] function RemoveInt(int[] ArrayValues, int ToRemove) global native` | 35 |
| function | `RemoveString` | `string[] function RemoveString(string[] ArrayValues, string ToRemove) global native` | 37 |
| function | `RemoveForm` | `Form[] function RemoveForm(Form[] ArrayValues, Form ToRemove) global native` | 38 |
| function | `RemoveAlias` | `Alias[] function RemoveAlias(Alias[] ArrayValues, Alias ToRemove) global native` | 39 |
| function | `RemoveActor` | `Actor[] function RemoveActor(Actor[] ArrayValues, Actor ToRemove) global native` | 40 |
| function | `RemoveObjRef` | `ObjectReference[] function RemoveObjRef(ObjectReference[] ArrayValues, ObjectReference ToRemove) global native` | 41 |
| function | `RemoveDupeFloat` | `float[] function RemoveDupeFloat(float[] ArrayValues) global native` | 44 |
| function | `RemoveDupeInt` | `int[] function RemoveDupeInt(int[] ArrayValues) global native` | 45 |
| function | `RemoveDupeString` | `string[] function RemoveDupeString(string[] ArrayValues) global native` | 46 |
| function | `RemoveDupeForm` | `Form[] function RemoveDupeForm(Form[] ArrayValues) global native` | 47 |
| function | `RemoveDupeAlias` | `Alias[] function RemoveDupeAlias(Alias[] ArrayValues) global native` | 48 |
| function | `RemoveDupeActor` | `Actor[] function RemoveDupeActor(Actor[] ArrayValues) global native` | 49 |
| function | `RemoveDupeObjRef` | `ObjectReference[] function RemoveDupeObjRef(ObjectReference[] ArrayValues) global native` | 50 |
| function | `GetDiffFloat` | `float[] function GetDiffFloat(float[] ArrayValues1, float[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 55 |
| function | `GetDiffInt` | `int[] function GetDiffInt(int[] ArrayValues1, int[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 56 |
| function | `GetDiffString` | `string[] function GetDiffString(string[] ArrayValues1, string[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 57 |
| function | `GetDiffForm` | `Form[] function GetDiffForm(Form[] ArrayValues1, Form[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 58 |
| function | `GetDiffAlias` | `Alias[] function GetDiffAlias(Alias[] ArrayValues1, Alias[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 59 |
| function | `GetDiffActor` | `Actor[] function GetDiffActor(Actor[] ArrayValues1, Actor[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 60 |
| function | `GetDiffObjRef` | `ObjectReference[] function GetDiffObjRef(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` | 61 |
| function | `GetMatchingFloat` | `float[] function GetMatchingFloat(float[] ArrayValues1, float[] ArrayValues2) global native` | 64 |
| function | `GetMatchingInt` | `int[] function GetMatchingInt(int[] ArrayValues1, int[] ArrayValues2) global native` | 65 |
| function | `GetMatchingString` | `string[] function GetMatchingString(string[] ArrayValues1, string[] ArrayValues2) global native` | 66 |
| function | `GetMatchingForm` | `Form[] function GetMatchingForm(Form[] ArrayValues1, Form[] ArrayValues2) global native` | 67 |
| function | `GetMatchingAlias` | `Alias[] function GetMatchingAlias(Alias[] ArrayValues1, Alias[] ArrayValues2) global native` | 68 |
| function | `GetMatchingActor` | `Actor[] function GetMatchingActor(Actor[] ArrayValues1, Actor[] ArrayValues2) global native` | 69 |
| function | `GetMatchingObjRef` | `ObjectReference[] function GetMatchingObjRef(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2) global native` | 70 |
| function | `CountFloat` | `int function CountFloat(float[] ArrayValues, float EqualTo) global native` | 73 |
| function | `CountInt` | `int function CountInt(int[] ArrayValues, int EqualTo) global native` | 74 |
| function | `CountBool` | `int function CountBool(bool[] ArrayValues, bool EqualTo) global native` | 75 |
| function | `CountString` | `int function CountString(string[] ArrayValues, string EqualTo) global native` | 76 |
| function | `CountForm` | `int function CountForm(Form[] ArrayValues, Form EqualTo) global native` | 77 |
| function | `CountAlias` | `int function CountAlias(Alias[] ArrayValues, Alias EqualTo) global native` | 78 |
| function | `CountActor` | `int function CountActor(Actor[] ArrayValues, Actor EqualTo) global native` | 79 |
| function | `CountObjRef` | `int function CountObjRef(ObjectReference[] ArrayValues, ObjectReference EqualTo) global native` | 80 |
| function | `MergeFloatArray` | `float[] function MergeFloatArray(float[] ArrayValues1, float[] ArrayValues2, bool RemoveDupes = false) global native` | 83 |
| function | `MergeIntArray` | `int[] function MergeIntArray(int[] ArrayValues1, int[] ArrayValues2, bool RemoveDupes = false) global native` | 84 |
| function | `MergeStringArray` | `string[] function MergeStringArray(string[] ArrayValues1, string[] ArrayValues2, bool RemoveDupes = false) global native` | 86 |
| function | `MergeFormArray` | `Form[] function MergeFormArray(Form[] ArrayValues1, Form[] ArrayValues2, bool RemoveDupes = false) global native` | 87 |
| function | `MergeAliasArray` | `Alias[] function MergeAliasArray(Alias[] ArrayValues1, Alias[] ArrayValues2, bool RemoveDupes = false) global native` | 88 |
| function | `MergeActorArray` | `Actor[] function MergeActorArray(Actor[] ArrayValues1, Actor[] ArrayValues2, bool RemoveDupes = false) global native` | 89 |
| function | `MergeObjRefArray` | `ObjectReference[] function MergeObjRefArray(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool RemoveDupes = false) global native` | 90 |
| function | `SliceFloatArray` | `float[] function SliceFloatArray(float[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 94 |
| function | `SliceIntArray` | `int[] function SliceIntArray(int[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 95 |
| function | `SliceStringArray` | `string[] function SliceStringArray(string[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 97 |
| function | `SliceFormArray` | `Form[] function SliceFormArray(Form[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 98 |
| function | `SliceAliasArray` | `Alias[] function SliceAliasArray(Alias[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 99 |
| function | `SliceActorArray` | `Actor[] function SliceActorArray(Actor[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 100 |
| function | `SliceObjRefArray` | `ObjectReference[] function SliceObjRefArray(ObjectReference[] ArrayValues, int StartIndex, int EndIndex = -1) global native` | 101 |
| function | `SortIntArray` | `function SortIntArray(int[] ArrayValues, bool descending = false) global native` | 105 |
| function | `SortFloatArray` | `function SortFloatArray(float[] ArrayValues, bool descending = false) global native` | 106 |
| function | `SortStringArray` | `function SortStringArray(string[] ArrayValues, bool descending = false) global native` | 107 |
| function | `ClearEmpty` | `string[] function ClearEmpty(string[] ArrayValues) global` | 113 |
| function | `ClearNone` | `Form[] function ClearNone(Form[] ArrayValues) global` | 116 |
| function | `CountFalse` | `int function CountFalse(bool[] ArrayValues) global` | 120 |
| function | `CountTrue` | `int function CountTrue(bool[] ArrayValues) global` | 123 |
| function | `CountNone` | `int function CountNone(Form[] ArrayValues) global` | 126 |
| function | `StringSplit` | `string[] function StringSplit(string ArgString, string Delimiter = ",") global native` | 135 |
| function | `StringJoin` | `string function StringJoin(string[] Values, string Delimiter = ",") global native` | 138 |
| function | `AddIntValues` | `int function AddIntValues(int[] Values) global native` | 147 |
| function | `AddFloatValues` | `float function AddFloatValues(float[] Values) global native` | 148 |
| function | `ClampInt` | `int function ClampInt(int value, int min, int max) global native` | 151 |
| function | `ClampFloat` | `float function ClampFloat(float value, float min, float max) global native` | 152 |
| function | `WrapInt` | `int function WrapInt(int value, int end, int start = 0) global native` | 157 |
| function | `WrapFloat` | `float function WrapFloat(float value, float end, float start = 0.0) global native` | 158 |
| function | `SignInt` | `int function SignInt(bool doSign, int value) global native` | 161 |
| function | `SignFloat` | `float function SignFloat(bool doSign, float value) global native` | 162 |
| function | `ResizeBoolArray` | `bool[] function ResizeBoolArray(bool[] ArrayValues, int toSize, bool filler = false) global` | 169 |
| function | `PushBool` | `bool[] function PushBool(bool[] ArrayValues, bool push) global` | 182 |
| function | `RemoveBool` | `bool[] function RemoveBool(bool[] ArrayValues, bool ToRemove) global` | 186 |
| function | `MergeBoolArray` | `bool[] function MergeBoolArray(bool[] ArrayValues1, bool[] ArrayValues2, bool RemoveDupes = false) global` | 191 |
| function | `SliceBoolArray` | `bool[] function SliceBoolArray(bool[] ArrayValues, int StartIndex, int EndIndex = -1) global` | 223 |
| function | `FloatArray` | `float[] function FloatArray(int size, float filler = 0.0) global` | 254 |
| function | `IntArray` | `int[] function IntArray(int size, int filler = 0) global` | 257 |
| function | `BoolArray` | `bool[] function BoolArray(int size, bool filler = false) global` | 260 |
| function | `StringArray` | `string[] function StringArray(int size, string filler = "") global` | 263 |
| function | `FormArray` | `Form[] function FormArray(int size, Form filler = none) global` | 266 |
| function | `AliasArray` | `Alias[] function AliasArray(int size, Alias filler = none) global` | 269 |
| function | `ResizeFloatArray` | `float[] function ResizeFloatArray(float[] ArrayValues, int toSize, float filler = 0.0) global` | 273 |
| function | `ResizeIntArray` | `int[] function ResizeIntArray(int[] ArrayValues, int toSize, int filler = 0) global` | 276 |
| function | `ResizeStringArray` | `string[] function ResizeStringArray(string[] ArrayValues, int toSize, string filler = "") global` | 279 |
| function | `ResizeFormArray` | `Form[] function ResizeFormArray(Form[] ArrayValues, int toSize, Form filler = none) global` | 282 |
| function | `ResizeAliasArray` | `Alias[] function ResizeAliasArray(Alias[] ArrayValues, int toSize, Alias filler = none) global` | 285 |

## StorageUtil

Source: `Scripts/Source/StorageUtil.psc` · blob `c309fef20cf56342c5ee0ed53f5d146af51bc940`

| Kind | Name | Declaration | Line |
|---|---|---|---:|
| function | `SetIntValue` | `int function SetIntValue(Form ObjKey, string KeyName, int value) global native` | 77 |
| function | `SetFloatValue` | `float function SetFloatValue(Form ObjKey, string KeyName, float value) global native` | 78 |
| function | `SetStringValue` | `string function SetStringValue(Form ObjKey, string KeyName, string value) global native` | 79 |
| function | `SetFormValue` | `Form function SetFormValue(Form ObjKey, string KeyName, Form value) global native` | 80 |
| function | `UnsetIntValue` | `bool function UnsetIntValue(Form ObjKey, string KeyName) global native` | 89 |
| function | `UnsetFloatValue` | `bool function UnsetFloatValue(Form ObjKey, string KeyName) global native` | 90 |
| function | `UnsetStringValue` | `bool function UnsetStringValue(Form ObjKey, string KeyName) global native` | 91 |
| function | `UnsetFormValue` | `bool function UnsetFormValue(Form ObjKey, string KeyName) global native` | 92 |
| function | `HasIntValue` | `bool function HasIntValue(Form ObjKey, string KeyName) global native` | 100 |
| function | `HasFloatValue` | `bool function HasFloatValue(Form ObjKey, string KeyName) global native` | 101 |
| function | `HasStringValue` | `bool function HasStringValue(Form ObjKey, string KeyName) global native` | 102 |
| function | `HasFormValue` | `bool function HasFormValue(Form ObjKey, string KeyName) global native` | 103 |
| function | `GetIntValue` | `int function GetIntValue(Form ObjKey, string KeyName, int missing = 0) global native` | 112 |
| function | `GetFloatValue` | `float function GetFloatValue(Form ObjKey, string KeyName, float missing = 0.0) global native` | 113 |
| function | `GetStringValue` | `string function GetStringValue(Form ObjKey, string KeyName, string missing = "") global native` | 114 |
| function | `GetFormValue` | `Form function GetFormValue(Form ObjKey, string KeyName, Form missing = none) global native` | 115 |
| function | `PluckIntValue` | `int function PluckIntValue(Form ObjKey, string KeyName, int missing = 0) global native` | 124 |
| function | `PluckFloatValue` | `float function PluckFloatValue(Form ObjKey, string KeyName, float missing = 0.0) global native` | 125 |
| function | `PluckStringValue` | `string function PluckStringValue(Form ObjKey, string KeyName, string missing = "") global native` | 126 |
| function | `PluckFormValue` | `Form function PluckFormValue(Form ObjKey, string KeyName, Form missing = none) global native` | 127 |
| function | `AdjustIntValue` | `int function AdjustIntValue(Form ObjKey, string KeyName, int amount) global native` | 137 |
| function | `AdjustFloatValue` | `float function AdjustFloatValue(Form ObjKey, string KeyName, float amount) global native` | 138 |
| function | `IntListAdd` | `int function IntListAdd(Form ObjKey, string KeyName, int value, bool allowDuplicate = true) global native` | 150 |
| function | `FloatListAdd` | `int function FloatListAdd(Form ObjKey, string KeyName, float value, bool allowDuplicate = true) global native` | 151 |
| function | `StringListAdd` | `int function StringListAdd(Form ObjKey, string KeyName, string value, bool allowDuplicate = true) global native` | 152 |
| function | `FormListAdd` | `int function FormListAdd(Form ObjKey, string KeyName, Form value, bool allowDuplicate = true) global native` | 153 |
| function | `IntListGet` | `int function IntListGet(Form ObjKey, string KeyName, int index) global native` | 162 |
| function | `FloatListGet` | `float function FloatListGet(Form ObjKey, string KeyName, int index) global native` | 163 |
| function | `StringListGet` | `string function StringListGet(Form ObjKey, string KeyName, int index) global native` | 164 |
| function | `FormListGet` | `Form function FormListGet(Form ObjKey, string KeyName, int index) global native` | 165 |
| function | `IntListSet` | `int function IntListSet(Form ObjKey, string KeyName, int index, int value) global native` | 175 |
| function | `FloatListSet` | `float function FloatListSet(Form ObjKey, string KeyName, int index, float value) global native` | 176 |
| function | `StringListSet` | `string function StringListSet(Form ObjKey, string KeyName, int index, string value) global native` | 177 |
| function | `FormListSet` | `Form function FormListSet(Form ObjKey, string KeyName, int index, Form value) global native` | 178 |
| function | `IntListPluck` | `int function IntListPluck(Form ObjKey, string KeyName, int index, int missing) global native` | 188 |
| function | `FloatListPluck` | `float function FloatListPluck(Form ObjKey, string KeyName, int index, float missing) global native` | 189 |
| function | `StringListPluck` | `string function StringListPluck(Form ObjKey, string KeyName, int index, string missing) global native` | 190 |
| function | `FormListPluck` | `Form function FormListPluck(Form ObjKey, string KeyName, int index, Form missing) global native` | 191 |
| function | `IntListShift` | `int function IntListShift(Form ObjKey, string KeyName) global native` | 198 |
| function | `FloatListShift` | `float function FloatListShift(Form ObjKey, string KeyName) global native` | 199 |
| function | `StringListShift` | `string function StringListShift(Form ObjKey, string KeyName) global native` | 200 |
| function | `FormListShift` | `Form function FormListShift(Form ObjKey, string KeyName) global native` | 201 |
| function | `IntListPop` | `int function IntListPop(Form ObjKey, string KeyName) global native` | 208 |
| function | `FloatListPop` | `float function FloatListPop(Form ObjKey, string KeyName) global native` | 209 |
| function | `StringListPop` | `string function StringListPop(Form ObjKey, string KeyName) global native` | 210 |
| function | `FormListPop` | `Form function FormListPop(Form ObjKey, string KeyName) global native` | 211 |
| function | `IntListAdjust` | `int function IntListAdjust(Form ObjKey, string KeyName, int index, int amount) global native` | 222 |
| function | `FloatListAdjust` | `float function FloatListAdjust(Form ObjKey, string KeyName, int index, float amount) global native` | 223 |
| function | `IntListInsert` | `bool function IntListInsert(Form ObjKey, string KeyName, int index, int value) global native` | 233 |
| function | `FloatListInsert` | `bool function FloatListInsert(Form ObjKey, string KeyName, int index, float value) global native` | 234 |
| function | `StringListInsert` | `bool function StringListInsert(Form ObjKey, string KeyName, int index, string value) global native` | 235 |
| function | `FormListInsert` | `bool function FormListInsert(Form ObjKey, string KeyName, int index, Form value) global native` | 236 |
| function | `IntListRemove` | `int function IntListRemove(Form ObjKey, string KeyName, int value, bool allInstances = false) global native` | 247 |
| function | `FloatListRemove` | `int function FloatListRemove(Form ObjKey, string KeyName, float value, bool allInstances = false) global native` | 248 |
| function | `StringListRemove` | `int function StringListRemove(Form ObjKey, string KeyName, string value, bool allInstances = false) global native` | 249 |
| function | `FormListRemove` | `int function FormListRemove(Form ObjKey, string KeyName, Form value, bool allInstances = false) global native` | 250 |
| function | `IntListClear` | `int function IntListClear(Form ObjKey, string KeyName) global native` | 259 |
| function | `FloatListClear` | `int function FloatListClear(Form ObjKey, string KeyName) global native` | 260 |
| function | `StringListClear` | `int function StringListClear(Form ObjKey, string KeyName) global native` | 261 |
| function | `FormListClear` | `int function FormListClear(Form ObjKey, string KeyName) global native` | 262 |
| function | `IntListRemoveAt` | `bool function IntListRemoveAt(Form ObjKey, string KeyName, int index) global native` | 271 |
| function | `FloatListRemoveAt` | `bool function FloatListRemoveAt(Form ObjKey, string KeyName, int index) global native` | 272 |
| function | `StringListRemoveAt` | `bool function StringListRemoveAt(Form ObjKey, string KeyName, int index) global native` | 273 |
| function | `FormListRemoveAt` | `bool function FormListRemoveAt(Form ObjKey, string KeyName, int index) global native` | 274 |
| function | `IntListCount` | `int function IntListCount(Form ObjKey, string KeyName) global native` | 281 |
| function | `FloatListCount` | `int function FloatListCount(Form ObjKey, string KeyName) global native` | 282 |
| function | `StringListCount` | `int function StringListCount(Form ObjKey, string KeyName) global native` | 283 |
| function | `FormListCount` | `int function FormListCount(Form ObjKey, string KeyName) global native` | 284 |
| function | `IntListCountValue` | `int function IntListCountValue(Form ObjKey, string KeyName, int value, bool exclude = false) global native` | 293 |
| function | `FloatListCountValue` | `int function FloatListCountValue(Form ObjKey, string KeyName, float value, bool exclude = false) global native` | 294 |
| function | `StringListCountValue` | `int function StringListCountValue(Form ObjKey, string KeyName, string value, bool exclude = false) global native` | 295 |
| function | `FormListCountValue` | `int function FormListCountValue(Form ObjKey, string KeyName, Form value, bool exclude = false) global native` | 296 |
| function | `IntListFind` | `int function IntListFind(Form ObjKey, string KeyName, int value) global native` | 305 |
| function | `FloatListFind` | `int function FloatListFind(Form ObjKey, string KeyName, float value) global native` | 306 |
| function | `StringListFind` | `int function StringListFind(Form ObjKey, string KeyName, string value) global native` | 307 |
| function | `FormListFind` | `int function FormListFind(Form ObjKey, string KeyName, Form value) global native` | 308 |
| function | `IntListHas` | `bool function IntListHas(Form ObjKey, string KeyName, int value) global native` | 317 |
| function | `FloatListHas` | `bool function FloatListHas(Form ObjKey, string KeyName, float value) global native` | 318 |
| function | `StringListHas` | `bool function StringListHas(Form ObjKey, string KeyName, string value) global native` | 319 |
| function | `FormListHas` | `bool function FormListHas(Form ObjKey, string KeyName, Form value) global native` | 320 |
| function | `IntListSort` | `function IntListSort(Form ObjKey, string KeyName) global native` | 327 |
| function | `FloatListSort` | `function FloatListSort(Form ObjKey, string KeyName) global native` | 328 |
| function | `StringListSort` | `function StringListSort(Form ObjKey, string KeyName) global native` | 329 |
| function | `FormListSort` | `function FormListSort(Form ObjKey, string KeyName) global native` | 330 |
| function | `IntListSlice` | `function IntListSlice(Form ObjKey, string KeyName, int[] slice, int startIndex = 0) global native` | 341 |
| function | `FloatListSlice` | `function FloatListSlice(Form ObjKey, string KeyName, float[] slice, int startIndex = 0) global native` | 342 |
| function | `StringListSlice` | `function StringListSlice(Form ObjKey, string KeyName, string[] slice, int startIndex = 0) global native` | 343 |
| function | `FormListSlice` | `function FormListSlice(Form ObjKey, string KeyName, Form[] slice, int startIndex = 0) global native` | 344 |
| function | `IntListResize` | `int function IntListResize(Form ObjKey, string KeyName, int toLength, int filler = 0) global native` | 358 |
| function | `FloatListResize` | `int function FloatListResize(Form ObjKey, string KeyName, int toLength, float filler = 0.0) global native` | 359 |
| function | `StringListResize` | `int function StringListResize(Form ObjKey, string KeyName, int toLength, string filler = "") global native` | 360 |
| function | `FormListResize` | `int function FormListResize(Form ObjKey, string KeyName, int toLength, Form filler = none) global native` | 361 |
| function | `IntListCopy` | `bool function IntListCopy(Form ObjKey, string KeyName, int[] copy) global native` | 373 |
| function | `FloatListCopy` | `bool function FloatListCopy(Form ObjKey, string KeyName, float[] copy) global native` | 374 |
| function | `StringListCopy` | `bool function StringListCopy(Form ObjKey, string KeyName, string[] copy) global native` | 375 |
| function | `FormListCopy` | `bool function FormListCopy(Form ObjKey, string KeyName, Form[] copy) global native` | 376 |
| function | `IntListToArray` | `int[] function IntListToArray(Form ObjKey, string KeyName) global native` | 385 |
| function | `FloatListToArray` | `float[] function FloatListToArray(Form ObjKey, string KeyName) global native` | 386 |
| function | `StringListToArray` | `string[] function StringListToArray(Form ObjKey, string KeyName) global native` | 387 |
| function | `FormListToArray` | `Form[] function FormListToArray(Form ObjKey, string KeyName) global native` | 388 |
| function | `IntListRandom` | `int function IntListRandom(Form ObjKey, string KeyName) global native` | 398 |
| function | `FloatListRandom` | `float function FloatListRandom(Form ObjKey, string KeyName) global native` | 399 |
| function | `StringListRandom` | `string function StringListRandom(Form ObjKey, string KeyName) global native` | 400 |
| function | `FormListRandom` | `Form function FormListRandom(Form ObjKey, string KeyName) global native` | 401 |
| function | `FormListFilterByTypes` | `Form[] function FormListFilterByTypes(Form ObjKey, string KeyName, int[] FormTypeIDs, bool ReturnMatching = true) global native` | 412 |
| function | `FormListFilterByType` | `Form[] function FormListFilterByType(Form ObjKey, string KeyName, int FormTypeID, bool ReturnMatching = true) global` | 414 |
| function | `CountIntValuePrefix` | `int function CountIntValuePrefix(string PrefixKey) global native` | 424 |
| function | `CountFloatValuePrefix` | `int function CountFloatValuePrefix(string PrefixKey) global native` | 425 |
| function | `CountStringValuePrefix` | `int function CountStringValuePrefix(string PrefixKey) global native` | 426 |
| function | `CountFormValuePrefix` | `int function CountFormValuePrefix(string PrefixKey) global native` | 427 |
| function | `CountIntListPrefix` | `int function CountIntListPrefix(string PrefixKey) global native` | 429 |
| function | `CountFloatListPrefix` | `int function CountFloatListPrefix(string PrefixKey) global native` | 430 |
| function | `CountStringListPrefix` | `int function CountStringListPrefix(string PrefixKey) global native` | 431 |
| function | `CountFormListPrefix` | `int function CountFormListPrefix(string PrefixKey) global native` | 432 |
| function | `CountAllPrefix` | `int function CountAllPrefix(string PrefixKey) global native` | 435 |
| function | `CountObjIntValuePrefix` | `int function CountObjIntValuePrefix(Form ObjKey, string PrefixKey) global native` | 442 |
| function | `CountObjFloatValuePrefix` | `int function CountObjFloatValuePrefix(Form ObjKey, string PrefixKey) global native` | 443 |
| function | `CountObjStringValuePrefix` | `int function CountObjStringValuePrefix(Form ObjKey, string PrefixKey) global native` | 444 |
| function | `CountObjFormValuePrefix` | `int function CountObjFormValuePrefix(Form ObjKey, string PrefixKey) global native` | 445 |
| function | `CountObjIntListPrefix` | `int function CountObjIntListPrefix(Form ObjKey, string PrefixKey) global native` | 447 |
| function | `CountObjFloatListPrefix` | `int function CountObjFloatListPrefix(Form ObjKey, string PrefixKey) global native` | 448 |
| function | `CountObjStringListPrefix` | `int function CountObjStringListPrefix(Form ObjKey, string PrefixKey) global native` | 449 |
| function | `CountObjFormListPrefix` | `int function CountObjFormListPrefix(Form ObjKey, string PrefixKey) global native` | 450 |
| function | `CountAllObjPrefix` | `int function CountAllObjPrefix(Form ObjKey, string PrefixKey) global native` | 453 |
| function | `ClearIntValuePrefix` | `int function ClearIntValuePrefix(string PrefixKey) global native` | 461 |
| function | `ClearFloatValuePrefix` | `int function ClearFloatValuePrefix(string PrefixKey) global native` | 462 |
| function | `ClearStringValuePrefix` | `int function ClearStringValuePrefix(string PrefixKey) global native` | 463 |
| function | `ClearFormValuePrefix` | `int function ClearFormValuePrefix(string PrefixKey) global native` | 464 |
| function | `ClearIntListPrefix` | `int function ClearIntListPrefix(string PrefixKey) global native` | 466 |
| function | `ClearFloatListPrefix` | `int function ClearFloatListPrefix(string PrefixKey) global native` | 467 |
| function | `ClearStringListPrefix` | `int function ClearStringListPrefix(string PrefixKey) global native` | 468 |
| function | `ClearFormListPrefix` | `int function ClearFormListPrefix(string PrefixKey) global native` | 469 |
| function | `ClearAllPrefix` | `int function ClearAllPrefix(string PrefixKey) global native` | 472 |
| function | `ClearObjIntValuePrefix` | `int function ClearObjIntValuePrefix(Form ObjKey, string PrefixKey) global native` | 481 |
| function | `ClearObjFloatValuePrefix` | `int function ClearObjFloatValuePrefix(Form ObjKey, string PrefixKey) global native` | 482 |
| function | `ClearObjStringValuePrefix` | `int function ClearObjStringValuePrefix(Form ObjKey, string PrefixKey) global native` | 483 |
| function | `ClearObjFormValuePrefix` | `int function ClearObjFormValuePrefix(Form ObjKey, string PrefixKey) global native` | 484 |
| function | `ClearObjIntListPrefix` | `int function ClearObjIntListPrefix(Form ObjKey, string PrefixKey) global native` | 486 |
| function | `ClearObjFloatListPrefix` | `int function ClearObjFloatListPrefix(Form ObjKey, string PrefixKey) global native` | 487 |
| function | `ClearObjStringListPrefix` | `int function ClearObjStringListPrefix(Form ObjKey, string PrefixKey) global native` | 488 |
| function | `ClearObjFormListPrefix` | `int function ClearObjFormListPrefix(Form ObjKey, string PrefixKey) global native` | 489 |
| function | `ClearAllObjPrefix` | `int function ClearAllObjPrefix(Form ObjKey, string PrefixKey) global native` | 492 |
| function | `debug_DeleteValues` | `function debug_DeleteValues(Form ObjKey) global native` | 498 |
| function | `debug_DeleteAllValues` | `function debug_DeleteAllValues() global native` | 499 |
| function | `debug_Cleanup` | `int function debug_Cleanup() global native` | 501 |
| function | `debug_AllIntObjs` | `Form[] function debug_AllIntObjs() global native` | 503 |
| function | `debug_AllFloatObjs` | `Form[] function debug_AllFloatObjs() global native` | 504 |
| function | `debug_AllStringObjs` | `Form[] function debug_AllStringObjs() global native` | 505 |
| function | `debug_AllFormObjs` | `Form[] function debug_AllFormObjs() global native` | 506 |
| function | `debug_AllIntListObjs` | `Form[] function debug_AllIntListObjs() global native` | 507 |
| function | `debug_AllFloatListObjs` | `Form[] function debug_AllFloatListObjs() global native` | 508 |
| function | `debug_AllStringListObjs` | `Form[] function debug_AllStringListObjs() global native` | 509 |
| function | `debug_AllFormListObjs` | `Form[] function debug_AllFormListObjs() global native` | 510 |
| function | `debug_AllObjIntKeys` | `string[] function debug_AllObjIntKeys(Form ObjKey) global native` | 512 |
| function | `debug_AllObjFloatKeys` | `string[] function debug_AllObjFloatKeys(Form ObjKey) global native` | 513 |
| function | `debug_AllObjStringKeys` | `string[] function debug_AllObjStringKeys(Form ObjKey) global native` | 514 |
| function | `debug_AllObjFormKeys` | `string[] function debug_AllObjFormKeys(Form ObjKey) global native` | 515 |
| function | `debug_AllObjIntListKeys` | `string[] function debug_AllObjIntListKeys(Form ObjKey) global native` | 516 |
| function | `debug_AllObjFloatListKeys` | `string[] function debug_AllObjFloatListKeys(Form ObjKey) global native` | 517 |
| function | `debug_AllObjStringListKeys` | `string[] function debug_AllObjStringListKeys(Form ObjKey) global native` | 518 |
| function | `debug_AllObjFormListKeys` | `string[] function debug_AllObjFormListKeys(Form ObjKey) global native` | 519 |
| function | `debug_GetIntObjectCount` | `int function debug_GetIntObjectCount() global native` | 521 |
| function | `debug_GetFloatObjectCount` | `int function debug_GetFloatObjectCount() global native` | 522 |
| function | `debug_GetStringObjectCount` | `int function debug_GetStringObjectCount() global native` | 523 |
| function | `debug_GetFormObjectCount` | `int function debug_GetFormObjectCount() global native` | 524 |
| function | `debug_GetIntListObjectCount` | `int function debug_GetIntListObjectCount() global native` | 525 |
| function | `debug_GetFloatListObjectCount` | `int function debug_GetFloatListObjectCount() global native` | 526 |
| function | `debug_GetStringListObjectCount` | `int function debug_GetStringListObjectCount() global native` | 527 |
| function | `debug_GetFormListObjectCount` | `int function debug_GetFormListObjectCount() global native` | 528 |
| function | `debug_GetIntObject` | `Form function debug_GetIntObject(int index) global native` | 530 |
| function | `debug_GetFloatObject` | `Form function debug_GetFloatObject(int index) global native` | 531 |
| function | `debug_GetStringObject` | `Form function debug_GetStringObject(int index) global native` | 532 |
| function | `debug_GetFormObject` | `Form function debug_GetFormObject(int index) global native` | 533 |
| function | `debug_GetIntListObject` | `Form function debug_GetIntListObject(int index) global native` | 534 |
| function | `debug_GetFloatListObject` | `Form function debug_GetFloatListObject(int index) global native` | 535 |
| function | `debug_GetStringListObject` | `Form function debug_GetStringListObject(int index) global native` | 536 |
| function | `debug_GetFormListObject` | `Form function debug_GetFormListObject(int index) global native` | 537 |
| function | `debug_GetIntKeysCount` | `int function debug_GetIntKeysCount(Form ObjKey) global native` | 539 |
| function | `debug_GetFloatKeysCount` | `int function debug_GetFloatKeysCount(Form ObjKey) global native` | 540 |
| function | `debug_GetStringKeysCount` | `int function debug_GetStringKeysCount(Form ObjKey) global native` | 541 |
| function | `debug_GetFormKeysCount` | `int function debug_GetFormKeysCount(Form ObjKey) global native` | 542 |
| function | `debug_GetIntListKeysCount` | `int function debug_GetIntListKeysCount(Form ObjKey) global native` | 543 |
| function | `debug_GetFloatListKeysCount` | `int function debug_GetFloatListKeysCount(Form ObjKey) global native` | 544 |
| function | `debug_GetStringListKeysCount` | `int function debug_GetStringListKeysCount(Form ObjKey) global native` | 545 |
| function | `debug_GetFormListKeysCount` | `int function debug_GetFormListKeysCount(Form ObjKey) global native` | 546 |
| function | `debug_GetIntKey` | `string function debug_GetIntKey(Form ObjKey, int index) global native` | 548 |
| function | `debug_GetFloatKey` | `string function debug_GetFloatKey(Form ObjKey, int index) global native` | 549 |
| function | `debug_GetStringKey` | `string function debug_GetStringKey(Form ObjKey, int index) global native` | 550 |
| function | `debug_GetFormKey` | `string function debug_GetFormKey(Form ObjKey, int index) global native` | 551 |
| function | `debug_GetIntListKey` | `string function debug_GetIntListKey(Form ObjKey, int index) global native` | 552 |
| function | `debug_GetFloatListKey` | `string function debug_GetFloatListKey(Form ObjKey, int index) global native` | 553 |
| function | `debug_GetStringListKey` | `string function debug_GetStringListKey(Form ObjKey, int index) global native` | 554 |
| function | `debug_GetFormListKey` | `string function debug_GetFormListKey(Form ObjKey, int index) global native` | 555 |
| function | `FileSetIntValue` | `int function FileSetIntValue(string KeyName, int value) global` | 568 |
| function | `FileSetFloatValue` | `float function FileSetFloatValue(string KeyName, float value) global` | 571 |
| function | `FileSetStringValue` | `string function FileSetStringValue(string KeyName, string value) global` | 574 |
| function | `FileSetFormValue` | `form function FileSetFormValue(string KeyName, Form value) global` | 577 |
| function | `FileAdjustIntValue` | `int function FileAdjustIntValue(string KeyName, int amount) global` | 581 |
| function | `FileAdjustFloatValue` | `float function FileAdjustFloatValue(string KeyName, float amount) global` | 584 |
| function | `FileUnsetIntValue` | `bool function FileUnsetIntValue(string KeyName) global` | 588 |
| function | `FileUnsetFloatValue` | `bool function FileUnsetFloatValue(string KeyName) global` | 591 |
| function | `FileUnsetStringValue` | `bool function FileUnsetStringValue(string KeyName) global` | 594 |
| function | `FileUnsetFormValue` | `bool function FileUnsetFormValue(string KeyName) global` | 597 |
| function | `FileHasIntValue` | `bool function FileHasIntValue(string KeyName) global` | 601 |
| function | `FileHasFloatValue` | `bool function FileHasFloatValue(string KeyName) global` | 604 |
| function | `FileHasStringValue` | `bool function FileHasStringValue(string KeyName) global` | 607 |
| function | `FileHasFormValue` | `bool function FileHasFormValue(string KeyName) global` | 610 |
| function | `FileGetIntValue` | `int function FileGetIntValue(string KeyName, int missing = 0) global` | 614 |
| function | `FileGetFloatValue` | `float function FileGetFloatValue(string KeyName, float missing = 0.0) global` | 617 |
| function | `FileGetStringValue` | `string function FileGetStringValue(string KeyName, string missing = "") global` | 620 |
| function | `FileGetFormValue` | `Form function FileGetFormValue(string KeyName, Form missing = none) global` | 623 |
| function | `FileIntListAdd` | `int function FileIntListAdd(string KeyName, int value, bool allowDuplicate = true) global` | 627 |
| function | `FileFloatListAdd` | `int function FileFloatListAdd(string KeyName, float value, bool allowDuplicate = true) global` | 630 |
| function | `FileStringListAdd` | `int function FileStringListAdd(string KeyName, string value, bool allowDuplicate = true) global` | 633 |
| function | `FileFormListAdd` | `int function FileFormListAdd(string KeyName, Form value, bool allowDuplicate = true) global` | 636 |
| function | `FileIntListAdjust` | `int function FileIntListAdjust(string KeyName, int index, int amount) global` | 640 |
| function | `FileFloatListAdjust` | `float function FileFloatListAdjust(string KeyName, int index, float amount) global` | 643 |
| function | `FileIntListRemove` | `int function FileIntListRemove(string KeyName, int value, bool allInstances = false) global` | 647 |
| function | `FileFloatListRemove` | `int function FileFloatListRemove(string KeyName, float value, bool allInstances = false) global` | 650 |
| function | `FileStringListRemove` | `int function FileStringListRemove(string KeyName, string value, bool allInstances = false) global` | 653 |
| function | `FileFormListRemove` | `int function FileFormListRemove(string KeyName, Form value, bool allInstances = false) global` | 656 |
| function | `FileIntListGet` | `int function FileIntListGet(string KeyName, int index) global` | 660 |
| function | `FileFloatListGet` | `float function FileFloatListGet(string KeyName, int index) global` | 663 |
| function | `FileStringListGet` | `string function FileStringListGet(string KeyName, int index) global` | 666 |
| function | `FileFormListGet` | `Form function FileFormListGet(string KeyName, int index) global` | 669 |
| function | `FileIntListSet` | `int function FileIntListSet(string KeyName, int index, int value) global` | 673 |
| function | `FileFloatListSet` | `float function FileFloatListSet(string KeyName, int index, float value) global` | 676 |
| function | `FileStringListSet` | `string function FileStringListSet(string KeyName, int index, string value) global` | 679 |
| function | `FileFormListSet` | `Form function FileFormListSet(string KeyName, int index, Form value) global` | 682 |
| function | `FileIntListClear` | `int function FileIntListClear(string KeyName) global` | 686 |
| function | `FileFloatListClear` | `int function FileFloatListClear(string KeyName) global` | 689 |
| function | `FileStringListClear` | `int function FileStringListClear(string KeyName) global` | 692 |
| function | `FileFormListClear` | `int function FileFormListClear(string KeyName) global` | 695 |
| function | `FileIntListRemoveAt` | `bool function FileIntListRemoveAt(string KeyName, int index) global` | 699 |
| function | `FileFloatListRemoveAt` | `bool function FileFloatListRemoveAt(string KeyName, int index) global` | 702 |
| function | `FileStringListRemoveAt` | `bool function FileStringListRemoveAt(string KeyName, int index) global` | 705 |
| function | `FileFormListRemoveAt` | `bool function FileFormListRemoveAt(string KeyName, int index) global` | 708 |
| function | `FileIntListInsert` | `bool function FileIntListInsert(string KeyName, int index, int value) global` | 712 |
| function | `FileFloatListInsert` | `bool function FileFloatListInsert(string KeyName, int index, float value) global` | 715 |
| function | `FileStringListInsert` | `bool function FileStringListInsert(string KeyName, int index, string value) global` | 718 |
| function | `FileFormListInsert` | `bool function FileFormListInsert(string KeyName, int index, Form value) global` | 721 |
| function | `FileIntListCount` | `int function FileIntListCount(string KeyName) global` | 725 |
| function | `FileFloatListCount` | `int function FileFloatListCount(string KeyName) global` | 728 |
| function | `FileStringListCount` | `int function FileStringListCount(string KeyName) global` | 731 |
| function | `FileFormListCount` | `int function FileFormListCount(string KeyName) global` | 734 |
| function | `FileIntListFind` | `int function FileIntListFind(string KeyName, int value) global` | 738 |
| function | `FileFloatListFind` | `int function FileFloatListFind(string KeyName, float value) global` | 741 |
| function | `FileStringListFind` | `int function FileStringListFind(string KeyName, string value) global` | 744 |
| function | `FileFormListFind` | `int function FileFormListFind(string KeyName, Form value) global` | 747 |
| function | `FileIntListHas` | `bool function FileIntListHas(string KeyName, int value) global` | 751 |
| function | `FileFloatListHas` | `bool function FileFloatListHas(string KeyName, float value) global` | 754 |
| function | `FileStringListHas` | `bool function FileStringListHas(string KeyName, string value) global` | 757 |
| function | `FileFormListHas` | `bool function FileFormListHas(string KeyName, Form value) global` | 760 |
| function | `FileIntListSlice` | `function FileIntListSlice(string KeyName, int[] slice, int startIndex = 0) global` | 764 |
| function | `FileFloatListSlice` | `function FileFloatListSlice(string KeyName, float[] slice, int startIndex = 0) global` | 767 |
| function | `FileStringListSlice` | `function FileStringListSlice(string KeyName, string[] slice, int startIndex = 0) global` | 770 |
| function | `FileFormListSlice` | `function FileFormListSlice(string KeyName, Form[] slice, int startIndex = 0) global` | 773 |
| function | `FileIntListResize` | `int function FileIntListResize(string KeyName, int toLength, int filler = 0) global` | 777 |
| function | `FileFloatListResize` | `int function FileFloatListResize(string KeyName, int toLength, float filler = 0.0) global` | 780 |
| function | `FileStringListResize` | `int function FileStringListResize(string KeyName, int toLength, string filler = "") global` | 783 |
| function | `FileFormListResize` | `int function FileFormListResize(string KeyName, int toLength, Form filler = none) global` | 786 |
| function | `FileIntListCopy` | `bool function FileIntListCopy(string KeyName, int[] copy) global` | 791 |
| function | `FileFloatListCopy` | `bool function FileFloatListCopy(string KeyName, float[] copy) global` | 794 |
| function | `FileStringListCopy` | `bool function FileStringListCopy(string KeyName, string[] copy) global` | 797 |
| function | `FileFormListCopy` | `bool function FileFormListCopy(string KeyName, Form[] copy) global` | 800 |
| function | `debug_SaveFile` | `function debug_SaveFile() global` | 804 |
| function | `debug_FileGetIntKeysCount` | `int function debug_FileGetIntKeysCount() global` | 812 |
| function | `debug_FileGetFloatKeysCount` | `int function debug_FileGetFloatKeysCount() global` | 816 |
| function | `debug_FileGetStringKeysCount` | `int function debug_FileGetStringKeysCount() global` | 820 |
| function | `debug_FileGetIntListKeysCount` | `int function debug_FileGetIntListKeysCount() global` | 824 |
| function | `debug_FileGetFloatListKeysCount` | `int function debug_FileGetFloatListKeysCount() global` | 828 |
| function | `debug_FileGetStringListKeysCount` | `int function debug_FileGetStringListKeysCount() global` | 832 |
| function | `debug_FileGetIntKey` | `string function debug_FileGetIntKey(int index) global` | 836 |
| function | `debug_FileGetFloatKey` | `string function debug_FileGetFloatKey(int index) global` | 840 |
| function | `debug_FileGetStringKey` | `string function debug_FileGetStringKey(int index) global` | 844 |
| function | `debug_FileGetIntListKey` | `string function debug_FileGetIntListKey(int index) global` | 848 |
| function | `debug_FileGetFloatListKey` | `string function debug_FileGetFloatListKey(int index) global` | 852 |
| function | `debug_FileGetStringListKey` | `string function debug_FileGetStringListKey(int index) global` | 856 |
| function | `debug_FileDeleteAllValues` | `function debug_FileDeleteAllValues() global` | 860 |
| function | `debug_SetDebugMode` | `function debug_SetDebugMode(bool enabled) global` | 863 |
| function | `ImportFile` | `bool function ImportFile(string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false) global` | 866 |
| function | `ExportFile` | `bool function ExportFile(string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false, bool append = true) global` | 869 |

## Architectural map

- `StorageUtil` — save-associated/global/Form-keyed typed key-value and dynamic-list storage.
- `JsonUtil` — external JSON-backed persistent data.
- `ActorUtil` — actor/package and actor utility operations.
- `ObjectUtil` — object/form utility operations.
- `MiscUtil` — miscellaneous/string/world/filesystem-style utilities.
- `PapyrusUtil` — core/version/array and framework helpers.

## Persistence warning

Signatures alone do not determine persistence scope. StorageUtil, JsonUtil, ordinary Papyrus properties, JContainers and SKSE co-save state have different lifetime/profile/save semantics; consult `papyrusutil-jcontainers-persistent-data.md`.

## Evidence rules

Every declaration is tied to the source PSC blob SHA above. Future framework updates should diff function/event names and complete signatures, not only version numbers.
