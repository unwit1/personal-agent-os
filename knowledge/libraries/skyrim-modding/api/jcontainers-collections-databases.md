# JContainers Current Papyrus Registration API — Collections and Databases

Imported: 2026-09-24
Source: https://github.com/SilverIce/JContainers · ref `master`
Registration statements cataloged: **149**
Status: current-source C++ Papyrus registration metadata catalog

## Why this is not a PSC catalog

Current JContainers source generates/binds its public Papyrus API from C++ reflection metadata in `JContainers/src/api_3/`. The current repository does not carry the public JArray/JMap/JValue/etc. PSC files as ordinary canonical source files. This catalog therefore records the **actual registration metadata** rather than pretending a historical distributed PSC package is the current API.

Macro semantics are sourced from `src/reflection/tes_binding.h`:
- `REGISTERF2(func,...)` publishes `#func` as the Papyrus function name.
- `REGISTERF(func,"Name",...)` publishes the explicit quoted name.
- STATELESS variants use the same naming rule but bind without per-context state.
- registration metadata also stores argument-name text and comments used by the generator.

For complex template registration expressions where a safe public name cannot be inferred mechanically, this catalog leaves the derived name blank and preserves the exact registration statement.

## JArray

Source: `JContainers/src/api_3/tes_array.h` · blob `eff6869dc0e3e49ad5f20c421cd8a695deb322af`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `object` | 37 | `REGISTERF(tes_object::object<array>, "object", "", kCommentObject);` |
| `objectWithSize` | 51 | `REGISTERF2(objectWithSize, "size", "Creates a new array of given size, filled with empty (None) items");` |
| `objectWithInts` | 67 | `REGISTERF(fromArray<SInt32>, "objectWithInts", "values", "Creates a new array that contains given values\n\ objectWithBooleans converts booleans into integers");` |
| `objectWithStrings` | 70 | `REGISTERF(fromArray<skse::string_ref>, "objectWithStrings", "values", nullptr);` |
| `objectWithFloats` | 71 | `REGISTERF(fromArray<Float32>, "objectWithFloats", "values", nullptr);` |
| `objectWithBooleans` | 72 | `REGISTERF(fromArray<bool>, "objectWithBooleans", "values", nullptr);` |
| `objectWithForms` | 73 | `REGISTERF(ARGS(fromArray<TESForm*, form_ref>), "objectWithForms", "values", nullptr);` |
| `subArray` | 93 | `REGISTERF2(subArray, "* startIndex endIndex", "Creates a new array containing all the values from the source array in range [startIndex, endIndex)");` |
| `addFromArray` | 106 | `REGISTERF2(addFromArray, "* source insertAtIndex=-1", "Inserts the values from the source array into this array. If insertAtIndex is -1 (default behaviour) it appends to the end.\n" NEGATIVE_IDX_COMMENT);` |
| `addFromFormList` | 133 | `REGISTERF2(addFromFormList, "* source insertAtIndex=-1", nullptr);` |
| `getInt` | 143 | `REGISTERF(itemAtIndex<SInt32>, "getInt", "* index default=0", "Returns the item at the index of the array.\n" NEGATIVE_IDX_COMMENT);` |
| `getFlt` | 145 | `REGISTERF(itemAtIndex<Float32>, "getFlt", "* index default=0.0", "");` |
| `getStr` | 146 | `REGISTERF(itemAtIndex<skse::string_ref>, "getStr", "* index default=\"\"", "");` |
| `getObj` | 147 | `REGISTERF(itemAtIndex<object_base*>, "getObj", "* index default=0", "");` |
| `getForm` | 148 | `REGISTERF(itemAtIndex<form_ref>, "getForm", "* index default=None", "");` |
| `findInt` | 167 | `REGISTERF(findVal<SInt32>, "findInt", "* value searchStartIndex=0", "Returns the index of the first found value/container that equals to given the value/container (default behaviour if searchStartIndex is 0).\n\ If nothing was found it returns -1.\n\ @searchStartIndex - index of the array where to start search\n" NEGATIVE_IDX_COMMENT);` |
| `findFlt` | 172 | `REGISTERF(findVal<Float32>, "findFlt", "* value searchStartIndex=0", "");` |
| `findStr` | 173 | `REGISTERF(findVal<const char *>, "findStr", "* value searchStartIndex=0", "");` |
| `findObj` | 174 | `REGISTERF(findVal<object_base*>, "findObj", "* container searchStartIndex=0", "");` |
| `findForm` | 175 | `REGISTERF(findVal<form_ref>, "findForm", "* value searchStartIndex=0", "");` |
| `setInt` | 183 | `REGISTERF(replaceItemAtIndex<SInt32>, "setInt", "* index value", "Replaces existing value at the @index of the array with the new @value.\n" NEGATIVE_IDX_COMMENT);` |
| `setFlt` | 185 | `REGISTERF(replaceItemAtIndex<Float32>, "setFlt", "* index value", "");` |
| `setStr` | 186 | `REGISTERF(replaceItemAtIndex<const char *>, "setStr", "* index value", "");` |
| `setObj` | 187 | `REGISTERF(replaceItemAtIndex<object_base*>, "setObj", "* index container", "");` |
| `setForm` | 188 | `REGISTERF(replaceItemAtIndex<form_ref>, "setForm", "* index value", "");` |
| `addInt` | 196 | `REGISTERF(addItemAt<SInt32>, "addInt", "* value addToIndex=-1", "Appends the @value/@container to the end of the array.\n\ If @addToIndex >= 0 it inserts value at given index. " NEGATIVE_IDX_COMMENT);` |
| `addFlt` | 198 | `REGISTERF(addItemAt<Float32>, "addFlt", "* value addToIndex=-1", "");` |
| `addStr` | 199 | `REGISTERF(addItemAt<const char *>, "addStr", "* value addToIndex=-1", "");` |
| `addObj` | 200 | `REGISTERF(addItemAt<object_base*>, "addObj", "* container addToIndex=-1", "");` |
| `addForm` | 201 | `REGISTERF(addItemAt<form_ref>, "addForm", "* value addToIndex=-1", "");` |
| `count` | 206 | `REGISTERF2(count, "*", "Returns count of the items in the array");` |
| `clear` | 211 | `REGISTERF2(clear, "*", "Removes all the items from the array");` |
| `eraseIndex` | 218 | `REGISTERF2(eraseIndex, "* index", "Erases the item at the index. "NEGATIVE_IDX_COMMENT);` |
| `eraseRange` | 233 | `REGISTERF2(eraseRange, "* first last", "Erases [first, last] index range of the items. "NEGATIVE_IDX_COMMENT "\nFor ex. with [1,-1] range it will erase everything except the first item");` |
| `valueType` | 244 | `REGISTERF2(valueType, "* index", "Returns type of the value at the @index. "NEGATIVE_IDX_COMMENT"\n"VALUE_TYPE_COMMENT);` |
| `swapItems` | 256 | `REGISTERF2(swapItems, "* index1 index2", "Exchanges the items at @index1 and @index2. "NEGATIVE_IDX_COMMENT);` |
| `sort` | 265 | `REGISTERF2(sort, "*", "Sorts the items into ascending order (none < int < float < form < object < string). Returns the array itself");` |
| `unique` | 276 | `REGISTERF2(unique, "*", "Sorts the items, removes duplicates. Returns array itself. You can treat it as JSet now");` |
| `writeToIntegerPArray` | 321 | `REGISTERF(writeToPapyrusArray<SInt32>, "writeToIntegerPArray", ARGNAMES "0", "TOTOTO??");` |
| `writeToFloatPArray` | 322 | `REGISTERF(writeToPapyrusArray<Float32>, "writeToFloatPArray", ARGNAMES "0.0", "");` |
| `writeToFormPArray` | 323 | `REGISTERF(writeToPapyrusArray<TESForm*>, "writeToFormPArray", ARGNAMES "None", "");` |
| — | 324 | `//REGISTERF(writeToPapyrusArray<bool>, "writeToBooleanPArray", ARGNAMES, "");` |
| `writeToStringPArray` | 325 | `REGISTERF(writeToPapyrusArray<skse::string_ref>, "writeToStringPArray", ARGNAMES "\"\"", "");` |

