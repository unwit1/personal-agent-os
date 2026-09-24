# JContainers Native Papyrus Registration Catalog

Imported: 2026-09-24
Upstream: `SilverIce/JContainers`
Status: source-derived registration inventory

This catalog inventories native registration declarations. `REGISTERF` metadata is the authoritative source for Papyrus-visible names/comments in this code generation architecture.

## tes_object.h

Source: `JContainers/src/api_3/tes_object.h`
Blob: `48a881ba7db5e97f59a4146bfd5237b53ae7e7a8`
Registration declarations captured: 40

| Line | Registration source |
|---:|---|
| 17 | `REGISTER_TES_NAME("JValue");` |
| 32 | `REGISTERF2(retain, "* tag=\"\"",` |
| 51 | `REGISTERF2(release, "*", "Releases the object and returns zero, so you can release and nullify with one line of code: object = JValue.release(object)");` |
| 64 | `REGISTERF2(releaseAndRetain, "previousObject newObject tag=\"\"",` |
| 82 | `REGISTERF2(releaseObjectsWithTag, "tag",` |
| 92 | `REGISTERF2(zeroLifetime, "*", "Minimizes the time JC temporarily owns the object, returns the object.\n\` |
| 122 | `REGISTERF2(addToPool, "* poolName",` |
| 139 | `REGISTERF2(cleanPool, "poolName", nullptr);` |
| 144 | `REGISTERF2(shallowCopy, "*", "--- Mics. functionality\n\nReturns shallow copy (won't copy child objects)");` |
| 149 | `REGISTERF2(deepCopy, "*", "Returns deep copy");` |
| 154 | `REGISTERF2(isExists, "*", "Tests whether given object identifier points to existing object");` |
| 160 | `REGISTERF(isCast<array>, "isArray", "*", "Returns true if the object is map, array or formmap container");` |
| 161 | `REGISTERF(isCast<map>, "isMap", "*", nullptr);` |
| 162 | `REGISTERF(isCast<form_map>, "isFormMap", "*", nullptr);` |
| 163 | `REGISTERF(isCast<integer_map>, "isIntegerMap", "*", nullptr);` |
| 168 | `REGISTERF2(empty, "*", "Returns true, if the container is empty");` |
| 173 | `REGISTERF2(count, "*", "Returns amount of items in the container");` |
| 180 | `REGISTERF2(clear, "*", "Removes all items from the container");` |
| 186 | `REGISTERF2(readFromFile, "filePath", "JSON serialization/deserialization:\n\nCreates and returns a new container object containing contents of JSON file");` |
| 225 | `REGISTERF2(readFromDirectory, "directoryPath extension=\"\"",` |
| 233 | `REGISTERF2(objectFromPrototype, "prototype", "Creates a new container object using given JSON string");` |
| 242 | `REGISTERF2(toString, "* indentation=2", "Serializes the object into a JSON-formatted string.\n"` |
| 263 | `REGISTERF(writeToFile, "writeToFile", "* filePath", "Writes the object into JSON file");` |
| 280 | `REGISTERF(hasPath, "hasPath", "* path",` |
| 286 | `REGISTERF(solvedValueType, "solvedValueType", "* path", "Returns type of resolved value. "VALUE_TYPE_COMMENT);` |
| 301 | `REGISTERF(resolveGetter<Float32>, "solveFlt", "* path default=0.0", "Attempts to retrieve value at given path. If fails, returns @default value");` |
| 302 | `REGISTERF(resolveGetter<SInt32>, "solveInt", "* path default=0", nullptr);` |
| 303 | `REGISTERF(resolveGetter<skse::string_ref>, "solveStr", "* path default=\"\"", nullptr);` |
| 304 | `REGISTERF(resolveGetter<Handle>, "solveObj", "* path default=0", nullptr);` |
| 305 | `REGISTERF(resolveGetter<form_ref>, "solveForm", "* path default=None", nullptr);` |
| 315 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "* path value createMissingKeys=false",` |
| 319 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "* path value createMissingKeys=false", nullptr);` |
| 320 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "* path value createMissingKeys=false", nullptr);` |
| 321 | `REGISTERF(solveSetter<ref>, "solveObjSetter", "* path value createMissingKeys=false", nullptr);` |
| 322 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "* path value createMissingKeys=false", nullptr);` |
| 366 | `REGISTERF(evalLua<Float32>, "evalLuaFlt", "* luaCode default=0.0", "Evaluates piece of lua code. Lua support is experimental");` |
| 367 | `REGISTERF(evalLua<SInt32>, "evalLuaInt", "* luaCode default=0", nullptr);` |
| 368 | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", "* luaCode default=\"\"", nullptr);` |
| 369 | `REGISTERF(evalLua<Handle>, "evalLuaObj", "* luaCode default=0", nullptr);` |
| 370 | `REGISTERF(evalLua<form_ref>, "evalLuaForm", "* luaCode default=None", nullptr);` |

## tes_array.h

Source: `JContainers/src/api_3/tes_array.h`
Blob: `1d8450e020952a9efc3f1d0df3bb74e238d53142`
Registration declarations captured: 44

| Line | Registration source |
|---:|---|
| 16 | `REGISTER_TES_NAME("JArray");` |
| 37 | `REGISTERF(tes_object::object<array>, "object", "", kCommentObject);` |
| 51 | `REGISTERF2(objectWithSize, "size", "Creates a new array of given size, filled with empty (None) items");` |
| 67 | `REGISTERF(fromArray<SInt32>, "objectWithInts", "values",` |
| 70 | `REGISTERF(fromArray<skse::string_ref>, "objectWithStrings",  "values", nullptr);` |
| 71 | `REGISTERF(fromArray<Float32>, "objectWithFloats",  "values", nullptr);` |
| 72 | `REGISTERF(fromArray<bool>, "objectWithBooleans",  "values", nullptr);` |
| 73 | `REGISTERF(ARGS(fromArray<TESForm*, form_ref>), "objectWithForms", "values", nullptr);` |
| 93 | `REGISTERF2(subArray, "* startIndex endIndex", "Creates a new array containing all the values from the source array in range [startIndex, endIndex)");` |
| 106 | `REGISTERF2(addFromArray, "* source insertAtIndex=-1",` |
| 133 | `REGISTERF2(addFromFormList, "* source insertAtIndex=-1", nullptr);` |
| 143 | `REGISTERF(itemAtIndex<SInt32>, "getInt", "* index default=0", "Returns the item at the index of the array.\n"` |
| 145 | `REGISTERF(itemAtIndex<Float32>, "getFlt", "* index default=0.0", "");` |
| 146 | `REGISTERF(itemAtIndex<skse::string_ref>, "getStr", "* index default=\"\"", "");` |
| 147 | `REGISTERF(itemAtIndex<object_base*>, "getObj", "* index default=0", "");` |
| 148 | `REGISTERF(itemAtIndex<form_ref>, "getForm", "* index default=None", "");` |
| 167 | `REGISTERF(findVal<SInt32>, "findInt", "* value searchStartIndex=0",` |
| 172 | `REGISTERF(findVal<Float32>, "findFlt", "* value searchStartIndex=0", "");` |
| 173 | `REGISTERF(findVal<const char *>, "findStr", "* value searchStartIndex=0", "");` |
| 174 | `REGISTERF(findVal<object_base*>, "findObj", "* container searchStartIndex=0", "");` |
| 175 | `REGISTERF(findVal<form_ref>, "findForm", "* value searchStartIndex=0", "");` |
| 183 | `REGISTERF(replaceItemAtIndex<SInt32>, "setInt", "* index value", "Replaces existing value at the @index of the array with the new @value.\n"` |
| 185 | `REGISTERF(replaceItemAtIndex<Float32>, "setFlt", "* index value", "");` |
| 186 | `REGISTERF(replaceItemAtIndex<const char *>, "setStr", "* index value", "");` |
| 187 | `REGISTERF(replaceItemAtIndex<object_base*>, "setObj", "* index container", "");` |
| 188 | `REGISTERF(replaceItemAtIndex<form_ref>, "setForm", "* index value", "");` |
| 196 | `REGISTERF(addItemAt<SInt32>, "addInt", "* value addToIndex=-1", "Appends the @value/@container to the end of the array.\n\` |
| 198 | `REGISTERF(addItemAt<Float32>, "addFlt", "* value addToIndex=-1", "");` |
| 199 | `REGISTERF(addItemAt<const char *>, "addStr", "* value addToIndex=-1", "");` |
| 200 | `REGISTERF(addItemAt<object_base*>, "addObj", "* container addToIndex=-1", "");` |
| 201 | `REGISTERF(addItemAt<form_ref>, "addForm", "* value addToIndex=-1", "");` |
| 206 | `REGISTERF2(count, "*", "Returns count of the items in the array");` |
| 211 | `REGISTERF2(clear, "*", "Removes all the items from the array");` |
| 218 | `REGISTERF2(eraseIndex, "* index", "Erases the item at the index. "NEGATIVE_IDX_COMMENT);` |
| 233 | `REGISTERF2(eraseRange, "* first last", "Erases [first, last] index range of the items. "NEGATIVE_IDX_COMMENT` |
| 244 | `REGISTERF2(valueType, "* index", "Returns type of the value at the @index. "NEGATIVE_IDX_COMMENT"\n"VALUE_TYPE_COMMENT);` |
| 256 | `REGISTERF2(swapItems, "* index1 index2", "Exchanges the items at @index1 and @index2. "NEGATIVE_IDX_COMMENT);` |
| 265 | `REGISTERF2(sort, "*", "Sorts the items into ascending order (none < int < float < form < object < string). Returns the array itself");` |
| 276 | `REGISTERF2(unique, "*", "Sorts the items, removes duplicates. Returns array itself. You can treat it as JSet now");` |
| 333 | `REGISTERF(writeToPapyrusArray<SInt32>, "writeToIntegerPArray", ARGNAMES "0",` |
| 340 | `REGISTERF(writeToPapyrusArray<Float32>, "writeToFloatPArray", ARGNAMES "0.0", "");` |
| 341 | `REGISTERF(writeToPapyrusArray<form_ref>, "writeToFormPArray", ARGNAMES "None", "");` |
| 342 | `//REGISTERF(writeToPapyrusArray<bool>, "writeToBooleanPArray", ARGNAMES, "");` |
| 343 | `REGISTERF(writeToPapyrusArray<std::string>, "writeToStringPArray", ARGNAMES "\"\"", "");` |

## tes_map.h

Source: `JContainers/src/api_3/tes_map.h`
Blob: `3518a0f65666b54959863d69328e084f96b3733d`
Registration declarations captured: 29

| Line | Registration source |
|---:|---|
| 25 | `REGISTERF(tes_object::object<Cnt>, "object", "", kCommentObject);` |
| 32 | `REGISTERF(getItem<SInt32>, "getInt", "object key default=0", "Returns the value associated with the @key. If not, returns @default value");` |
| 33 | `REGISTERF(getItem<Float32>, "getFlt", "object key default=0.0", "");` |
| 34 | `REGISTERF(getItem<skse::string_ref>, "getStr", "object key default=\"\"", "");` |
| 35 | `REGISTERF(getItem<object_base*>, "getObj", "object key default=0", "");` |
| 36 | `REGISTERF(getItem<form_ref>, "getForm", "object key default=None", "");` |
| 42 | `REGISTERF(setItem<SInt32>, "setInt", "* key value", "Inserts @key: @value pair. Replaces existing pair with the same @key");` |
| 43 | `REGISTERF(setItem<Float32>, "setFlt", "* key value", "");` |
| 44 | `REGISTERF(setItem<const char *>, "setStr", "* key value", "");` |
| 45 | `REGISTERF(setItem<object_base*>, "setObj", "* key container", "");` |
| 46 | `REGISTERF(setItem<form_ref>, "setForm", "* key value", "");` |
| 51 | `REGISTERF2(hasKey, "* key", "Returns true, if the container has @key: value pair");` |
| 58 | `REGISTERF2(valueType, "* key", "Returns type of the value associated with the @key.\n"VALUE_TYPE_COMMENT);` |
| 75 | `REGISTERF(allKeys, "allKeys", "*", "Returns a new array containing all keys");` |
| 94 | `REGISTERF2(allKeysPArray, "*", "");` |
| 111 | `REGISTERF(allValues, "allValues", "*", "Returns a new array containing all values");` |
| 119 | `REGISTERF(removeKey, "removeKey", "* key", "Removes the pair from the container where the key equals to the @key");` |
| 128 | `REGISTERF2(count, "*", "Returns count of pairs in the conainer");` |
| 137 | `REGISTERF2(clear, "*", "Removes all pairs from the container");` |
| 156 | `REGISTERF2(addPairs, "* source overrideDuplicates", "Inserts key-value pairs from the source container");` |
| 214 | `REGISTER_TES_NAME("JMap");` |
| 221 | `REGISTERF(nextKey<skse::string_ref>, "nextKey", STR(* previousKey="" endKey=""), tes_map_nextKey_comment);` |
| 231 | `REGISTERF(getNthKey<skse::string_ref>, "getNthKey", "* keyIndex", getNthKey_comment());` |
| 235 | `REGISTER_TES_NAME("JFormMap");` |
| 236 | `REGISTERF(tes_form_map_ext::nextKey, "nextKey", STR(* previousKey=None endKey=None), tes_map_nextKey_comment);` |
| 237 | `REGISTERF(tes_form_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |
| 257 | `REGISTER_TES_NAME("JIntMap");` |
| 258 | `REGISTERF(tes_integer_map::nextKey, "nextKey", STR(* previousKey=0 endKey=0), tes_map_nextKey_comment);` |
| 259 | `REGISTERF(tes_integer_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |

## tes_db.h

Source: `JContainers/src/api_3/tes_db.h`
Blob: `a63e5aef707c532a504597993c9fa0e928e23687`
Registration declarations captured: 18

| Line | Registration source |
|---:|---|
| 8 | `REGISTER_TES_NAME("JDB");` |
| 20 | `REGISTERF(solveGetter<Float32>, "solveFlt", "path default=0.0",` |
| 32 | `REGISTERF(solveGetter<SInt32>, "solveInt", "path default=0", nullptr);` |
| 33 | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "path default=\"\"", nullptr);` |
| 34 | `REGISTERF(solveGetter<object_base*>, "solveObj", "path default=0", nullptr);` |
| 35 | `REGISTERF(solveGetter<form_ref>, "solveForm", "path default=None", nullptr);` |
| 41 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "path value createMissingKeys=false",` |
| 44 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "path value createMissingKeys=false", nullptr);` |
| 45 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "path value createMissingKeys=false", nullptr);` |
| 46 | `REGISTERF(solveSetter<object_base*>, "solveObjSetter", "path value createMissingKeys=false", nullptr);` |
| 47 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "path value createMissingKeys=false", nullptr);` |
| 59 | `REGISTERF(setObj, "setObj", "key object",` |
| 68 | `REGISTERF2(hasPath, "path", "Returns true, if JDB capable resolve given @path, i.e. if it able to execute solve* or solver*Setter functions successfully");` |
| 73 | `REGISTERF2(allKeys, "*", "returns new array containing all JDB keys");` |
| 78 | `REGISTERF2(allValues, "*", "returns new array containing all containers associated with JDB");` |
| 83 | `REGISTERF2(writeToFile, "path", "writes storage data into JSON file at given path");` |
| 87 | `REGISTERF2(readFromFile, "path",` |
| 93 | `REGISTERF2(root, "", "Returns underlying JDB's container - an instance of JMap.\nThe object being owned (retained) internally, so you don't have to (but can) retain or release it.")` |

## tes_form_db.h

Source: `JContainers/src/api_3/tes_form_db.h`
Blob: `8ff16cbb7f834392e1939fcc302048a12959f8e9`
Registration declarations captured: 27

| Line | Registration source |
|---:|---|
| 10 | `REGISTER_TES_NAME("JFormDB");` |
| 103 | `REGISTERF2(setEntry, "storageName fKey entry", "associates given form key and entry (container). set entry to zero to destroy association");` |
| 119 | `REGISTERF(makeMapEntry, "makeEntry", "storageName fKey", "returns (or creates new if not found) JMap entry for given storage and form");` |
| 126 | `REGISTERF2(findEntry, "storageName fKey", "search for entry for given storage and form");` |
| 139 | `REGISTERF(solveGetter<Float32>, "solveFlt", "fKey path default=0.0", "attempts to get value associated with path.");` |
| 140 | `REGISTERF(solveGetter<SInt32>, "solveInt", "fKey path default=0", nullptr);` |
| 141 | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "fKey path default=\"\"", nullptr);` |
| 142 | `REGISTERF(solveGetter<Handle>, "solveObj", "fKey path default=0", nullptr);` |
| 143 | `REGISTERF(solveGetter<form_ref>, "solveForm", "fKey path default=None", nullptr);` |
| 150 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "fKey path value createMissingKeys=false",` |
| 153 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 154 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 155 | `REGISTERF(solveSetter<object_stack_ref&>, "solveObjSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 156 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 162 | `REGISTERF2(hasPath, "fKey path", "returns true, if capable resolve given path, e.g. it able to execute solve* or solver*Setter functions successfully");` |
| 170 | `REGISTERF2(allKeys, "fKey key",` |
| 179 | `REGISTERF2(allValues, "fKey key", "returns new array containing all values");` |
| 187 | `REGISTERF(getItem<SInt32>, "getInt", "fKey key", "returns value associated with key");` |
| 188 | `REGISTERF(getItem<Float32>, "getFlt", "fKey key", "");` |
| 189 | `REGISTERF(getItem<skse::string_ref>, "getStr", "fKey key", "");` |
| 190 | `REGISTERF(getItem<object_base *>, "getObj", "fKey key", "");` |
| 191 | `REGISTERF(getItem<form_ref>, "getForm", "fKey key", "");` |
| 198 | `REGISTERF(setItem<SInt32>, "setInt", "fKey key value", "creates key-value association. replaces existing value if any");` |
| 199 | `REGISTERF(setItem<Float32>, "setFlt", "fKey key value", "");` |
| 200 | `REGISTERF(setItem<const char *>, "setStr", "fKey key value", "");` |
| 201 | `REGISTERF(setItem<object_stack_ref&>, "setObj", "fKey key container", "");` |
| 202 | `REGISTERF(setItem<form_ref>, "setForm", "fKey key value", "");` |

## tes_lua.h

Source: `JContainers/src/api_3/tes_lua.h`
Blob: `74bbf3ecc1176f9840eabd5d9934f2b2d8e65e71`
Registration declarations captured: 11

| Line | Registration source |
|---:|---|
| 16 | `REGISTERF(evalLua<Float32>, "evalLuaFlt", ARGNAMES "0.0" ARGNAMES_2,` |
| 30 | `REGISTERF(evalLua<SInt32>, "evalLuaInt", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| 31 | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", ARGNAMES R"("")" ARGNAMES_2, nullptr);` |
| 32 | `REGISTERF(evalLua<Handle>, "evalLuaObj", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| 33 | `REGISTERF(evalLua<TESForm*>, "evalLuaForm", ARGNAMES "None" ARGNAMES_2, nullptr);` |
| 47 | `REGISTERF(pushArg<const char*>, "setStr", ARGNAMES,` |
| 50 | `REGISTERF(pushArg<Float32>, "setFlt", ARGNAMES, "");` |
| 51 | `REGISTERF(pushArg<SInt32>, "setInt", ARGNAMES, "");` |
| 52 | `REGISTERF(pushArg<form_ref>, "setForm", ARGNAMES, "");` |
| 53 | `REGISTERF(pushArg<object_base*>, "setObj", ARGNAMES, "");` |
| 66 | `REGISTER_TES_NAME("JLua");` |

## tes_string.h

Source: `JContainers/src/api_3/tes_string.h`
Blob: `4a7c320b1861ddcf316771e0903b09d38530a8b1`
Registration declarations captured: 1

| Line | Registration source |
|---:|---|
| 37 | `REGISTERF2(wrap, "sourceText charactersPerLine=60",` |

## tes_atomic.h

Source: `JContainers/src/api_3/tes_atomic.h`
Blob: `c8e3f860e353d3f8de93c333df97b176a28b8f03`
Registration declarations captured: 21

| Line | Registration source |
|---:|---|
| 9 | `REGISTER_TES_NAME("JAtomic");` |
| 118 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::plus<SInt32>>), "fetchAddInt", PARAMS_INT,` |
| 128 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::plus<Float32>>), "fetchAddFlt", PARAMS_FLT, nullptr);` |
| 130 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::multiplies<SInt32>>), "fetchMultInt", PARAMS_INT, "x *= v");` |
| 131 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::multiplies<Float32>>), "fetchMultFlt", PARAMS_FLT, nullptr);` |
| 133 | `REGISTERF(ARGS(performAtomicFunction<int32_t, std::modulus<int32_t>>), "fetchModInt", PARAMS_INT, "x %= v");` |
| 135 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::divides<SInt32>>), "fetchDivInt", PARAMS_INT, "x /= v");` |
| 136 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::divides<Float32>>), "fetchDivFlt", PARAMS_FLT, nullptr);` |
| 138 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_and<uint32_t>>), "fetchAndInt", PARAMS_INT, "x &= v");` |
| 139 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_xor<uint32_t>>), "fetchXorInt", PARAMS_INT, "x ^= v");` |
| 140 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_or<uint32_t>>), "fetchOrInt", PARAMS_INT, "x \|= v");` |
| 146 | `REGISTERF(exchange<SInt32>, "exchangeInt", PARAMS_INT "0",` |
| 149 | `REGISTERF(exchange<Float32>, "exchangeFlt", PARAMS_INT "0.0", nullptr);` |
| 150 | `REGISTERF(exchange<std::string>, "exchangeStr", PARAMS_INT "\"\"", nullptr);` |
| 152 | `REGISTERF(exchange<form_ref>, "exchangeForm", PARAMS_INT "None", nullptr);` |
| 153 | `REGISTERF(exchange<object_base*>, "exchangeObj", PARAMS_INT "0", nullptr);` |
| 157 | `REGISTERF(compareExchange<SInt32>, "compareExchangeInt", PARAMS_INT "0",` |
| 160 | `REGISTERF(compareExchange<Float32>, "compareExchangeFlt", PARAMS_INT "0.0", nullptr);` |
| 161 | `REGISTERF(compareExchange<std::string>, "compareExchangeStr", PARAMS_INT "\"\"", nullptr);` |
| 163 | `REGISTERF(compareExchange<form_ref>, "compareExchangeForm", PARAMS_INT "None", nullptr);` |
| 164 | `REGISTERF(compareExchange<object_base*>, "compareExchangeObj", PARAMS_INT "0", nullptr);` |

