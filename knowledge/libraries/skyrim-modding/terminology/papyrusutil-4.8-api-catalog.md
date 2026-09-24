# PapyrusUtil 4.8 — Papyrus API Declaration Catalog

Imported: 2026-09-24
Pinned source commit: `ff854180db67d330da34371781bcf9e6443b53c3`
Status: source-derived declaration catalog

## Counts

| Script | Declarations |
|---|---:|
| PapyrusUtil | 97 |
| StorageUtil | 282 |
| JsonUtil | 135 |
| ActorUtil | 5 |
| ObjectUtil | 0 |
| MiscUtil | 18 |

Total declaration rows indexed: **537**

## Complete declaration index

## PapyrusUtil

Source: `Scripts/Source/PapyrusUtil.psc` — blob `9f8c370b3f2a170d9ddd9d627f47df9850bf1f50`

| Line | Function | Declaration |
|---:|---|---|
| 4 | `GetVersion` | `int function GetVersion() global native` |
| 7 | `GetScriptVersion` | `int function GetScriptVersion() global` |
| 16 | `ActorArray` | `Actor[] function ActorArray(int size, Actor filler = none) global native` |
| 17 | `ResizeActorArray` | `Actor[] function ResizeActorArray(Actor[] ArrayValues, int toSize, Actor filler = none) global native` |
| 18 | `ObjRefArray` | `ObjectReference[] function ObjRefArray(int size, ObjectReference filler = none) global native` |
| 19 | `ResizeObjRefArray` | `ObjectReference[] function ResizeObjRefArray(ObjectReference[] ArrayValues, int toSize, ObjectReference filler = none) global native` |
| 24 | `PushFloat` | `float[] function PushFloat(float[] ArrayValues, float push) global native` |
| 25 | `PushInt` | `int[] function PushInt(int[] ArrayValues, int push) global native` |
| 27 | `PushString` | `string[] function PushString(string[] ArrayValues, string push) global native` |
| 28 | `PushForm` | `Form[] function PushForm(Form[] ArrayValues, Form push) global native` |
| 29 | `PushAlias` | `Alias[] function PushAlias(Alias[] ArrayValues, Alias push) global native` |
| 30 | `PushActor` | `Actor[] function PushActor(Actor[] ArrayValues, Actor push) global native` |
| 31 | `PushObjRef` | `ObjectReference[] function PushObjRef(ObjectReference[] ArrayValues, ObjectReference push) global native` |
| 34 | `RemoveFloat` | `float[] function RemoveFloat(float[] ArrayValues, float ToRemove) global native` |
| 35 | `RemoveInt` | `int[] function RemoveInt(int[] ArrayValues, int ToRemove) global native` |
| 37 | `RemoveString` | `string[] function RemoveString(string[] ArrayValues, string ToRemove) global native` |
| 38 | `RemoveForm` | `Form[] function RemoveForm(Form[] ArrayValues, Form ToRemove) global native` |
| 39 | `RemoveAlias` | `Alias[] function RemoveAlias(Alias[] ArrayValues, Alias ToRemove) global native` |
| 40 | `RemoveActor` | `Actor[] function RemoveActor(Actor[] ArrayValues, Actor ToRemove) global native` |
| 41 | `RemoveObjRef` | `ObjectReference[] function RemoveObjRef(ObjectReference[] ArrayValues, ObjectReference ToRemove) global native` |
| 44 | `RemoveDupeFloat` | `float[] function RemoveDupeFloat(float[] ArrayValues) global native` |
| 45 | `RemoveDupeInt` | `int[] function RemoveDupeInt(int[] ArrayValues) global native` |
| 46 | `RemoveDupeString` | `string[] function RemoveDupeString(string[] ArrayValues) global native` |
| 47 | `RemoveDupeForm` | `Form[] function RemoveDupeForm(Form[] ArrayValues) global native` |
| 48 | `RemoveDupeAlias` | `Alias[] function RemoveDupeAlias(Alias[] ArrayValues) global native` |
| 49 | `RemoveDupeActor` | `Actor[] function RemoveDupeActor(Actor[] ArrayValues) global native` |
| 50 | `RemoveDupeObjRef` | `ObjectReference[] function RemoveDupeObjRef(ObjectReference[] ArrayValues) global native` |
| 55 | `GetDiffFloat` | `float[] function GetDiffFloat(float[] ArrayValues1, float[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 56 | `GetDiffInt` | `int[] function GetDiffInt(int[] ArrayValues1, int[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 57 | `GetDiffString` | `string[] function GetDiffString(string[] ArrayValues1, string[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 58 | `GetDiffForm` | `Form[] function GetDiffForm(Form[] ArrayValues1, Form[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 59 | `GetDiffAlias` | `Alias[] function GetDiffAlias(Alias[] ArrayValues1, Alias[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 60 | `GetDiffActor` | `Actor[] function GetDiffActor(Actor[] ArrayValues1, Actor[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 61 | `GetDiffObjRef` | `ObjectReference[] function GetDiffObjRef(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool CompareBoth = false, bool IncludeDupes = false) global native` |
| 64 | `GetMatchingFloat` | `float[] function GetMatchingFloat(float[] ArrayValues1, float[] ArrayValues2) global native` |
| 65 | `GetMatchingInt` | `int[] function GetMatchingInt(int[] ArrayValues1, int[] ArrayValues2) global native` |
| 66 | `GetMatchingString` | `string[] function GetMatchingString(string[] ArrayValues1, string[] ArrayValues2) global native` |
| 67 | `GetMatchingForm` | `Form[] function GetMatchingForm(Form[] ArrayValues1, Form[] ArrayValues2) global native` |
| 68 | `GetMatchingAlias` | `Alias[] function GetMatchingAlias(Alias[] ArrayValues1, Alias[] ArrayValues2) global native` |
| 69 | `GetMatchingActor` | `Actor[] function GetMatchingActor(Actor[] ArrayValues1, Actor[] ArrayValues2) global native` |
| 70 | `GetMatchingObjRef` | `ObjectReference[] function GetMatchingObjRef(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2) global native` |
| 73 | `CountFloat` | `int function CountFloat(float[] ArrayValues, float EqualTo) global native` |
| 74 | `CountInt` | `int function CountInt(int[] ArrayValues, int EqualTo) global native` |
| 75 | `CountBool` | `int function CountBool(bool[] ArrayValues, bool EqualTo) global native` |
| 76 | `CountString` | `int function CountString(string[] ArrayValues, string EqualTo) global native` |
| 77 | `CountForm` | `int function CountForm(Form[] ArrayValues, Form EqualTo) global native` |
| 78 | `CountAlias` | `int function CountAlias(Alias[] ArrayValues, Alias EqualTo) global native` |
| 79 | `CountActor` | `int function CountActor(Actor[] ArrayValues, Actor EqualTo) global native` |
| 80 | `CountObjRef` | `int function CountObjRef(ObjectReference[] ArrayValues, ObjectReference EqualTo) global native` |
| 83 | `MergeFloatArray` | `float[] function MergeFloatArray(float[] ArrayValues1, float[] ArrayValues2, bool RemoveDupes = false) global native` |
| 84 | `MergeIntArray` | `int[] function MergeIntArray(int[] ArrayValues1, int[] ArrayValues2, bool RemoveDupes = false) global native` |
| 86 | `MergeStringArray` | `string[] function MergeStringArray(string[] ArrayValues1, string[] ArrayValues2, bool RemoveDupes = false) global native` |
| 87 | `MergeFormArray` | `Form[] function MergeFormArray(Form[] ArrayValues1, Form[] ArrayValues2, bool RemoveDupes = false) global native` |
| 88 | `MergeAliasArray` | `Alias[] function MergeAliasArray(Alias[] ArrayValues1, Alias[] ArrayValues2, bool RemoveDupes = false) global native` |
| 89 | `MergeActorArray` | `Actor[] function MergeActorArray(Actor[] ArrayValues1, Actor[] ArrayValues2, bool RemoveDupes = false) global native` |
| 90 | `MergeObjRefArray` | `ObjectReference[] function MergeObjRefArray(ObjectReference[] ArrayValues1, ObjectReference[] ArrayValues2, bool RemoveDupes = false) global native` |
| 94 | `SliceFloatArray` | `float[] function SliceFloatArray(float[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 95 | `SliceIntArray` | `int[] function SliceIntArray(int[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 97 | `SliceStringArray` | `string[] function SliceStringArray(string[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 98 | `SliceFormArray` | `Form[] function SliceFormArray(Form[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 99 | `SliceAliasArray` | `Alias[] function SliceAliasArray(Alias[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 100 | `SliceActorArray` | `Actor[] function SliceActorArray(Actor[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 101 | `SliceObjRefArray` | `ObjectReference[] function SliceObjRefArray(ObjectReference[] ArrayValues, int StartIndex, int EndIndex = -1) global native` |
| 105 | `SortIntArray` | `function SortIntArray(int[] ArrayValues, bool descending = false) global native` |
| 106 | `SortFloatArray` | `function SortFloatArray(float[] ArrayValues, bool descending = false) global native` |
| 107 | `SortStringArray` | `function SortStringArray(string[] ArrayValues, bool descending = false) global native` |
| 113 | `ClearEmpty` | `string[] function ClearEmpty(string[] ArrayValues) global` |
| 116 | `ClearNone` | `Form[] function ClearNone(Form[] ArrayValues) global` |
| 120 | `CountFalse` | `int function CountFalse(bool[] ArrayValues) global` |
| 123 | `CountTrue` | `int function CountTrue(bool[] ArrayValues) global` |
| 126 | `CountNone` | `int function CountNone(Form[] ArrayValues) global` |
| 135 | `StringSplit` | `string[] function StringSplit(string ArgString, string Delimiter = ",") global native` |
| 138 | `StringJoin` | `string function StringJoin(string[] Values, string Delimiter = ",") global native` |
| 147 | `AddIntValues` | `int function AddIntValues(int[] Values) global native` |
| 148 | `AddFloatValues` | `float function AddFloatValues(float[] Values) global native` |
| 151 | `ClampInt` | `int function ClampInt(int value, int min, int max) global native` |
| 152 | `ClampFloat` | `float function ClampFloat(float value, float min, float max) global native` |
| 157 | `WrapInt` | `int function WrapInt(int value, int end, int start = 0) global native` |
| 158 | `WrapFloat` | `float function WrapFloat(float value, float end, float start = 0.0) global native` |
| 161 | `SignInt` | `int function SignInt(bool doSign, int value) global native` |
| 162 | `SignFloat` | `float function SignFloat(bool doSign, float value) global native` |
| 169 | `ResizeBoolArray` | `bool[] function ResizeBoolArray(bool[] ArrayValues, int toSize, bool filler = false) global` |
| 182 | `PushBool` | `bool[] function PushBool(bool[] ArrayValues, bool push) global` |
| 186 | `RemoveBool` | `bool[] function RemoveBool(bool[] ArrayValues, bool ToRemove) global` |
| 191 | `MergeBoolArray` | `bool[] function MergeBoolArray(bool[] ArrayValues1, bool[] ArrayValues2, bool RemoveDupes = false) global` |
| 223 | `SliceBoolArray` | `bool[] function SliceBoolArray(bool[] ArrayValues, int StartIndex, int EndIndex = -1) global` |
| 254 | `FloatArray` | `float[] function FloatArray(int size, float filler = 0.0) global` |
| 257 | `IntArray` | `int[] function IntArray(int size, int filler = 0) global` |
| 260 | `BoolArray` | `bool[] function BoolArray(int size, bool filler = false) global` |
| 263 | `StringArray` | `string[] function StringArray(int size, string filler = "") global` |
| 266 | `FormArray` | `Form[] function FormArray(int size, Form filler = none) global` |
| 269 | `AliasArray` | `Alias[] function AliasArray(int size, Alias filler = none) global` |
| 273 | `ResizeFloatArray` | `float[] function ResizeFloatArray(float[] ArrayValues, int toSize, float filler = 0.0) global` |
| 276 | `ResizeIntArray` | `int[] function ResizeIntArray(int[] ArrayValues, int toSize, int filler = 0) global` |
| 279 | `ResizeStringArray` | `string[] function ResizeStringArray(string[] ArrayValues, int toSize, string filler = "") global` |
| 282 | `ResizeFormArray` | `Form[] function ResizeFormArray(Form[] ArrayValues, int toSize, Form filler = none) global` |
| 285 | `ResizeAliasArray` | `Alias[] function ResizeAliasArray(Alias[] ArrayValues, int toSize, Alias filler = none) global` |

## StorageUtil

Source: `Scripts/Source/StorageUtil.psc` — blob `c309fef20cf56342c5ee0ed53f5d146af51bc940`

| Line | Function | Declaration |
|---:|---|---|
| 77 | `SetIntValue` | `int function SetIntValue(Form ObjKey, string KeyName, int value) global native` |
| 78 | `SetFloatValue` | `float function SetFloatValue(Form ObjKey, string KeyName, float value) global native` |
| 79 | `SetStringValue` | `string function SetStringValue(Form ObjKey, string KeyName, string value) global native` |
| 80 | `SetFormValue` | `Form function SetFormValue(Form ObjKey, string KeyName, Form value) global native` |
| 89 | `UnsetIntValue` | `bool function UnsetIntValue(Form ObjKey, string KeyName) global native` |
| 90 | `UnsetFloatValue` | `bool function UnsetFloatValue(Form ObjKey, string KeyName) global native` |
| 91 | `UnsetStringValue` | `bool function UnsetStringValue(Form ObjKey, string KeyName) global native` |
| 92 | `UnsetFormValue` | `bool function UnsetFormValue(Form ObjKey, string KeyName) global native` |
| 100 | `HasIntValue` | `bool function HasIntValue(Form ObjKey, string KeyName) global native` |
| 101 | `HasFloatValue` | `bool function HasFloatValue(Form ObjKey, string KeyName) global native` |
| 102 | `HasStringValue` | `bool function HasStringValue(Form ObjKey, string KeyName) global native` |
| 103 | `HasFormValue` | `bool function HasFormValue(Form ObjKey, string KeyName) global native` |
| 112 | `GetIntValue` | `int function GetIntValue(Form ObjKey, string KeyName, int missing = 0) global native` |
| 113 | `GetFloatValue` | `float function GetFloatValue(Form ObjKey, string KeyName, float missing = 0.0) global native` |
| 114 | `GetStringValue` | `string function GetStringValue(Form ObjKey, string KeyName, string missing = "") global native` |
| 115 | `GetFormValue` | `Form function GetFormValue(Form ObjKey, string KeyName, Form missing = none) global native` |
| 124 | `PluckIntValue` | `int function PluckIntValue(Form ObjKey, string KeyName, int missing = 0) global native` |
| 125 | `PluckFloatValue` | `float function PluckFloatValue(Form ObjKey, string KeyName, float missing = 0.0) global native` |
| 126 | `PluckStringValue` | `string function PluckStringValue(Form ObjKey, string KeyName, string missing = "") global native` |
| 127 | `PluckFormValue` | `Form function PluckFormValue(Form ObjKey, string KeyName, Form missing = none) global native` |
| 137 | `AdjustIntValue` | `int function AdjustIntValue(Form ObjKey, string KeyName, int amount) global native` |
| 138 | `AdjustFloatValue` | `float function AdjustFloatValue(Form ObjKey, string KeyName, float amount) global native` |
| 150 | `IntListAdd` | `int function IntListAdd(Form ObjKey, string KeyName, int value, bool allowDuplicate = true) global native` |
| 151 | `FloatListAdd` | `int function FloatListAdd(Form ObjKey, string KeyName, float value, bool allowDuplicate = true) global native` |
| 152 | `StringListAdd` | `int function StringListAdd(Form ObjKey, string KeyName, string value, bool allowDuplicate = true) global native` |
| 153 | `FormListAdd` | `int function FormListAdd(Form ObjKey, string KeyName, Form value, bool allowDuplicate = true) global native` |
| 162 | `IntListGet` | `int function IntListGet(Form ObjKey, string KeyName, int index) global native` |
| 163 | `FloatListGet` | `float function FloatListGet(Form ObjKey, string KeyName, int index) global native` |
| 164 | `StringListGet` | `string function StringListGet(Form ObjKey, string KeyName, int index) global native` |
| 165 | `FormListGet` | `Form function FormListGet(Form ObjKey, string KeyName, int index) global native` |
| 175 | `IntListSet` | `int function IntListSet(Form ObjKey, string KeyName, int index, int value) global native` |
| 176 | `FloatListSet` | `float function FloatListSet(Form ObjKey, string KeyName, int index, float value) global native` |
| 177 | `StringListSet` | `string function StringListSet(Form ObjKey, string KeyName, int index, string value) global native` |
| 178 | `FormListSet` | `Form function FormListSet(Form ObjKey, string KeyName, int index, Form value) global native` |
| 188 | `IntListPluck` | `int function IntListPluck(Form ObjKey, string KeyName, int index, int missing) global native` |
| 189 | `FloatListPluck` | `float function FloatListPluck(Form ObjKey, string KeyName, int index, float missing) global native` |
| 190 | `StringListPluck` | `string function StringListPluck(Form ObjKey, string KeyName, int index, string missing) global native` |
| 191 | `FormListPluck` | `Form function FormListPluck(Form ObjKey, string KeyName, int index, Form missing) global native` |
| 198 | `IntListShift` | `int function IntListShift(Form ObjKey, string KeyName) global native` |
| 199 | `FloatListShift` | `float function FloatListShift(Form ObjKey, string KeyName) global native` |
| 200 | `StringListShift` | `string function StringListShift(Form ObjKey, string KeyName) global native` |
| 201 | `FormListShift` | `Form function FormListShift(Form ObjKey, string KeyName) global native` |
| 208 | `IntListPop` | `int function IntListPop(Form ObjKey, string KeyName) global native` |
| 209 | `FloatListPop` | `float function FloatListPop(Form ObjKey, string KeyName) global native` |
| 210 | `StringListPop` | `string function StringListPop(Form ObjKey, string KeyName) global native` |
| 211 | `FormListPop` | `Form function FormListPop(Form ObjKey, string KeyName) global native` |
| 222 | `IntListAdjust` | `int function IntListAdjust(Form ObjKey, string KeyName, int index, int amount) global native` |
| 223 | `FloatListAdjust` | `float function FloatListAdjust(Form ObjKey, string KeyName, int index, float amount) global native` |
| 233 | `IntListInsert` | `bool function IntListInsert(Form ObjKey, string KeyName, int index, int value) global native` |
| 234 | `FloatListInsert` | `bool function FloatListInsert(Form ObjKey, string KeyName, int index, float value) global native` |
| 235 | `StringListInsert` | `bool function StringListInsert(Form ObjKey, string KeyName, int index, string value) global native` |
| 236 | `FormListInsert` | `bool function FormListInsert(Form ObjKey, string KeyName, int index, Form value) global native` |
| 247 | `IntListRemove` | `int function IntListRemove(Form ObjKey, string KeyName, int value, bool allInstances = false) global native` |
| 248 | `FloatListRemove` | `int function FloatListRemove(Form ObjKey, string KeyName, float value, bool allInstances = false) global native` |
| 249 | `StringListRemove` | `int function StringListRemove(Form ObjKey, string KeyName, string value, bool allInstances = false) global native` |
| 250 | `FormListRemove` | `int function FormListRemove(Form ObjKey, string KeyName, Form value, bool allInstances = false) global native` |
| 259 | `IntListClear` | `int function IntListClear(Form ObjKey, string KeyName) global native` |
| 260 | `FloatListClear` | `int function FloatListClear(Form ObjKey, string KeyName) global native` |
| 261 | `StringListClear` | `int function StringListClear(Form ObjKey, string KeyName) global native` |
| 262 | `FormListClear` | `int function FormListClear(Form ObjKey, string KeyName) global native` |
| 271 | `IntListRemoveAt` | `bool function IntListRemoveAt(Form ObjKey, string KeyName, int index) global native` |
| 272 | `FloatListRemoveAt` | `bool function FloatListRemoveAt(Form ObjKey, string KeyName, int index) global native` |
| 273 | `StringListRemoveAt` | `bool function StringListRemoveAt(Form ObjKey, string KeyName, int index) global native` |
| 274 | `FormListRemoveAt` | `bool function FormListRemoveAt(Form ObjKey, string KeyName, int index) global native` |
| 281 | `IntListCount` | `int function IntListCount(Form ObjKey, string KeyName) global native` |
| 282 | `FloatListCount` | `int function FloatListCount(Form ObjKey, string KeyName) global native` |
| 283 | `StringListCount` | `int function StringListCount(Form ObjKey, string KeyName) global native` |
| 284 | `FormListCount` | `int function FormListCount(Form ObjKey, string KeyName) global native` |
| 293 | `IntListCountValue` | `int function IntListCountValue(Form ObjKey, string KeyName, int value, bool exclude = false) global native` |
| 294 | `FloatListCountValue` | `int function FloatListCountValue(Form ObjKey, string KeyName, float value, bool exclude = false) global native` |
| 295 | `StringListCountValue` | `int function StringListCountValue(Form ObjKey, string KeyName, string value, bool exclude = false) global native` |
| 296 | `FormListCountValue` | `int function FormListCountValue(Form ObjKey, string KeyName, Form value, bool exclude = false) global native` |
| 305 | `IntListFind` | `int function IntListFind(Form ObjKey, string KeyName, int value) global native` |
| 306 | `FloatListFind` | `int function FloatListFind(Form ObjKey, string KeyName, float value) global native` |
| 307 | `StringListFind` | `int function StringListFind(Form ObjKey, string KeyName, string value) global native` |
| 308 | `FormListFind` | `int function FormListFind(Form ObjKey, string KeyName, Form value) global native` |
| 317 | `IntListHas` | `bool function IntListHas(Form ObjKey, string KeyName, int value) global native` |
| 318 | `FloatListHas` | `bool function FloatListHas(Form ObjKey, string KeyName, float value) global native` |
| 319 | `StringListHas` | `bool function StringListHas(Form ObjKey, string KeyName, string value) global native` |
| 320 | `FormListHas` | `bool function FormListHas(Form ObjKey, string KeyName, Form value) global native` |
| 327 | `IntListSort` | `function IntListSort(Form ObjKey, string KeyName) global native` |
| 328 | `FloatListSort` | `function FloatListSort(Form ObjKey, string KeyName) global native` |
| 329 | `StringListSort` | `function StringListSort(Form ObjKey, string KeyName) global native` |
| 330 | `FormListSort` | `function FormListSort(Form ObjKey, string KeyName) global native` |
| 341 | `IntListSlice` | `function IntListSlice(Form ObjKey, string KeyName, int[] slice, int startIndex = 0) global native` |
| 342 | `FloatListSlice` | `function FloatListSlice(Form ObjKey, string KeyName, float[] slice, int startIndex = 0) global native` |
| 343 | `StringListSlice` | `function StringListSlice(Form ObjKey, string KeyName, string[] slice, int startIndex = 0) global native` |
| 344 | `FormListSlice` | `function FormListSlice(Form ObjKey, string KeyName, Form[] slice, int startIndex = 0) global native` |
| 358 | `IntListResize` | `int function IntListResize(Form ObjKey, string KeyName, int toLength, int filler = 0) global native` |
| 359 | `FloatListResize` | `int function FloatListResize(Form ObjKey, string KeyName, int toLength, float filler = 0.0) global native` |
| 360 | `StringListResize` | `int function StringListResize(Form ObjKey, string KeyName, int toLength, string filler = "") global native` |
| 361 | `FormListResize` | `int function FormListResize(Form ObjKey, string KeyName, int toLength, Form filler = none) global native` |
| 373 | `IntListCopy` | `bool function IntListCopy(Form ObjKey, string KeyName, int[] copy) global native` |
| 374 | `FloatListCopy` | `bool function FloatListCopy(Form ObjKey, string KeyName, float[] copy) global native` |
| 375 | `StringListCopy` | `bool function StringListCopy(Form ObjKey, string KeyName, string[] copy) global native` |
| 376 | `FormListCopy` | `bool function FormListCopy(Form ObjKey, string KeyName, Form[] copy) global native` |
| 385 | `IntListToArray` | `int[] function IntListToArray(Form ObjKey, string KeyName) global native` |
| 386 | `FloatListToArray` | `float[] function FloatListToArray(Form ObjKey, string KeyName) global native` |
| 387 | `StringListToArray` | `string[] function StringListToArray(Form ObjKey, string KeyName) global native` |
| 388 | `FormListToArray` | `Form[] function FormListToArray(Form ObjKey, string KeyName) global native` |
| 398 | `IntListRandom` | `int function IntListRandom(Form ObjKey, string KeyName) global native` |
| 399 | `FloatListRandom` | `float function FloatListRandom(Form ObjKey, string KeyName) global native` |
| 400 | `StringListRandom` | `string function StringListRandom(Form ObjKey, string KeyName) global native` |
| 401 | `FormListRandom` | `Form function FormListRandom(Form ObjKey, string KeyName) global native` |
| 412 | `FormListFilterByTypes` | `Form[] function FormListFilterByTypes(Form ObjKey, string KeyName, int[] FormTypeIDs, bool ReturnMatching = true) global native` |
| 414 | `FormListFilterByType` | `Form[] function FormListFilterByType(Form ObjKey, string KeyName, int FormTypeID, bool ReturnMatching = true) global` |
| 424 | `CountIntValuePrefix` | `int function CountIntValuePrefix(string PrefixKey) global native` |
| 425 | `CountFloatValuePrefix` | `int function CountFloatValuePrefix(string PrefixKey) global native` |
| 426 | `CountStringValuePrefix` | `int function CountStringValuePrefix(string PrefixKey) global native` |
| 427 | `CountFormValuePrefix` | `int function CountFormValuePrefix(string PrefixKey) global native` |
| 429 | `CountIntListPrefix` | `int function CountIntListPrefix(string PrefixKey) global native` |
| 430 | `CountFloatListPrefix` | `int function CountFloatListPrefix(string PrefixKey) global native` |
| 431 | `CountStringListPrefix` | `int function CountStringListPrefix(string PrefixKey) global native` |
| 432 | `CountFormListPrefix` | `int function CountFormListPrefix(string PrefixKey) global native` |
| 435 | `CountAllPrefix` | `int function CountAllPrefix(string PrefixKey) global native` |
| 442 | `CountObjIntValuePrefix` | `int function CountObjIntValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 443 | `CountObjFloatValuePrefix` | `int function CountObjFloatValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 444 | `CountObjStringValuePrefix` | `int function CountObjStringValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 445 | `CountObjFormValuePrefix` | `int function CountObjFormValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 447 | `CountObjIntListPrefix` | `int function CountObjIntListPrefix(Form ObjKey, string PrefixKey) global native` |
| 448 | `CountObjFloatListPrefix` | `int function CountObjFloatListPrefix(Form ObjKey, string PrefixKey) global native` |
| 449 | `CountObjStringListPrefix` | `int function CountObjStringListPrefix(Form ObjKey, string PrefixKey) global native` |
| 450 | `CountObjFormListPrefix` | `int function CountObjFormListPrefix(Form ObjKey, string PrefixKey) global native` |
| 453 | `CountAllObjPrefix` | `int function CountAllObjPrefix(Form ObjKey, string PrefixKey) global native` |
| 461 | `ClearIntValuePrefix` | `int function ClearIntValuePrefix(string PrefixKey) global native` |
| 462 | `ClearFloatValuePrefix` | `int function ClearFloatValuePrefix(string PrefixKey) global native` |
| 463 | `ClearStringValuePrefix` | `int function ClearStringValuePrefix(string PrefixKey) global native` |
| 464 | `ClearFormValuePrefix` | `int function ClearFormValuePrefix(string PrefixKey) global native` |
| 466 | `ClearIntListPrefix` | `int function ClearIntListPrefix(string PrefixKey) global native` |
| 467 | `ClearFloatListPrefix` | `int function ClearFloatListPrefix(string PrefixKey) global native` |
| 468 | `ClearStringListPrefix` | `int function ClearStringListPrefix(string PrefixKey) global native` |
| 469 | `ClearFormListPrefix` | `int function ClearFormListPrefix(string PrefixKey) global native` |
| 472 | `ClearAllPrefix` | `int function ClearAllPrefix(string PrefixKey) global native` |
| 481 | `ClearObjIntValuePrefix` | `int function ClearObjIntValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 482 | `ClearObjFloatValuePrefix` | `int function ClearObjFloatValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 483 | `ClearObjStringValuePrefix` | `int function ClearObjStringValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 484 | `ClearObjFormValuePrefix` | `int function ClearObjFormValuePrefix(Form ObjKey, string PrefixKey) global native` |
| 486 | `ClearObjIntListPrefix` | `int function ClearObjIntListPrefix(Form ObjKey, string PrefixKey) global native` |
| 487 | `ClearObjFloatListPrefix` | `int function ClearObjFloatListPrefix(Form ObjKey, string PrefixKey) global native` |
| 488 | `ClearObjStringListPrefix` | `int function ClearObjStringListPrefix(Form ObjKey, string PrefixKey) global native` |
| 489 | `ClearObjFormListPrefix` | `int function ClearObjFormListPrefix(Form ObjKey, string PrefixKey) global native` |
| 492 | `ClearAllObjPrefix` | `int function ClearAllObjPrefix(Form ObjKey, string PrefixKey) global native` |
| 498 | `debug_DeleteValues` | `function debug_DeleteValues(Form ObjKey) global native` |
| 499 | `debug_DeleteAllValues` | `function debug_DeleteAllValues() global native` |
| 501 | `debug_Cleanup` | `int function debug_Cleanup() global native` |
| 503 | `debug_AllIntObjs` | `Form[] function debug_AllIntObjs() global native` |
| 504 | `debug_AllFloatObjs` | `Form[] function debug_AllFloatObjs() global native` |
| 505 | `debug_AllStringObjs` | `Form[] function debug_AllStringObjs() global native` |
| 506 | `debug_AllFormObjs` | `Form[] function debug_AllFormObjs() global native` |
| 507 | `debug_AllIntListObjs` | `Form[] function debug_AllIntListObjs() global native` |
| 508 | `debug_AllFloatListObjs` | `Form[] function debug_AllFloatListObjs() global native` |
| 509 | `debug_AllStringListObjs` | `Form[] function debug_AllStringListObjs() global native` |
| 510 | `debug_AllFormListObjs` | `Form[] function debug_AllFormListObjs() global native` |
| 512 | `debug_AllObjIntKeys` | `string[] function debug_AllObjIntKeys(Form ObjKey) global native` |
| 513 | `debug_AllObjFloatKeys` | `string[] function debug_AllObjFloatKeys(Form ObjKey) global native` |
| 514 | `debug_AllObjStringKeys` | `string[] function debug_AllObjStringKeys(Form ObjKey) global native` |
| 515 | `debug_AllObjFormKeys` | `string[] function debug_AllObjFormKeys(Form ObjKey) global native` |
| 516 | `debug_AllObjIntListKeys` | `string[] function debug_AllObjIntListKeys(Form ObjKey) global native` |
| 517 | `debug_AllObjFloatListKeys` | `string[] function debug_AllObjFloatListKeys(Form ObjKey) global native` |
| 518 | `debug_AllObjStringListKeys` | `string[] function debug_AllObjStringListKeys(Form ObjKey) global native` |
| 519 | `debug_AllObjFormListKeys` | `string[] function debug_AllObjFormListKeys(Form ObjKey) global native` |
| 521 | `debug_GetIntObjectCount` | `int function debug_GetIntObjectCount() global native` |
| 522 | `debug_GetFloatObjectCount` | `int function debug_GetFloatObjectCount() global native` |
| 523 | `debug_GetStringObjectCount` | `int function debug_GetStringObjectCount() global native` |
| 524 | `debug_GetFormObjectCount` | `int function debug_GetFormObjectCount() global native` |
| 525 | `debug_GetIntListObjectCount` | `int function debug_GetIntListObjectCount() global native` |
| 526 | `debug_GetFloatListObjectCount` | `int function debug_GetFloatListObjectCount() global native` |
| 527 | `debug_GetStringListObjectCount` | `int function debug_GetStringListObjectCount() global native` |
| 528 | `debug_GetFormListObjectCount` | `int function debug_GetFormListObjectCount() global native` |
| 530 | `debug_GetIntObject` | `Form function debug_GetIntObject(int index) global native` |
| 531 | `debug_GetFloatObject` | `Form function debug_GetFloatObject(int index) global native` |
| 532 | `debug_GetStringObject` | `Form function debug_GetStringObject(int index) global native` |
| 533 | `debug_GetFormObject` | `Form function debug_GetFormObject(int index) global native` |
| 534 | `debug_GetIntListObject` | `Form function debug_GetIntListObject(int index) global native` |
| 535 | `debug_GetFloatListObject` | `Form function debug_GetFloatListObject(int index) global native` |
| 536 | `debug_GetStringListObject` | `Form function debug_GetStringListObject(int index) global native` |
| 537 | `debug_GetFormListObject` | `Form function debug_GetFormListObject(int index) global native` |
| 539 | `debug_GetIntKeysCount` | `int function debug_GetIntKeysCount(Form ObjKey) global native` |
| 540 | `debug_GetFloatKeysCount` | `int function debug_GetFloatKeysCount(Form ObjKey) global native` |
| 541 | `debug_GetStringKeysCount` | `int function debug_GetStringKeysCount(Form ObjKey) global native` |
| 542 | `debug_GetFormKeysCount` | `int function debug_GetFormKeysCount(Form ObjKey) global native` |
| 543 | `debug_GetIntListKeysCount` | `int function debug_GetIntListKeysCount(Form ObjKey) global native` |
| 544 | `debug_GetFloatListKeysCount` | `int function debug_GetFloatListKeysCount(Form ObjKey) global native` |
| 545 | `debug_GetStringListKeysCount` | `int function debug_GetStringListKeysCount(Form ObjKey) global native` |
| 546 | `debug_GetFormListKeysCount` | `int function debug_GetFormListKeysCount(Form ObjKey) global native` |
| 548 | `debug_GetIntKey` | `string function debug_GetIntKey(Form ObjKey, int index) global native` |
| 549 | `debug_GetFloatKey` | `string function debug_GetFloatKey(Form ObjKey, int index) global native` |
| 550 | `debug_GetStringKey` | `string function debug_GetStringKey(Form ObjKey, int index) global native` |
| 551 | `debug_GetFormKey` | `string function debug_GetFormKey(Form ObjKey, int index) global native` |
| 552 | `debug_GetIntListKey` | `string function debug_GetIntListKey(Form ObjKey, int index) global native` |
| 553 | `debug_GetFloatListKey` | `string function debug_GetFloatListKey(Form ObjKey, int index) global native` |
| 554 | `debug_GetStringListKey` | `string function debug_GetStringListKey(Form ObjKey, int index) global native` |
| 555 | `debug_GetFormListKey` | `string function debug_GetFormListKey(Form ObjKey, int index) global native` |
| 568 | `FileSetIntValue` | `int function FileSetIntValue(string KeyName, int value) global` |
| 571 | `FileSetFloatValue` | `float function FileSetFloatValue(string KeyName, float value) global` |
| 574 | `FileSetStringValue` | `string function FileSetStringValue(string KeyName, string value) global` |
| 577 | `FileSetFormValue` | `form function FileSetFormValue(string KeyName, Form value) global` |
| 581 | `FileAdjustIntValue` | `int function FileAdjustIntValue(string KeyName, int amount) global` |
| 584 | `FileAdjustFloatValue` | `float function FileAdjustFloatValue(string KeyName, float amount) global` |
| 588 | `FileUnsetIntValue` | `bool function FileUnsetIntValue(string KeyName) global` |
| 591 | `FileUnsetFloatValue` | `bool function FileUnsetFloatValue(string KeyName) global` |
| 594 | `FileUnsetStringValue` | `bool function FileUnsetStringValue(string KeyName) global` |
| 597 | `FileUnsetFormValue` | `bool function FileUnsetFormValue(string KeyName) global` |
| 601 | `FileHasIntValue` | `bool function FileHasIntValue(string KeyName) global` |
| 604 | `FileHasFloatValue` | `bool function FileHasFloatValue(string KeyName) global` |
| 607 | `FileHasStringValue` | `bool function FileHasStringValue(string KeyName) global` |
| 610 | `FileHasFormValue` | `bool function FileHasFormValue(string KeyName) global` |
| 614 | `FileGetIntValue` | `int function FileGetIntValue(string KeyName, int missing = 0) global` |
| 617 | `FileGetFloatValue` | `float function FileGetFloatValue(string KeyName, float missing = 0.0) global` |
| 620 | `FileGetStringValue` | `string function FileGetStringValue(string KeyName, string missing = "") global` |
| 623 | `FileGetFormValue` | `Form function FileGetFormValue(string KeyName, Form missing = none) global` |
| 627 | `FileIntListAdd` | `int function FileIntListAdd(string KeyName, int value, bool allowDuplicate = true) global` |
| 630 | `FileFloatListAdd` | `int function FileFloatListAdd(string KeyName, float value, bool allowDuplicate = true) global` |
| 633 | `FileStringListAdd` | `int function FileStringListAdd(string KeyName, string value, bool allowDuplicate = true) global` |
| 636 | `FileFormListAdd` | `int function FileFormListAdd(string KeyName, Form value, bool allowDuplicate = true) global` |
| 640 | `FileIntListAdjust` | `int function FileIntListAdjust(string KeyName, int index, int amount) global` |
| 643 | `FileFloatListAdjust` | `float function FileFloatListAdjust(string KeyName, int index, float amount) global` |
| 647 | `FileIntListRemove` | `int function FileIntListRemove(string KeyName, int value, bool allInstances = false) global` |
| 650 | `FileFloatListRemove` | `int function FileFloatListRemove(string KeyName, float value, bool allInstances = false) global` |
| 653 | `FileStringListRemove` | `int function FileStringListRemove(string KeyName, string value, bool allInstances = false) global` |
| 656 | `FileFormListRemove` | `int function FileFormListRemove(string KeyName, Form value, bool allInstances = false) global` |
| 660 | `FileIntListGet` | `int function FileIntListGet(string KeyName, int index) global` |
| 663 | `FileFloatListGet` | `float function FileFloatListGet(string KeyName, int index) global` |
| 666 | `FileStringListGet` | `string function FileStringListGet(string KeyName, int index) global` |
| 669 | `FileFormListGet` | `Form function FileFormListGet(string KeyName, int index) global` |
| 673 | `FileIntListSet` | `int function FileIntListSet(string KeyName, int index, int value) global` |
| 676 | `FileFloatListSet` | `float function FileFloatListSet(string KeyName, int index, float value) global` |
| 679 | `FileStringListSet` | `string function FileStringListSet(string KeyName, int index, string value) global` |
| 682 | `FileFormListSet` | `Form function FileFormListSet(string KeyName, int index, Form value) global` |
| 686 | `FileIntListClear` | `int function FileIntListClear(string KeyName) global` |
| 689 | `FileFloatListClear` | `int function FileFloatListClear(string KeyName) global` |
| 692 | `FileStringListClear` | `int function FileStringListClear(string KeyName) global` |
| 695 | `FileFormListClear` | `int function FileFormListClear(string KeyName) global` |
| 699 | `FileIntListRemoveAt` | `bool function FileIntListRemoveAt(string KeyName, int index) global` |
| 702 | `FileFloatListRemoveAt` | `bool function FileFloatListRemoveAt(string KeyName, int index) global` |
| 705 | `FileStringListRemoveAt` | `bool function FileStringListRemoveAt(string KeyName, int index) global` |
| 708 | `FileFormListRemoveAt` | `bool function FileFormListRemoveAt(string KeyName, int index) global` |
| 712 | `FileIntListInsert` | `bool function FileIntListInsert(string KeyName, int index, int value) global` |
| 715 | `FileFloatListInsert` | `bool function FileFloatListInsert(string KeyName, int index, float value) global` |
| 718 | `FileStringListInsert` | `bool function FileStringListInsert(string KeyName, int index, string value) global` |
| 721 | `FileFormListInsert` | `bool function FileFormListInsert(string KeyName, int index, Form value) global` |
| 725 | `FileIntListCount` | `int function FileIntListCount(string KeyName) global` |
| 728 | `FileFloatListCount` | `int function FileFloatListCount(string KeyName) global` |
| 731 | `FileStringListCount` | `int function FileStringListCount(string KeyName) global` |
| 734 | `FileFormListCount` | `int function FileFormListCount(string KeyName) global` |
| 738 | `FileIntListFind` | `int function FileIntListFind(string KeyName, int value) global` |
| 741 | `FileFloatListFind` | `int function FileFloatListFind(string KeyName, float value) global` |
| 744 | `FileStringListFind` | `int function FileStringListFind(string KeyName, string value) global` |
| 747 | `FileFormListFind` | `int function FileFormListFind(string KeyName, Form value) global` |
| 751 | `FileIntListHas` | `bool function FileIntListHas(string KeyName, int value) global` |
| 754 | `FileFloatListHas` | `bool function FileFloatListHas(string KeyName, float value) global` |
| 757 | `FileStringListHas` | `bool function FileStringListHas(string KeyName, string value) global` |
| 760 | `FileFormListHas` | `bool function FileFormListHas(string KeyName, Form value) global` |
| 764 | `FileIntListSlice` | `function FileIntListSlice(string KeyName, int[] slice, int startIndex = 0) global` |
| 767 | `FileFloatListSlice` | `function FileFloatListSlice(string KeyName, float[] slice, int startIndex = 0) global` |
| 770 | `FileStringListSlice` | `function FileStringListSlice(string KeyName, string[] slice, int startIndex = 0) global` |
| 773 | `FileFormListSlice` | `function FileFormListSlice(string KeyName, Form[] slice, int startIndex = 0) global` |
| 777 | `FileIntListResize` | `int function FileIntListResize(string KeyName, int toLength, int filler = 0) global` |
| 780 | `FileFloatListResize` | `int function FileFloatListResize(string KeyName, int toLength, float filler = 0.0) global` |
| 783 | `FileStringListResize` | `int function FileStringListResize(string KeyName, int toLength, string filler = "") global` |
| 786 | `FileFormListResize` | `int function FileFormListResize(string KeyName, int toLength, Form filler = none) global` |
| 791 | `FileIntListCopy` | `bool function FileIntListCopy(string KeyName, int[] copy) global` |
| 794 | `FileFloatListCopy` | `bool function FileFloatListCopy(string KeyName, float[] copy) global` |
| 797 | `FileStringListCopy` | `bool function FileStringListCopy(string KeyName, string[] copy) global` |
| 800 | `FileFormListCopy` | `bool function FileFormListCopy(string KeyName, Form[] copy) global` |
| 804 | `debug_SaveFile` | `function debug_SaveFile() global` |
| 812 | `debug_FileGetIntKeysCount` | `int function debug_FileGetIntKeysCount() global` |
| 816 | `debug_FileGetFloatKeysCount` | `int function debug_FileGetFloatKeysCount() global` |
| 820 | `debug_FileGetStringKeysCount` | `int function debug_FileGetStringKeysCount() global` |
| 824 | `debug_FileGetIntListKeysCount` | `int function debug_FileGetIntListKeysCount() global` |
| 828 | `debug_FileGetFloatListKeysCount` | `int function debug_FileGetFloatListKeysCount() global` |
| 832 | `debug_FileGetStringListKeysCount` | `int function debug_FileGetStringListKeysCount() global` |
| 836 | `debug_FileGetIntKey` | `string function debug_FileGetIntKey(int index) global` |
| 840 | `debug_FileGetFloatKey` | `string function debug_FileGetFloatKey(int index) global` |
| 844 | `debug_FileGetStringKey` | `string function debug_FileGetStringKey(int index) global` |
| 848 | `debug_FileGetIntListKey` | `string function debug_FileGetIntListKey(int index) global` |
| 852 | `debug_FileGetFloatListKey` | `string function debug_FileGetFloatListKey(int index) global` |
| 856 | `debug_FileGetStringListKey` | `string function debug_FileGetStringListKey(int index) global` |
| 860 | `debug_FileDeleteAllValues` | `function debug_FileDeleteAllValues() global` |
| 863 | `debug_SetDebugMode` | `function debug_SetDebugMode(bool enabled) global` |
| 866 | `ImportFile` | `bool function ImportFile(string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false) global` |
| 869 | `ExportFile` | `bool function ExportFile(string fileName, string restrictKey = "", int restrictType = -1, Form restrictForm = none, bool restrictGlobal = false, bool keyContains = false, bool append = true) global` |

## JsonUtil

Source: `Scripts/Source/JsonUtil.psc` — blob `7618e9f385daf60b94cde392015489fd585c6098`

| Line | Function | Declaration |
|---:|---|---|
| 33 | `Load` | `bool function Load(string FileName) global native` |
| 34 | `Save` | `bool function Save(string FileName, bool minify = false) global native` |
| 35 | `Unload` | `bool function Unload(string FileName, bool saveChanges = true, bool minify = false) global native` |
| 38 | `IsPendingSave` | `bool function IsPendingSave(string FileName) global native` |
| 40 | `IsGood` | `bool function IsGood(string FileName) global native` |
| 42 | `GetErrors` | `string function GetErrors(string FileName) global native` |
| 44 | `JsonInFolder` | `string[] function JsonInFolder(string folderPath) global native` |
| 46 | `JsonExists` | `bool function JsonExists(string FileName) global` |
| 56 | `SetIntValue` | `int function SetIntValue(string FileName, string KeyName, int value) global native` |
| 57 | `SetFloatValue` | `float function SetFloatValue(string FileName, string KeyName, float value) global native` |
| 58 | `SetStringValue` | `string function SetStringValue(string FileName, string KeyName, string value) global native` |
| 59 | `SetFormValue` | `form function SetFormValue(string FileName, string KeyName, form value) global native` |
| 61 | `GetIntValue` | `int function GetIntValue(string FileName, string KeyName, int missing = 0) global native` |
| 62 | `GetFloatValue` | `float function GetFloatValue(string FileName, string KeyName, float missing = 0.0) global native` |
| 63 | `GetStringValue` | `string function GetStringValue(string FileName, string KeyName, string missing = "") global native` |
| 64 | `GetFormValue` | `form function GetFormValue(string FileName, string KeyName, form missing = none) global native` |
| 66 | `UnsetIntValue` | `bool function UnsetIntValue(string FileName, string KeyName) global native` |
| 67 | `UnsetFloatValue` | `bool function UnsetFloatValue(string FileName, string KeyName) global native` |
| 68 | `UnsetStringValue` | `bool function UnsetStringValue(string FileName, string KeyName) global native` |
| 69 | `UnsetFormValue` | `bool function UnsetFormValue(string FileName, string KeyName) global native` |
| 71 | `HasIntValue` | `bool function HasIntValue(string FileName, string KeyName) global native` |
| 72 | `HasFloatValue` | `bool function HasFloatValue(string FileName, string KeyName) global native` |
| 73 | `HasStringValue` | `bool function HasStringValue(string FileName, string KeyName) global native` |
| 74 | `HasFormValue` | `bool function HasFormValue(string FileName, string KeyName) global native` |
| 76 | `IntListAdd` | `int function IntListAdd(string FileName, string KeyName, int value, bool allowDuplicate = true) global native` |
| 77 | `FloatListAdd` | `int function FloatListAdd(string FileName, string KeyName, float value, bool allowDuplicate = true) global native` |
| 78 | `StringListAdd` | `int function StringListAdd(string FileName, string KeyName, String value, bool allowDuplicate = true) global native` |
| 79 | `FormListAdd` | `int function FormListAdd(string FileName, string KeyName, Form value, bool allowDuplicate = true) global native` |
| 81 | `IntListGet` | `Int function IntListGet(string FileName, string KeyName, int index) global native` |
| 82 | `FloatListGet` | `Float function FloatListGet(string FileName, string KeyName, int index) global native` |
| 83 | `StringListGet` | `String function StringListGet(string FileName, string KeyName, int index) global native` |
| 84 | `FormListGet` | `Form function FormListGet(string FileName, string KeyName, int index) global native` |
| 86 | `IntListSet` | `Int function IntListSet(string FileName, string KeyName, int index, int value) global native` |
| 87 | `FloatListSet` | `Float function FloatListSet(string FileName, string KeyName, int index, float value) global native` |
| 88 | `StringListSet` | `String function StringListSet(string FileName, string KeyName, int index, String value) global native` |
| 89 | `FormListSet` | `Form function FormListSet(string FileName, string KeyName, int index, Form value) global native` |
| 91 | `IntListRemove` | `int function IntListRemove(string FileName, string KeyName, int value, bool allInstances = true) global native` |
| 92 | `FloatListRemove` | `int function FloatListRemove(string FileName, string KeyName, float value, bool allInstances = true) global native` |
| 93 | `StringListRemove` | `int function StringListRemove(string FileName, string KeyName, String value, bool allInstances = true) global native` |
| 94 | `FormListRemove` | `int function FormListRemove(string FileName, string KeyName, Form value, bool allInstances = true) global native` |
| 96 | `IntListInsertAt` | `bool function IntListInsertAt(string FileName, string KeyName, int index, int value) global native` |
| 97 | `FloatListInsertAt` | `bool function FloatListInsertAt(string FileName, string KeyName, int index, float value) global native` |
| 98 | `StringListInsertAt` | `bool function StringListInsertAt(string FileName, string KeyName, int index, String value) global native` |
| 99 | `FormListInsertAt` | `bool function FormListInsertAt(string FileName, string KeyName, int index, Form value) global native` |
| 101 | `IntListRemoveAt` | `bool function IntListRemoveAt(string FileName, string KeyName, int index) global native` |
| 102 | `FloatListRemoveAt` | `bool function FloatListRemoveAt(string FileName, string KeyName, int index) global native` |
| 103 | `StringListRemoveAt` | `bool function StringListRemoveAt(string FileName, string KeyName, int index) global native` |
| 104 | `FormListRemoveAt` | `bool function FormListRemoveAt(string FileName, string KeyName, int index) global native` |
| 106 | `IntListClear` | `int function IntListClear(string FileName, string KeyName) global native` |
| 107 | `FloatListClear` | `int function FloatListClear(string FileName, string KeyName) global native` |
| 108 | `StringListClear` | `int function StringListClear(string FileName, string KeyName) global native` |
| 109 | `FormListClear` | `int function FormListClear(string FileName, string KeyName) global native` |
| 111 | `IntListCount` | `int function IntListCount(string FileName, string KeyName) global native` |
| 112 | `FloatListCount` | `int function FloatListCount(string FileName, string KeyName) global native` |
| 113 | `StringListCount` | `int function StringListCount(string FileName, string KeyName) global native` |
| 114 | `FormListCount` | `int function FormListCount(string FileName, string KeyName) global native` |
| 116 | `IntListCountValue` | `int function IntListCountValue(string FileName, string KeyName, int value, bool exclude = false) global native` |
| 117 | `FloatListCountValue` | `int function FloatListCountValue(string FileName, string KeyName, float value, bool exclude = false) global native` |
| 118 | `StringListCountValue` | `int function StringListCountValue(string FileName, string KeyName, String value, bool exclude = false) global native` |
| 119 | `FormListCountValue` | `int function FormListCountValue(string FileName, string KeyName, Form value, bool exclude = false) global native` |
| 121 | `IntListFind` | `int function IntListFind(string FileName, string KeyName, int value) global native` |
| 122 | `FloatListFind` | `int function FloatListFind(string FileName, string KeyName, float value) global native` |
| 123 | `StringListFind` | `int function StringListFind(string FileName, string KeyName, String value) global native` |
| 124 | `FormListFind` | `int function FormListFind(string FileName, string KeyName, Form value) global native` |
| 126 | `IntListHas` | `bool function IntListHas(string FileName, string KeyName, int value) global native` |
| 127 | `FloatListHas` | `bool function FloatListHas(string FileName, string KeyName, float value) global native` |
| 128 | `StringListHas` | `bool function StringListHas(string FileName, string KeyName, String value) global native` |
| 129 | `FormListHas` | `bool function FormListHas(string FileName, string KeyName, Form value) global native` |
| 131 | `IntListSlice` | `function IntListSlice(string FileName, string KeyName, int[] slice, int startIndex = 0) global native` |
| 132 | `FloatListSlice` | `function FloatListSlice(string FileName, string KeyName, float[] slice, int startIndex = 0) global native` |
| 133 | `StringListSlice` | `function StringListSlice(string FileName, string KeyName, string[] slice, int startIndex = 0) global native` |
| 134 | `FormListSlice` | `function FormListSlice(string FileName, string KeyName, Form[] slice, int startIndex = 0) global native` |
| 136 | `IntListResize` | `int function IntListResize(string FileName, string KeyName, int toLength, int filler = 0) global native` |
| 137 | `FloatListResize` | `int function FloatListResize(string FileName, string KeyName, int toLength, float filler = 0.0) global native` |
| 138 | `StringListResize` | `int function StringListResize(string FileName, string KeyName, int toLength, string filler = "") global native` |
| 139 | `FormListResize` | `int function FormListResize(string FileName, string KeyName, int toLength, Form filler = none) global native` |
| 141 | `IntListCopy` | `bool function IntListCopy(string FileName, string KeyName, int[] copy) global native` |
| 142 | `FloatListCopy` | `bool function FloatListCopy(string FileName, string KeyName, float[] copy) global native` |
| 143 | `StringListCopy` | `bool function StringListCopy(string FileName, string KeyName, string[] copy) global native` |
| 144 | `FormListCopy` | `bool function FormListCopy(string FileName, string KeyName, Form[] copy) global native` |
| 146 | `IntListToArray` | `int[] function IntListToArray(string FileName, string KeyName) global native` |
| 147 | `FloatListToArray` | `float[] function FloatListToArray(string FileName, string KeyName) global native` |
| 148 | `StringListToArray` | `string[] function StringListToArray(string FileName, string KeyName) global native` |
| 149 | `FormListToArray` | `Form[] function FormListToArray(string FileName, string KeyName) global native` |
| 151 | `AdjustIntValue` | `int function AdjustIntValue(string FileName, string KeyName, int amount) global native` |
| 152 | `AdjustFloatValue` | `float function AdjustFloatValue(string FileName, string KeyName, float amount) global native` |
| 153 | `IntListAdjust` | `Int function IntListAdjust(string FileName, string KeyName, int index, Int amount) global native` |
| 154 | `FloatListAdjust` | `float function FloatListAdjust(string FileName, string KeyName, int index, float amount) global native` |
| 156 | `IntListRandom` | `int function IntListRandom(string FileName, string KeyName) global native` |
| 157 | `FloatListRandom` | `float function FloatListRandom(string FileName, string KeyName) global native` |
| 158 | `StringListRandom` | `string function StringListRandom(string FileName, string KeyName) global native` |
| 159 | `FormListRandom` | `Form function FormListRandom(string FileName, string KeyName) global native` |
| 161 | `CountIntValuePrefix` | `int function CountIntValuePrefix(string FileName, string PrefixKey) global native` |
| 162 | `CountFloatValuePrefix` | `int function CountFloatValuePrefix(string FileName, string PrefixKey) global native` |
| 163 | `CountStringValuePrefix` | `int function CountStringValuePrefix(string FileName, string PrefixKey) global native` |
| 164 | `CountFormValuePrefix` | `int function CountFormValuePrefix(string FileName, string PrefixKey) global native` |
| 166 | `CountIntListPrefix` | `int function CountIntListPrefix(string FileName, string PrefixKey) global native` |
| 167 | `CountFloatListPrefix` | `int function CountFloatListPrefix(string FileName, string PrefixKey) global native` |
| 168 | `CountStringListPrefix` | `int function CountStringListPrefix(string FileName, string PrefixKey) global native` |
| 169 | `CountFormListPrefix` | `int function CountFormListPrefix(string FileName, string PrefixKey) global native` |
| 171 | `CountAllPrefix` | `int function CountAllPrefix(string FileName, string PrefixKey) global native` |
| 183 | `SetPathIntValue` | `function SetPathIntValue(string FileName, string Path, int value) global native` |
| 184 | `SetPathFloatValue` | `function SetPathFloatValue(string FileName, string Path, float value) global native` |
| 185 | `SetPathStringValue` | `function SetPathStringValue(string FileName, string Path, string value) global native` |
| 186 | `SetPathFormValue` | `function SetPathFormValue(string FileName, string Path, form value) global native` |
| 188 | `SetRawPathValue` | `bool function SetRawPathValue(string FileName, string Path, string RawJSON) global native` |
| 190 | `GetPathIntValue` | `int function GetPathIntValue(string FileName, string Path, int missing = 0) global native` |
| 191 | `GetPathFloatValue` | `float function GetPathFloatValue(string FileName, string Path, float missing = 0.0) global native` |
| 192 | `GetPathStringValue` | `string function GetPathStringValue(string FileName, string Path, string missing = "") global native` |
| 193 | `GetPathFormValue` | `form function GetPathFormValue(string FileName, string Path, form missing = none) global native` |
| 194 | `GetPathBoolValue` | `bool function GetPathBoolValue(string FileName, string Path, bool missing = false) global` |
| 198 | `PathIntElements` | `int[] function PathIntElements(string FileName, string Path, int invalidType = 0) global native` |
| 199 | `PathFloatElements` | `float[] function PathFloatElements(string FileName, string Path, float invalidType = 0.0) global native` |
| 200 | `PathStringElements` | `string[] function PathStringElements(string FileName, string Path, string invalidType = "") global native` |
| 201 | `PathFormElements` | `form[] function PathFormElements(string FileName, string Path, form invalidType = none) global native` |
| 203 | `FindPathIntElement` | `int function FindPathIntElement(string FileName, string Path, int toFind) global native` |
| 204 | `FindPathFloatElement` | `int function FindPathFloatElement(string FileName, string Path, float toFind) global native` |
| 205 | `FindPathStringElement` | `int function FindPathStringElement(string FileName, string Path, string toFind) global native` |
| 206 | `FindPathFormElement` | `int function FindPathFormElement(string FileName, string Path, form toFind) global native` |
| 208 | `PathCount` | `int function PathCount(string FileName, string Path) global native` |
| 209 | `PathMembers` | `string[] function PathMembers(string FileName, string Path) global native` |
| 211 | `CanResolvePath` | `bool function CanResolvePath(string FileName, string Path) global native` |
| 212 | `IsPathString` | `bool function IsPathString(string FileName, string Path) global native` |
| 213 | `IsPathNumber` | `bool function IsPathNumber(string FileName, string Path) global native` |
| 214 | `IsPathForm` | `bool function IsPathForm(string FileName, string Path) global native` |
| 215 | `IsPathBool` | `bool function IsPathBool(string FileName, string Path) global native` |
| 216 | `IsPathArray` | `bool function IsPathArray(string FileName, string Path) global native` |
| 217 | `IsPathObject` | `bool function IsPathObject(string FileName, string Path) global native` |
| 219 | `SetPathIntArray` | `function SetPathIntArray(string FileName, string Path, int[] arr, bool append = false) global native` |
| 220 | `SetPathFloatArray` | `function SetPathFloatArray(string FileName, string Path, float[] arr, bool append = false) global native` |
| 221 | `SetPathStringArray` | `function SetPathStringArray(string FileName, string Path, string[] arr, bool append = false) global native` |
| 222 | `SetPathFormArray` | `function SetPathFormArray(string FileName, string Path, form[] arr, bool append = false) global native` |
| 224 | `ClearPath` | `function ClearPath(string FileName, string Path) global native` |
| 225 | `ClearPathIndex` | `function ClearPathIndex(string FileName, string Path, int Index) global native` |
| 228 | `ClearAll` | `function ClearAll(string FileName) global native` |

## ActorUtil

Source: `Scripts/Source/ActorUtil.psc` — blob `cff8e7b69c9f9edcb6f8051699c817e7d3d34b37`

| Line | Function | Declaration |
|---:|---|---|
| 13 | `AddPackageOverride` | `function AddPackageOverride(Actor targetActor, Package targetPackage, int priority = 30, int flags = 0) global native` |
| 16 | `RemovePackageOverride` | `bool function RemovePackageOverride(Actor targetActor, Package targetPackage) global native` |
| 19 | `CountPackageOverride` | `int function CountPackageOverride(Actor targetActor) global native` |
| 22 | `ClearPackageOverride` | `int function ClearPackageOverride(Actor targetActor) global native` |
| 25 | `RemoveAllPackageOverride` | `int function RemoveAllPackageOverride(Package targetPackage) global native` |

## ObjectUtil

Source: `Scripts/Source/ObjectUtil.psc` — blob `5f7be6a55a1b060efc4c58da7f56c905c7ba65f6`

| Line | Function | Declaration |
|---:|---|---|

## MiscUtil

Source: `Scripts/Source/MiscUtil.psc` — blob `ccbf5e6b59f7954ae525ba1c978d08900a2e03b3`

| Line | Function | Declaration |
|---:|---|---|
| 11 | `ScanCellObjects` | `ObjectReference[] function ScanCellObjects(int formType, ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none) global native` |
| 18 | `ScanCellNPCs` | `Actor[] function ScanCellNPCs(ObjectReference CenterOn, float radius = 0.0, Keyword HasKeyword = none, bool IgnoreDead = true) global native` |
| 22 | `ScanCellNPCsByFaction` | `Actor[] function ScanCellNPCsByFaction(Faction FindFaction, ObjectReference CenterOn, float radius = 0.0, int minRank = 0, int maxRank = 127, bool IgnoreDead = true) global native` |
| 30 | `ToggleFreeCamera` | `function ToggleFreeCamera(bool stopTime = false) global native` |
| 32 | `SetFreeCameraSpeed` | `function SetFreeCameraSpeed(float speed) global native` |
| 35 | `SetFreeCameraState` | `function SetFreeCameraState(bool enable, float speed = 10.0) global native` |
| 47 | `FilesInFolder` | `string[] function FilesInFolder(string directory, string extension="*") global native` |
| 51 | `FoldersInFolder` | `string[] function FoldersInFolder(string directory) global native` |
| 54 | `FileExists` | `bool function FileExists(string fileName) global native` |
| 58 | `ReadFromFile` | `string function ReadFromFile(string fileName) global native` |
| 61 | `WriteToFile` | `bool function WriteToFile(string fileName, string text, bool append = true, bool timestamp = false) global native` |
| 69 | `PrintConsole` | `function PrintConsole(string text) global native` |
| 72 | `GetRaceEditorID` | `string function GetRaceEditorID(Race raceForm) global native` |
| 75 | `GetActorRaceEditorID` | `string function GetActorRaceEditorID(Actor actorRef) global native` |
| 78 | `SetMenus` | `function SetMenus(bool enabled) global native` |
| 85 | `GetNodeRotation` | `float function GetNodeRotation(ObjectReference obj, string nodeName, bool firstPerson, int rotationIndex) global` |
| 92 | `ExecuteBat` | `function ExecuteBat(string fileName) global` |
| 97 | `ScanCellActors` | `Actor[] function ScanCellActors(ObjectReference CenterOn, float radius = 5000.0, Keyword HasKeyword = none) global` |


## Interpretation rules

1. A declaration marked `native` requires the PapyrusUtil DLL to load and register it.
2. Non-native wrapper functions can still depend on SKSE/PapyrusUtil native functions called internally.
3. `StorageUtil` and `JsonUtil` deliberately expose parallel typed APIs but different storage backends.
4. Form-valued persistent data requires form identity resolution across load order changes; preserve plugin/version provenance when debugging missing Forms.
5. Deprecated File* StorageUtil APIs proxy to JsonUtil's shared StorageUtil JSON compatibility file.
6. `ObjectUtil.psc` in this source explicitly states its old functions no longer function in current PapyrusUtilSE and are commented out to cause compiler errors during old-script conversions.