## JMap / JFormMap / JIntMap

Source: `JContainers/src/api_3/tes_map.h` · blob `3518a0f65666b54959863d69328e084f96b3733d`

The base `tes_map_t` registrations are instantiated for **JMap**, **JFormMap**, and **JIntMap**. Key-specific extension registrations then add appropriate `nextKey` and `getNthKey` implementations for each class.

| Public name | Source line | Registration metadata |
|---|---:|---|
| `object` | 25 | `REGISTERF(tes_object::object<Cnt>, "object", "", kCommentObject);` |
| `getInt` | 32 | `REGISTERF(getItem<SInt32>, "getInt", "object key default=0", "Returns the value associated with the @key. If not, returns @default value");` |
| `getFlt` | 33 | `REGISTERF(getItem<Float32>, "getFlt", "object key default=0.0", "");` |
| `getStr` | 34 | `REGISTERF(getItem<skse::string_ref>, "getStr", "object key default=\"\"", "");` |
| `getObj` | 35 | `REGISTERF(getItem<object_base*>, "getObj", "object key default=0", "");` |
| `getForm` | 36 | `REGISTERF(getItem<form_ref>, "getForm", "object key default=None", "");` |
| `setInt` | 42 | `REGISTERF(setItem<SInt32>, "setInt", "* key value", "Inserts @key: @value pair. Replaces existing pair with the same @key");` |
| `setFlt` | 43 | `REGISTERF(setItem<Float32>, "setFlt", "* key value", "");` |
| `setStr` | 44 | `REGISTERF(setItem<const char *>, "setStr", "* key value", "");` |
| `setObj` | 45 | `REGISTERF(setItem<object_base*>, "setObj", "* key container", "");` |
| `setForm` | 46 | `REGISTERF(setItem<form_ref>, "setForm", "* key value", "");` |
| `hasKey` | 51 | `REGISTERF2(hasKey, "* key", "Returns true, if the container has @key: value pair");` |
| `valueType` | 58 | `REGISTERF2(valueType, "* key", "Returns type of the value associated with the @key.\n"VALUE_TYPE_COMMENT);` |
| `allKeys` | 75 | `REGISTERF(allKeys, "allKeys", "*", "Returns a new array containing all keys");` |
| `allKeysPArray` | 94 | `REGISTERF2(allKeysPArray, "*", "");` |
| `allValues` | 111 | `REGISTERF(allValues, "allValues", "*", "Returns a new array containing all values");` |
| `removeKey` | 119 | `REGISTERF(removeKey, "removeKey", "* key", "Removes the pair from the container where the key equals to the @key");` |
| `count` | 128 | `REGISTERF2(count, "*", "Returns count of pairs in the conainer");` |
| `clear` | 137 | `REGISTERF2(clear, "*", "Removes all pairs from the container");` |
| `addPairs` | 156 | `REGISTERF2(addPairs, "* source overrideDuplicates", "Inserts key-value pairs from the source container");` |
| `nextKey` | 221 | `REGISTERF(nextKey<skse::string_ref>, "nextKey", STR(* previousKey="" endKey=""), tes_map_nextKey_comment);` |
| `getNthKey` | 231 | `REGISTERF(getNthKey<skse::string_ref>, "getNthKey", "* keyIndex", getNthKey_comment());` |
| `nextKey` | 236 | `REGISTERF(tes_form_map_ext::nextKey, "nextKey", STR(* previousKey=None endKey=None), tes_map_nextKey_comment);` |
| `getNthKey` | 237 | `REGISTERF(tes_form_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |
| `nextKey` | 258 | `REGISTERF(tes_integer_map::nextKey, "nextKey", STR(* previousKey=0 endKey=0), tes_map_nextKey_comment);` |
| `getNthKey` | 259 | `REGISTERF(tes_integer_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |

## JValue

Source: `JContainers/src/api_3/tes_object.h` · blob `168910972c2779a36a308a4308062928f42a18af`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `retain` | 32 | `REGISTERF2(retain, "* tag=\"\"", R"===(--- Lifetime management functionality. Read this https://github.com/SilverIce/JContainers/wiki/Lifetime-Management before using any of lifetime management functions Retains and returns the object.)===" );` |
| `release` | 51 | `REGISTERF2(release, "*", "Releases the object and returns zero, so you can release and nullify with one line of code: object = JValue.release(object)");` |
| `releaseAndRetain` | 64 | `REGISTERF2(releaseAndRetain, "previousObject newObject tag=\"\"", "Just a union of retain-release calls. Releases @previousObject, retains and returns @newObject.");` |
| `releaseObjectsWithTag` | 82 | `REGISTERF2(releaseObjectsWithTag, "tag", "For cleanup purposes only - releases all objects tagged with the @tag.\n" "Internally invokes JValue.release on the objects the same amount of times the objects were retained.");` |
| `zeroLifetime` | 92 | `REGISTERF2(zeroLifetime, "*", "Minimizes the time JC temporarily owns the object, returns the object.\n\ By using this function you help JC to delete unused objects as soon as possible.\n\ Has zero effect if the object is being retained or if another object contains/references it.");` |
| `addToPool` | 122 | `REGISTERF2(addToPool, "* poolName", "Handly for temporary objects (objects with no owners) - the pool 'locationName' owns any amount of objects, preventing their destuction, extends lifetime.\n\ Do not forget to clean the pool later! Typical use:\n\ int jTempMap = JValue.addToPool(JMap.object(), \"uniquePoolName\")\n\ int jKeys = JValue.addToPool(JMap.allKeys(someJMap), \"uniquePoolName\")\n\ and anywhere later:\n\ JValue.cleanPool(\"uniquePoolName\")" );` |
| `cleanPool` | 139 | `REGISTERF2(cleanPool, "poolName", nullptr);` |
| `shallowCopy` | 144 | `REGISTERF2(shallowCopy, "*", "--- Mics. functionality\n\nReturns shallow copy (won't copy child objects)");` |
| `deepCopy` | 149 | `REGISTERF2(deepCopy, "*", "Returns deep copy");` |
| `isExists` | 154 | `REGISTERF2(isExists, "*", "Tests whether given object identifier points to existing object");` |
| `isArray` | 160 | `REGISTERF(isCast<array>, "isArray", "*", "Returns true if the object is map, array or formmap container");` |
| `isMap` | 161 | `REGISTERF(isCast<map>, "isMap", "*", nullptr);` |
| `isFormMap` | 162 | `REGISTERF(isCast<form_map>, "isFormMap", "*", nullptr);` |
| `isIntegerMap` | 163 | `REGISTERF(isCast<integer_map>, "isIntegerMap", "*", nullptr);` |
| `empty` | 168 | `REGISTERF2(empty, "*", "Returns true, if the container is empty");` |
| `count` | 173 | `REGISTERF2(count, "*", "Returns amount of items in the container");` |
| `clear` | 180 | `REGISTERF2(clear, "*", "Removes all items from the container");` |
| `readFromFile` | 186 | `REGISTERF2(readFromFile, "filePath", "JSON serialization/deserialization:\n\nCreates and returns a new container object containing contents of JSON file");` |
| `readFromDirectory` | 225 | `REGISTERF2(readFromDirectory, "directoryPath extension=\"\"", "Parses JSON files in a directory (non recursive) and returns JMap containing {filename, container-object} pairs.\n" "Note: by default it does not filter files by extension and will try to parse everything");` |
| `objectFromPrototype` | 233 | `REGISTERF2(objectFromPrototype, "prototype", "Creates a new container object using given JSON string-prototype");` |
| `writeToFile` | 253 | `REGISTERF(writeToFile, "writeToFile", "* filePath", "Writes the object into JSON file");` |
| `hasPath` | 270 | `REGISTERF(hasPath, "hasPath", "* path", "Path resolving:\n\n\ Returns true, if it's possible to resolve given path, i.e. if it's possible to retrieve the value at the path.\n\ For ex. JValue.hasPath(container, \".player.health\") will test whether @container structure close to this one - {'player': {'health': health_value}}" );` |
| `solvedValueType` | 276 | `REGISTERF(solvedValueType, "solvedValueType", "* path", "Returns type of resolved value. "VALUE_TYPE_COMMENT);` |
| `solveFlt` | 291 | `REGISTERF(resolveGetter<Float32>, "solveFlt", "* path default=0.0", "Attempts to retrieve value at given path. If fails, returns @default value");` |
| `solveInt` | 292 | `REGISTERF(resolveGetter<SInt32>, "solveInt", "* path default=0", nullptr);` |
| `solveStr` | 293 | `REGISTERF(resolveGetter<skse::string_ref>, "solveStr", "* path default=\"\"", nullptr);` |
| `solveObj` | 294 | `REGISTERF(resolveGetter<Handle>, "solveObj", "* path default=0", nullptr);` |
| `solveForm` | 295 | `REGISTERF(resolveGetter<form_ref>, "solveForm", "* path default=None", nullptr);` |
| `solveFltSetter` | 305 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "* path value createMissingKeys=false", "Attempts to assign the value. If @createMissingKeys is False it may fail to assign - if no such path exist.\n" "With 'createMissingKeys=true' it creates any missing path element: solveIntSetter(map, \".keyA.keyB\", 10, true) on empty JMap creates {keyA: {keyB: 10}} structure" );` |
| `solveIntSetter` | 309 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "* path value createMissingKeys=false", nullptr);` |
| `solveStrSetter` | 310 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "* path value createMissingKeys=false", nullptr);` |
| `solveObjSetter` | 311 | `REGISTERF(solveSetter<ref>, "solveObjSetter", "* path value createMissingKeys=false", nullptr);` |
| `solveFormSetter` | 312 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "* path value createMissingKeys=false", nullptr);` |
| `evalLuaFlt` | 356 | `REGISTERF(evalLua<Float32>, "evalLuaFlt", "* luaCode default=0.0", "Evaluates piece of lua code. Lua support is experimental");` |
| `evalLuaInt` | 357 | `REGISTERF(evalLua<SInt32>, "evalLuaInt", "* luaCode default=0", nullptr);` |
| `evalLuaStr` | 358 | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", "* luaCode default=\"\"", nullptr);` |
| `evalLuaObj` | 359 | `REGISTERF(evalLua<Handle>, "evalLuaObj", "* luaCode default=0", nullptr);` |
| `evalLuaForm` | 360 | `REGISTERF(evalLua<form_ref>, "evalLuaForm", "* luaCode default=None", nullptr);` |

## JDB

Source: `JContainers/src/api_3/tes_db.h` · blob `2ee5ce5955b30c8552c6ecc686684c1d3de88d9c`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `solveFlt` | 20 | `REGISTERF(solveGetter<Float32>, "solveFlt", "path default=0.0", "Attempts to retrieve the value associated with the @path.\n\ For ex. the following information associated with 'frosfall' key:\n\ \n\ \"frostfall\" : {\n\ \"exposureRate\" : 0.5,\n\ \"arrayC\" : [\"stringValue\", 1.5, 10, 1.14]\n\ }\n\ \n\ then JDB.solveFlt(\".frostfall.exposureRate\") will return 0.5 and\n\ JDB.solveObj(\".frostfall.arrayC\") will return the array containing [\"stringValue\", 1.5, 10, 1.14] values");` |
| `solveInt` | 32 | `REGISTERF(solveGetter<SInt32>, "solveInt", "path default=0", nullptr);` |
| `solveStr` | 33 | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "path default=\"\"", nullptr);` |
| `solveObj` | 34 | `REGISTERF(solveGetter<object_base*>, "solveObj", "path default=0", nullptr);` |
| `solveForm` | 35 | `REGISTERF(solveGetter<form_ref>, "solveForm", "path default=None", nullptr);` |
| `solveFltSetter` | 41 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "path value createMissingKeys=false", "Attempts to assign the @value. Returns false if no such path.\n" "If 'createMissingKeys=true' it creates any missing path elements: JDB.solveIntSetter(\".frostfall.keyB\", 10, true) creates {frostfall: {keyB: 10}} structure");` |
| `solveIntSetter` | 44 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "path value createMissingKeys=false", nullptr);` |
| `solveStrSetter` | 45 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "path value createMissingKeys=false", nullptr);` |
| `solveObjSetter` | 46 | `REGISTERF(solveSetter<object_base*>, "solveObjSetter", "path value createMissingKeys=false", nullptr);` |
| `solveFormSetter` | 47 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "path value createMissingKeys=false", nullptr);` |
| `setObj` | 59 | `REGISTERF(setObj, "setObj", "key object", "Associates(and replaces previous association) container object with a string key.\n\ destroys association if object is zero\n\ for ex. JDB.setObj(\"frostfall\", frostFallInformation) will associate 'frostall' key and frostFallInformation so you can access it later" );` |
| `hasPath` | 68 | `REGISTERF2(hasPath, "path", "Returns true, if JDB capable resolve given @path, i.e. if it able to execute solve* or solver*Setter functions successfully");` |
| `allKeys` | 73 | `REGISTERF2(allKeys, "*", "returns new array containing all JDB keys");` |
| `allValues` | 78 | `REGISTERF2(allValues, "*", "returns new array containing all containers associated with JDB");` |
| `writeToFile` | 83 | `REGISTERF2(writeToFile, "path", "writes storage data into JSON file at given path");` |
| `readFromFile` | 87 | `REGISTERF2(readFromFile, "path", "DEPRECATED. Reads information from a JSON file at given path and replaces JDB content with the file content");` |