## tes_jcontainers.h

Source: `JContainers/src/api_3/tes_jcontainers.h`
Blob: `2b07b7b22219b47d030de568d7369d8804e9d7ed`
Registration declarations captured: 1

| Line | Registration source |
|---:|---|
| 8 | `REGISTER_TES_NAME("JContainers");` |

## tes_api_3.cpp

Source: `JContainers/src/api_3/tes_api_3.cpp`
Blob: `6cf71de1e7278d66b2ed81dd92fbf3cc65c7fbac`
Registration declarations captured: 0

| Line | Registration source |
|---:|---|

## Extracted registration declarations

**192 registration lines** across 10 high-impact api_3 source files.

This count is a native-source registration-inventory count, not necessarily a one-to-one count of generated Papyrus functions: macros can register overload/family metadata or expand helper templates.

## Semantic model

### Handle
Papyrus-facing container identity is represented by an integer-like handle to a native JContainers object.

### JValue
Common lifecycle, type, path, JSON and object operations shared by container families.

### JArray
Ordered values. Values can include primitive data, Forms, and nested container handles.

### JMap
String-keyed map.

### JFormMap
Form-keyed map with Form identity/serialization semantics.

### JDB
Global database entry point backed by a JMap-like root.

### JFormDB
Form-associated global database wrapper.

### Retain / release
Explicit lifecycle operations can extend/release object lifetime; poor ownership discipline can cause leaks or premature object loss.

### Path resolution
Nested object paths allow traversal/mutation through maps/arrays without manually walking every layer.

### JSON serialization
JContainers can create/read/write nested object graphs to JSON; external files have cross-save/profile persistence implications.

### Lua
Embedded Lua can evaluate/manipulate JContainers object graphs. Treat code/data boundaries and untrusted input carefully.

## Provider rule

Do not label these functions as vanilla Papyrus, SKSE core, or PapyrusUtil. JContainers is an independent native provider with its own serialization/object-lifetime model.