## JFormDB

Source: `JContainers/src/api_3/tes_form_db.h` · blob `8ff16cbb7f834392e1939fcc302048a12959f8e9`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `setEntry` | 103 | `REGISTERF2(setEntry, "storageName fKey entry", "associates given form key and entry (container). set entry to zero to destroy association");` |
| `makeEntry` | 119 | `REGISTERF(makeMapEntry, "makeEntry", "storageName fKey", "returns (or creates new if not found) JMap entry for given storage and form");` |
| `findEntry` | 126 | `REGISTERF2(findEntry, "storageName fKey", "search for entry for given storage and form");` |
| `solveFlt` | 139 | `REGISTERF(solveGetter<Float32>, "solveFlt", "fKey path default=0.0", "attempts to get value associated with path.");` |
| `solveInt` | 140 | `REGISTERF(solveGetter<SInt32>, "solveInt", "fKey path default=0", nullptr);` |
| `solveStr` | 141 | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "fKey path default=\"\"", nullptr);` |
| `solveObj` | 142 | `REGISTERF(solveGetter<Handle>, "solveObj", "fKey path default=0", nullptr);` |
| `solveForm` | 143 | `REGISTERF(solveGetter<form_ref>, "solveForm", "fKey path default=None", nullptr);` |
| `solveFltSetter` | 150 | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "fKey path value createMissingKeys=false", "Attempts to assign value. Returns false if no such path\n" "With 'createMissingKeys=true' it creates any missing path elements: JFormDB.solveIntSetter(formKey, \".frostfall.keyB\", 10, true) creates {frostfall: {keyB: 10}} structure");` |
| `solveIntSetter` | 153 | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "fKey path value createMissingKeys=false", nullptr);` |
| `solveStrSetter` | 154 | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "fKey path value createMissingKeys=false", nullptr);` |
| `solveObjSetter` | 155 | `REGISTERF(solveSetter<object_stack_ref&>, "solveObjSetter", "fKey path value createMissingKeys=false", nullptr);` |
| `solveFormSetter` | 156 | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "fKey path value createMissingKeys=false", nullptr);` |
| `hasPath` | 162 | `REGISTERF2(hasPath, "fKey path", "returns true, if capable resolve given path, e.g. it able to execute solve* or solver*Setter functions successfully");` |
| `allKeys` | 170 | `REGISTERF2(allKeys, "fKey key", "JMap-like interface functions:\n" "\n" "returns new array containing all keys");` |
| `allValues` | 179 | `REGISTERF2(allValues, "fKey key", "returns new array containing all values");` |
| `getInt` | 187 | `REGISTERF(getItem<SInt32>, "getInt", "fKey key", "returns value associated with key");` |
| `getFlt` | 188 | `REGISTERF(getItem<Float32>, "getFlt", "fKey key", "");` |
| `getStr` | 189 | `REGISTERF(getItem<skse::string_ref>, "getStr", "fKey key", "");` |
| `getObj` | 190 | `REGISTERF(getItem<object_base *>, "getObj", "fKey key", "");` |
| `getForm` | 191 | `REGISTERF(getItem<form_ref>, "getForm", "fKey key", "");` |
| `setInt` | 198 | `REGISTERF(setItem<SInt32>, "setInt", "fKey key value", "creates key-value association. replaces existing value if any");` |
| `setFlt` | 199 | `REGISTERF(setItem<Float32>, "setFlt", "fKey key value", "");` |
| `setStr` | 200 | `REGISTERF(setItem<const char *>, "setStr", "fKey key value", "");` |
| `setObj` | 201 | `REGISTERF(setItem<object_stack_ref&>, "setObj", "fKey key container", "");` |
| `setForm` | 202 | `REGISTERF(setItem<form_ref>, "setForm", "fKey key value", "");` |

## Semantic class map

### JValue
Common object/container functionality: lifetime retain/release, pools, copy, type tests, JSON read/write, path resolution, typed path getters/setters, and Lua evaluation helpers.

### JArray
Ordered heterogeneous container. Current registration metadata includes constructors, typed getters/setters/search/add operations, slicing/insertion, count/clear/erase, sort/unique, value-type queries and Papyrus-array export.

### JMap
String-keyed associative container.

### JFormMap
Form-keyed associative container. Iteration deliberately skips unloaded/None form keys at the Papyrus layer in its specialized next-key implementation.

### JIntMap
Integer-keyed associative container.

### JDB
Global persistent JContainers database/root map with path-solving and JSON persistence operations.

### JFormDB
Form-associated database/storage abstraction layered over JContainers maps.

## Provenance and compatibility rules

1. Treat this current C++ registration metadata as stronger evidence for the current generated Papyrus surface than old 3.3-era release PSCs.
2. Do not infer exact Papyrus return types from a registration statement unless the reflection type metadata is also resolved.
3. Public function names are trustworthy when explicitly quoted or produced by simple `REGISTERF2` name stringification.
4. JMap/JFormMap/JIntMap share generic map operations but differ in key type and iteration behavior.
5. JContainers object handles are framework-managed identities; they are not Skyrim FormIDs.
6. Retain/release/lifetime rules remain part of API correctness even when a container is reachable from another object.
7. Future source diffs should compare registration names, argument metadata, class names and API-version metadata.
