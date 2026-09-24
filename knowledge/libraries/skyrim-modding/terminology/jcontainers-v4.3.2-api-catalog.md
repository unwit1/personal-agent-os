# JContainers v4.3.2 — Papyrus Reflection API Catalog

Imported: 2026-09-24
Source: `ryobg/JContainers` tag `v4.3.2`
Status: source-derived native registration catalog

## Architecture

JContainers does not keep its primary Papyrus API as ordinary PSC source files. Its v4.3.2 runtime builds Papyrus native functions from reflection metadata in the `api_3` headers. `master.h` includes nine API modules.

The binding layer converts C++ types to Papyrus types, creates SKSE native functions, and registers them dynamically. JContainers marks registered functions `NoWait`.

## Provider files

| Source | Exposed class names | Blob SHA | Registration macro rows |
|---|---|---|---:|
| `src/JContainers/src/api_3/tes_object.h` | `JValue` | `9356b382241029b7de1102821a74a4d1e79b64b9` | 40 |
| `src/JContainers/src/api_3/tes_atomic.h` | `JAtomic` | `c8e3f860e353d3f8de93c333df97b176a28b8f03` | 10 |
| `src/JContainers/src/api_3/tes_array.h` | `JArray` | `10cc1925ef62dec8c38dbf2185a3aef61de8e09e` | 57 |
| `src/JContainers/src/api_3/tes_map.h` | `JMap`, `JFormMap`, `JIntMap` | `80fac0e009b1f165ad73a2d6a8aa4b823bf9b5cb` | 31 |
| `src/JContainers/src/api_3/tes_db.h` | `JDB` | `223d5c69c70ca3800ce3a5c2761f11ff8c7eb0c9` | 16 |
| `src/JContainers/src/api_3/tes_jcontainers.h` | `JContainers` | `350c044787fb0871267e7437c8a86c866a9df589` | 13 |
| `src/JContainers/src/api_3/tes_string.h` | `JString` | `455405de82d33e7251e941c3df40137df7f7db3e` | 7 |
| `src/JContainers/src/api_3/tes_form_db.h` | `JFormDB` | `7a1454ac081d416d0563325c9f7706b7703238a3` | 26 |
| `src/JContainers/src/api_3/tes_lua.h` | `JLua` | `3834c1d3fc2be58f0e5ac10119a29dea6a263f10` | 10 |

## Registration inventory

### JValue

Source: `src/JContainers/src/api_3/tes_object.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 40 | `enableAPILog` | `REGISTERF (enable_api_log, "enableAPILog", "*", "Most call entries made to JC will be logged. Heavy traffic, by default is disabled.\n" "Not thread safe for multiple users (though harmless).");` |
| 56 | `retain` | `REGISTERF2(retain, "* tag=\"\"", R"===(--- Lifetime management functionality. Read this https://github.com/ryobg/JContainers/wiki/Lifetime-Management before using any of lifetime management functions  Retains and returns the object.)===" );` |
| 77 | `release` | `REGISTERF2(release, "*", "Releases the object and returns zero, so you can release and nullify with one line of code: object = JValue.release(object)");` |
| 92 | `releaseAndRetain` | `REGISTERF2(releaseAndRetain, "previousObject newObject tag=\"\"", "Just a union of retain-release calls. Releases @previousObject, retains and returns @newObject.");` |
| 111 | `releaseObjectsWithTag` | `REGISTERF2(releaseObjectsWithTag, "tag", "Releases all objects tagged with @tag.\n" "Internally invokes JValue.release on each object same amount of times it has been retained.");` |
| 122 | `zeroLifetime` | `REGISTERF2(zeroLifetime, "*", "Minimizes the time JC temporarily owns the object, returns the object.\n\ By using this function you help JC to delete unused objects as soon as possible.\n\ Has zero effect if the object is being retained or if another object contains/references it.");` |
| 154 | `addToPool` | `REGISTERF2(addToPool, "* poolName", "Handly for temporary objects (objects with no owners) - the pool 'locationName' owns any amount of objects, preventing their destuction, extends lifetime.\n\ Do not forget to clean the pool later! Typical use:\n\ int jTempMap = JValue.addToPool(JMap.object(), \"uniquePoolName\")\n\ int jKeys = JValue.addToPool(JMap.allKeys(someJMap), \"uniquePoolName\")\n\ and anywhere later:\n\ JValue.cleanPool(\"uniquePoolName\")" );` |
| 174 | `cleanPool` | `REGISTERF2(cleanPool, "poolName", nullptr);` |
| 185 | `shallowCopy` | `REGISTERF2(shallowCopy, "*", "--- Mics. functionality\n\nReturns shallow copy (won't copy child objects)");` |
| 196 | `deepCopy` | `REGISTERF2(deepCopy, "*", "Returns deep copy");` |
| 202 | `isExists` | `REGISTERF2(isExists, "*", "Tests whether given object identifier is not the null object.\n" "Note that many other API functions already check that too.");` |
| 211 | `isArray` | `REGISTERF(isCast<array>, "isArray", "*", "Returns true if the object is map, array or formmap container");` |
| 212 | `isMap` | `REGISTERF(isCast<map>, "isMap", "*", nullptr);` |
| 213 | `isFormMap` | `REGISTERF(isCast<form_map>, "isFormMap", "*", nullptr);` |
| 214 | `isIntegerMap` | `REGISTERF(isCast<integer_map>, "isIntegerMap", "*", nullptr);` |
| 221 | `empty` | `REGISTERF2(empty, "*", "Returns true, if the container is empty");` |
| 232 | `count` | `REGISTERF2(count, "*", "Returns amount of items in the container");` |
| 240 | `clear` | `REGISTERF2(clear, "*", "Removes all items from the container");` |
| 247 | `readFromFile` | `REGISTERF2(readFromFile, "filePath", "JSON serialization/deserialization:\n\nCreates and returns a new container object containing contents of JSON file");` |
| 286 | `readFromDirectory` | `REGISTERF2(readFromDirectory, "directoryPath extension=\"\"", "Parses JSON files in a directory (non recursive) and returns JMap containing {filename, container-object} pairs.\n" "Note: by default it does not filter files by extension and will try to parse everything");` |
| 295 | `objectFromPrototype` | `REGISTERF2(objectFromPrototype, "prototype", "Creates a new container object using given JSON string-prototype");` |
| 316 | `writeToFile` | `REGISTERF(writeToFile, "writeToFile", "* filePath", "Writes the object into JSON file");` |
| 338 | `toJsonString` | `REGISTERF (toJsonString, "toJsonString", "*", "Serializes the object into JSON string and returns it");` |
| 354 | `solvedValueType` | `REGISTERF(solvedValueType, "solvedValueType", "* path", "Returns type of resolved value. " VALUE_TYPE_COMMENT);` |
| 362 | `hasPath` | `REGISTERF(hasPath, "hasPath", "* path", "Path resolving:\n\n\ Returns true, if it's possible to resolve given path, i.e. if it's possible to retrieve the value at the path.\n\ For ex. JValue.hasPath(container, \".player.health\") will test whether @container structure close to this one - {'player': {'health': health_value}}" );` |
| 384 | `solveFlt` | `REGISTERF(resolveGetter<Float32>, "solveFlt", "* path default=0.0", "Attempts to retrieve value at given path. If fails, returns @default value");` |
| 385 | `solveInt` | `REGISTERF(resolveGetter<SInt32>, "solveInt", "* path default=0", nullptr);` |
| 386 | `solveStr` | `REGISTERF(resolveGetter<skse::string_ref>, "solveStr", "* path default=\"\"", nullptr);` |
| 387 | `solveObj` | `REGISTERF(resolveGetter<Handle>, "solveObj", "* path default=0", nullptr);` |
| 388 | `solveForm` | `REGISTERF(resolveGetter<form_ref>, "solveForm", "* path default=None", nullptr);` |
| 400 | `solveFltSetter` | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "* path value createMissingKeys=false", "Attempts to assign the value. If @createMissingKeys is False it may fail to assign - if no such path exist.\n" "With 'createMissingKeys=true' it creates any missing path element: solveIntSetter(map, \".keyA.keyB\", 10, true) on empty JMap creates {keyA: {keyB: 10}} structure" );` |
| 404 | `solveIntSetter` | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "* path value createMissingKeys=false", nullptr);` |
| 405 | `solveStrSetter` | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "* path value createMissingKeys=false", nullptr);` |
| 406 | `solveObjSetter` | `REGISTERF(solveSetter<ref>, "solveObjSetter", "* path value createMissingKeys=false", nullptr);` |
| 407 | `solveFormSetter` | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "* path value createMissingKeys=false", nullptr);` |
| 452 | `evalLuaFlt` | `REGISTERF(evalLua<Float32>, "evalLuaFlt", "* luaCode default=0.0", "Evaluates piece of lua code. Lua support is experimental");` |
| 453 | `evalLuaInt` | `REGISTERF(evalLua<SInt32>, "evalLuaInt", "* luaCode default=0", nullptr);` |
| 454 | `evalLuaStr` | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", "* luaCode default=\"\"", nullptr);` |
| 455 | `evalLuaObj` | `REGISTERF(evalLua<Handle>, "evalLuaObj", "* luaCode default=0", nullptr);` |
| 456 | `evalLuaForm` | `REGISTERF(evalLua<form_ref>, "evalLuaForm", "* luaCode default=None", nullptr);` |

### JAtomic

Source: `src/JContainers/src/api_3/tes_atomic.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 146 | `exchangeInt` | `REGISTERF(exchange<SInt32>, "exchangeInt", PARAMS_INT "0", "Exchanges the value at the @path with the @value. Returns previous value.");` |
| 149 | `exchangeFlt` | `REGISTERF(exchange<Float32>, "exchangeFlt", PARAMS_INT "0.0", nullptr);` |
| 150 | `exchangeStr` | `REGISTERF(exchange<std::string>, "exchangeStr", PARAMS_INT "\"\"", nullptr);` |
| 152 | `exchangeForm` | `REGISTERF(exchange<form_ref>, "exchangeForm", PARAMS_INT "None", nullptr);` |
| 153 | `exchangeObj` | `REGISTERF(exchange<object_base*>, "exchangeObj", PARAMS_INT "0", nullptr);` |
| 157 | `compareExchangeInt` | `REGISTERF(compareExchange<SInt32>, "compareExchangeInt", PARAMS_INT "0", "Compares the value at the @path with the @expected and, if they are equal, exchanges the value at the @path with the @desired values.\nReturns previous value.");` |
| 160 | `compareExchangeFlt` | `REGISTERF(compareExchange<Float32>, "compareExchangeFlt", PARAMS_INT "0.0", nullptr);` |
| 161 | `compareExchangeStr` | `REGISTERF(compareExchange<std::string>, "compareExchangeStr", PARAMS_INT "\"\"", nullptr);` |
| 163 | `compareExchangeForm` | `REGISTERF(compareExchange<form_ref>, "compareExchangeForm", PARAMS_INT "None", nullptr);` |
| 164 | `compareExchangeObj` | `REGISTERF(compareExchange<object_base*>, "compareExchangeObj", PARAMS_INT "0", nullptr);` |

### JArray

Source: `src/JContainers/src/api_3/tes_array.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 42 | `object` | `REGISTERF(tes_object::object<array>, "object", "", kCommentObject);` |
| 59 | `objectWithSize` | `REGISTERF2(objectWithSize, "size", "Creates a new array of given size, filled with empty (None) items");` |
| 78 | `objectWithInts` | `REGISTERF(fromArray<SInt32>, "objectWithInts", "values", "Creates a new array that contains given values\n\ objectWithBooleans converts booleans into integers");` |
| 81 | `objectWithStrings` | `REGISTERF(fromArray<skse::string_ref>, "objectWithStrings",  "values", nullptr);` |
| 82 | `objectWithFloats` | `REGISTERF(fromArray<Float32>, "objectWithFloats",  "values", nullptr);` |
| 83 | `objectWithBooleans` | `REGISTERF(fromArray<bool>, "objectWithBooleans",  "values", nullptr);` |
| 107 | `subArray` | `REGISTERF2(subArray, "* startIndex endIndex", "Creates a new array containing all the values from the source array in range [startIndex, endIndex)");` |
| 123 | `addFromArray` | `REGISTERF2(addFromArray, "* source insertAtIndex=-1", "Inserts the values from the source array into this array. If insertAtIndex is -1 (default behaviour) it appends to the end.\n" NEGATIVE_IDX_COMMENT);` |
| 153 | `addFromFormList` | `REGISTERF2(addFromFormList, "* source insertAtIndex=-1", nullptr);` |
| 166 | `getInt` | `REGISTERF(itemAtIndex<SInt32>, "getInt", "* index default=0", "Returns the item at the index of the array.\n" NEGATIVE_IDX_COMMENT);` |
| 168 | `getFlt` | `REGISTERF(itemAtIndex<Float32>, "getFlt", "* index default=0.0", "");` |
| 169 | `getStr` | `REGISTERF(itemAtIndex<skse::string_ref>, "getStr", "* index default=\"\"", "");` |
| 170 | `getObj` | `REGISTERF(itemAtIndex<object_base*>, "getObj", "* index default=0", "");` |
| 171 | `getForm` | `REGISTERF(itemAtIndex<form_ref>, "getForm", "* index default=None", "");` |
| 192 | `asIntArray` | `REGISTERF (all_items<VMResultArray<SInt32>>,           "asIntArray",    "*", "Copy all items to new native Papyrus array of dynamic size.\n" "Items not matching the requested type will have default\n" "values as the ones from the getInt/Flt/Str/Form functions.");` |
| 196 | `asFloatArray` | `REGISTERF (all_items<VMResultArray<Float32>>,          "asFloatArray",  "*", "");` |
| 197 | `asStringArray` | `REGISTERF (all_items<VMResultArray<skse::string_ref>>, "asStringArray", "*", "");` |
| 198 | `asFormArray` | `REGISTERF (all_items<VMResultArray<TESForm*>>,         "asFormArray",   "*", "");` |
| 219 | `findInt` | `REGISTERF(findVal<SInt32>, "findInt", "* value searchStartIndex=0", "Returns the index of the first found value/container that equals to given the value/container (default behaviour if searchStartIndex is 0).\n\ If nothing was found it returns -1.\n\ @searchStartIndex - index of the array where to start search\n" NEGATIVE_IDX_COMMENT);` |
| 224 | `findFlt` | `REGISTERF(findVal<Float32>, "findFlt", "* value searchStartIndex=0", "");` |
| 225 | `findStr` | `REGISTERF(findVal<const char *>, "findStr", "* value searchStartIndex=0", "");` |
| 226 | `findObj` | `REGISTERF(findVal<object_base*>, "findObj", "* container searchStartIndex=0", "");` |
| 227 | `findForm` | `REGISTERF(findVal<form_ref>, "findForm", "* value searchStartIndex=0", "");` |
| 243 | `countInteger` | `REGISTERF (count_item<SInt32>, "countInteger", "* value", "Returns the number of times given value was found in a JArray.");` |
| 244 | `countFloat` | `REGISTERF (count_item<Float32>, "countFloat", "* value", "");` |
| 245 | `countString` | `REGISTERF (count_item<const char *>, "countString", "* value", "");` |
| 246 | `countObject` | `REGISTERF (count_item<object_base*>, "countObject", "* container", "");` |
| 247 | `countForm` | `REGISTERF (count_item<form_ref>, "countForm", "* value", "");` |
| 258 | `setInt` | `REGISTERF(replaceItemAtIndex<SInt32>, "setInt", "* index value", "Replaces existing value at the @index of the array with the new @value.\n" NEGATIVE_IDX_COMMENT);` |
| 260 | `setFlt` | `REGISTERF(replaceItemAtIndex<Float32>, "setFlt", "* index value", "");` |
| 261 | `setStr` | `REGISTERF(replaceItemAtIndex<const char *>, "setStr", "* index value", "");` |
| 262 | `setObj` | `REGISTERF(replaceItemAtIndex<object_base*>, "setObj", "* index container", "");` |
| 263 | `setForm` | `REGISTERF(replaceItemAtIndex<form_ref>, "setForm", "* index value", "");` |
| 274 | `addInt` | `REGISTERF(addItemAt<SInt32>, "addInt", "* value addToIndex=-1", "Appends the @value/@container to the end of the array.\n\ If @addToIndex >= 0 it inserts value at given index. " NEGATIVE_IDX_COMMENT);` |
| 276 | `addFlt` | `REGISTERF(addItemAt<Float32>, "addFlt", "* value addToIndex=-1", "");` |
| 277 | `addStr` | `REGISTERF(addItemAt<const char *>, "addStr", "* value addToIndex=-1", "");` |
| 278 | `addObj` | `REGISTERF(addItemAt<object_base*>, "addObj", "* container addToIndex=-1", "");` |
| 279 | `addForm` | `REGISTERF(addItemAt<form_ref>, "addForm", "* value addToIndex=-1", "");` |
| 285 | `count` | `REGISTERF2(count, "*", "Returns count of the items in the array");` |
| 291 | `clear` | `REGISTERF2(clear, "*", "Removes all the items from the array");` |
| 301 | `eraseIndex` | `REGISTERF2(eraseIndex, "* index", "Erases the item at the index. "NEGATIVE_IDX_COMMENT);` |
| 318 | `eraseRange` | `REGISTERF2(eraseRange, "* first last", "Erases [first, last] index range of the items. "NEGATIVE_IDX_COMMENT "\nFor ex. with [1,-1] range it will erase everything except the first item");` |
| 336 | `eraseInteger` | `REGISTERF (erase_item<SInt32>, "eraseInteger", "* value", "Erase all elements of given value. Returns the number of erased elements.");` |
| 337 | `eraseFloat` | `REGISTERF (erase_item<Float32>, "eraseFloat", "* value", "");` |
| 338 | `eraseString` | `REGISTERF (erase_item<const char *>, "eraseString", "* value", "");` |
| 339 | `eraseObject` | `REGISTERF (erase_item<object_base*>, "eraseObject", "* container", "");` |
| 340 | `eraseForm` | `REGISTERF (erase_item<form_ref>, "eraseForm", "* value", "");` |
| 353 | `valueType` | `REGISTERF2(valueType, "* index", "Returns type of the value at the @index. "NEGATIVE_IDX_COMMENT"\n"VALUE_TYPE_COMMENT);` |
| 367 | `swapItems` | `REGISTERF2(swapItems, "* index1 index2", "Exchanges the items at @index1 and @index2. "NEGATIVE_IDX_COMMENT);` |
| 379 | `sort` | `REGISTERF2(sort, "*", "Sorts the items into ascending order (none < int < float < form < object < string). Returns the array itself");` |
| 393 | `unique` | `REGISTERF2(unique, "*", "Sorts the items, removes duplicates. Returns array itself. You can treat it as JSet now");` |
| 405 | `reverse` | `REGISTERF2 (reverse, "*", "Reverse the order of elements. Returns the array itself.");` |
| 464 | `writeToIntegerPArray` | `REGISTERF(writeToPapyrusArray<SInt32>, "writeToIntegerPArray", ARGNAMES "0", "Writes the array's items into the @targetArray array starting at @destIndex\n\ @writeAtIdx - \ [-1, 0] - writes all the items in reverse order\n\ [0, -1] - writes all the items in straight order\n\ [1, 3] - writes 3 items in straight order" );` |
| 471 | `writeToFloatPArray` | `REGISTERF(writeToPapyrusArray<Float32>, "writeToFloatPArray", ARGNAMES "0.0", "");` |
| 472 | `writeToFormPArray` | `REGISTERF(writeToPapyrusArray<form_ref>, "writeToFormPArray", ARGNAMES "None", "");` |
| 473 | `writeToBooleanPArray` | `//REGISTERF(writeToPapyrusArray<bool>, "writeToBooleanPArray", ARGNAMES, "");` |
| 474 | `writeToStringPArray` | `REGISTERF(writeToPapyrusArray<std::string>, "writeToStringPArray", ARGNAMES "\"\"", "");` |

### JMap / JFormMap / JIntMap

Source: `src/JContainers/src/api_3/tes_map.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 29 | `object` | `REGISTERF(tes_object::object<Cnt>, "object", "", kCommentObject);` |
| 37 | `getInt` | `REGISTERF(getItem<SInt32>, "getInt", "object key default=0", "Returns the value associated with the @key. If not, returns @default value");` |
| 38 | `getFlt` | `REGISTERF(getItem<Float32>, "getFlt", "object key default=0.0", "");` |
| 39 | `getStr` | `REGISTERF(getItem<skse::string_ref>, "getStr", "object key default=\"\"", "");` |
| 40 | `getObj` | `REGISTERF(getItem<object_base*>, "getObj", "object key default=0", "");` |
| 41 | `getForm` | `REGISTERF(getItem<form_ref>, "getForm", "object key default=None", "");` |
| 48 | `setInt` | `REGISTERF(setItem<SInt32>, "setInt", "* key value", "Inserts @key: @value pair. Replaces existing pair with the same @key");` |
| 49 | `setFlt` | `REGISTERF(setItem<Float32>, "setFlt", "* key value", "");` |
| 50 | `setStr` | `REGISTERF(setItem<const char *>, "setStr", "* key value", "");` |
| 51 | `setObj` | `REGISTERF(setItem<object_base*>, "setObj", "* key container", "");` |
| 52 | `setForm` | `REGISTERF(setItem<form_ref>, "setForm", "* key value", "");` |
| 70 | `insertInt` | `REGISTERF (insertItem<SInt32>, "insertInt", "* key value", "Inserts @key: @value pair. Does nothing if the @key already exists");` |
| 71 | `insertFlt` | `REGISTERF (insertItem<Float32>, "insertFlt", "* key value", "");` |
| 72 | `insertStr` | `REGISTERF (insertItem<skse::string_ref>, "insertStr", "* key value", "");` |
| 73 | `insertObj` | `REGISTERF (insertItem<object_base*>, "insertObj", "* key container", "");` |
| 74 | `insertForm` | `REGISTERF (insertItem<form_ref>, "insertForm", "* key value", "");` |
| 80 | `hasKey` | `REGISTERF2(hasKey, "* key", "Returns true, if the container has @key: value pair");` |
| 88 | `valueType` | `REGISTERF2(valueType, "* key", "Returns type of the value associated with the @key.\n"VALUE_TYPE_COMMENT);` |
| 108 | `allKeys` | `REGISTERF(allKeys, "allKeys", "*", "Returns a new array containing all keys");` |
| 130 | `allKeysPArray` | `REGISTERF2(allKeysPArray, "*", "");` |
| 150 | `allValues` | `REGISTERF(allValues, "allValues", "*", "Returns a new array containing all values");` |
| 161 | `removeKey` | `REGISTERF(removeKey, "removeKey", "* key", "Removes the pair from the container where the key equals to the @key");` |
| 173 | `count` | `REGISTERF2(count, "*", "Returns count of pairs in the conainer");` |
| 185 | `clear` | `REGISTERF2(clear, "*", "Removes all pairs from the container");` |
| 207 | `addPairs` | `REGISTERF2(addPairs, "* source overrideDuplicates", "Inserts key-value pairs from the source container");` |
| 272 | `nextKey` | `REGISTERF(nextKey<skse::string_ref>, "nextKey", STR(* previousKey="" endKey=""), tes_map_nextKey_comment);` |
| 282 | `getNthKey` | `REGISTERF(getNthKey<skse::string_ref>, "getNthKey", "* keyIndex", getNthKey_comment());` |
| 287 | `nextKey` | `REGISTERF(tes_form_map_ext::nextKey, "nextKey", STR(* previousKey=None endKey=None), tes_map_nextKey_comment);` |
| 288 | `getNthKey` | `REGISTERF(tes_form_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |
| 309 | `nextKey` | `REGISTERF(tes_integer_map::nextKey, "nextKey", STR(* previousKey=0 endKey=0), tes_map_nextKey_comment);` |
| 310 | `getNthKey` | `REGISTERF(tes_integer_map::getNthKey, "getNthKey", "* keyIndex", tes_map_ext::getNthKey_comment());` |

### JDB

Source: `src/JContainers/src/api_3/tes_db.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 26 | `solveFlt` | `REGISTERF(solveGetter<Float32>, "solveFlt", "path default=0.0", "Attempts to retrieve the value associated with the @path.\n\ For ex. the following information associated with 'frosfall' key:\n\ \n\ \"frostfall\" : {\n\ \"exposureRate\" : 0.5,\n\ \"arrayC\" : [\"stringValue\", 1.5, 10, 1.14]\n\ }\n\ \n\ then JDB.solveFlt(\".frostfall.exposureRate\") will return 0.5 and\n\ JDB.solveObj(\".frostfall.arrayC\") will return the array containing [\"stringValue\", 1.5, 10, 1.14] values");` |
| 38 | `solveInt` | `REGISTERF(solveGetter<SInt32>, "solveInt", "path default=0", nullptr);` |
| 39 | `solveStr` | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "path default=\"\"", nullptr);` |
| 40 | `solveObj` | `REGISTERF(solveGetter<object_base*>, "solveObj", "path default=0", nullptr);` |
| 41 | `solveForm` | `REGISTERF(solveGetter<form_ref>, "solveForm", "path default=None", nullptr);` |
| 49 | `solveFltSetter` | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "path value createMissingKeys=false", "Attempts to assign the @value. Returns false if no such path.\n" "If 'createMissingKeys=true' it creates any missing path elements: JDB.solveIntSetter(\".frostfall.keyB\", 10, true) creates {frostfall: {keyB: 10}} structure");` |
| 52 | `solveIntSetter` | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "path value createMissingKeys=false", nullptr);` |
| 53 | `solveStrSetter` | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "path value createMissingKeys=false", nullptr);` |
| 54 | `solveObjSetter` | `REGISTERF(solveSetter<object_base*>, "solveObjSetter", "path value createMissingKeys=false", nullptr);` |
| 55 | `solveFormSetter` | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "path value createMissingKeys=false", nullptr);` |
| 70 | `setObj` | `REGISTERF(setObj, "setObj", "key object", "Associates(and replaces previous association) container object with a string key.\n\ destroys association if object is zero\n\ for ex. JDB.setObj(\"frostfall\", frostFallInformation) will associate 'frostall' key and frostFallInformation so you can access it later" );` |
| 80 | `hasPath` | `REGISTERF2(hasPath, "path", "Returns true, if JDB capable resolve given @path, i.e. if it able to execute solve* or solver*Setter functions successfully");` |
| 86 | `allKeys` | `REGISTERF2(allKeys, "*", "returns new array containing all JDB keys");` |
| 92 | `allValues` | `REGISTERF2(allValues, "*", "returns new array containing all containers associated with JDB");` |
| 98 | `writeToFile` | `REGISTERF2(writeToFile, "path", "writes storage data into JSON file at given path");` |
| 104 | `root` | `REGISTERF2(root, "", "Returns underlying JDB's container - an instance of JMap.\nThe object being owned (retained) internally, so you don't have to (but can) retain or release it.") };  TES_META_INFO(tes_db);` |

### JContainers

Source: `src/JContainers/src/api_3/tes_jcontainers.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 25 | `APIVersion` | `REGISTERF2_STATELESS (APIVersion, nullptr, "JContainers uses API.Feature.Minor.Patch versioning.");` |
| 31 | `featureVersion` | `REGISTERF2_STATELESS (featureVersion, nullptr, nullptr);` |
| 37 | `minorVersion` | `REGISTERF2_STATELESS (minorVersion, nullptr, nullptr);` |
| 43 | `patchVersion` | `REGISTERF2_STATELESS (patchVersion, nullptr, nullptr);` |
| 54 | `versionInt` | `REGISTERF2_STATELESS (versionInt, nullptr, []() { std::stringstream ss; ss << "Returns the full JContainers version as a sortable integer using AABBCCDD format.\n" << "\n" << "Formula:\n" << "    api * 1000000 + feature * 10000 + minor * 100 + patch\n" << "\n" << "Example:\n" << "    4.2.13.1 => 4021301\n" << "\n" << "Current version int is " << versionInt ();` |
| 73 | `versionString` | `REGISTERF2_STATELESS (versionString, nullptr, []() { std::stringstream ss; ss << "Returns the full JContainers version string in api.feature.minor.patch format.\n" << "\n" << "Current version string is " JC_VERSION_STR; return ss.str();` |
| 86 | `versionAtLeast` | `REGISTERF2_STATELESS(versionAtLeast, "api feature minor=0 patch=0", []() { std::stringstream ss; ss << "Returns true if the installed JContainers version is at least the requested version.\n" << "\n" << "Recommended compatibility check:\n" << "    bool valid = JContainers.versionAtLeast (4, 2, 13, 1)\n" << "\n" << "This should be preferred over APIVersion() and featureVersion()."; return ss.str ();` |
| 109 | `fileExistsAtPath` | `REGISTERF2_STATELESS(fileExistsAtPath, "path", "Returns true if the file at a specified @path exists");` |
| 146 | `contentsOfDirectoryAtPath` | `REGISTERF_STATELESS( contentsOfDirectoryAtPath<VMResultArray<skse::string_ref>>, "contentsOfDirectoryAtPath", "directoryPath extension=\"\"", nullptr);` |
| 158 | `removeFileAtPath` | `REGISTERF2_STATELESS(removeFileAtPath, "path", "Deletes the file or directory identified by the @path");` |
| 182 | `userDirectory` | `REGISTERF_STATELESS(_userDirectory, "userDirectory", "", "A path to user-specific directory - " JC_USER_FILES);` |
| 187 | `__isInstalled` | `REGISTERF2_STATELESS(__isInstalled, nullptr, "For internal purposes, do not use it.");` |
| 189 | `<embedded Papyrus text>` | `REGISTER_TEXT([]() { const char fmt[] = R"===( ; Returns true if JContainers plugin installed properly bool function isInstalled() global return __isInstalled() && %u == APIVersion() && %u == featureVersion() endfunction )==="; char buff[sizeof(fmt) * 3 / 2] = { '\0' }; assert(-1 != sprintf_s(buff, fmt, consts::api_version, consts::feature_version));` |

### JString

Source: `src/JContainers/src/api_3/tes_string.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 43 | `wrap` | `REGISTERF2(wrap, "sourceText charactersPerLine=60", "Breaks source text onto set of lines of almost equal size.\n\ Returns JArray object containing lines.\n\ Accepts ASCII and UTF-8 encoded strings only");` |
| 60 | `stoul` | `REGISTERF2_STATELESS (stoul, "num_string base=16", "Converts a base string into unsigned integer");` |
| 79 | `decodeFormStringToFormId` | `REGISTERF2_STATELESS(decodeFormStringToFormId, "formString", "FormId\|Form <-> \"__formData\|<pluginName>\|<lowFormId>\"-string converisons");` |
| 80 | `decodeFormStringToForm` | `REGISTERF2_STATELESS(decodeFormStringToForm, "formString", "");` |
| 81 | `encodeFormToString` | `REGISTERF2_STATELESS(encodeFormToString, "value", "");` |
| 82 | `encodeFormIdToString` | `REGISTERF2_STATELESS(encodeFormIdToString, "formId", "");` |
| 98 | `generateUUID` | `REGISTERF2_STATELESS(generateUUID, "", "Generates random uuid-string like 2e80251a-ab22-4ad8-928c-2d1c9561270e");` |

### JFormDB

Source: `src/JContainers/src/api_3/tes_form_db.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 111 | `setEntry` | `REGISTERF2(setEntry, "storageName fKey entry", "associates given form key and entry (container). set entry to zero to destroy association");` |
| 130 | `makeEntry` | `REGISTERF(makeMapEntry, "makeEntry", "storageName fKey", "returns (or creates new if not found) JMap entry for given storage and form");` |
| 140 | `findEntry` | `REGISTERF2(findEntry, "storageName fKey", "search for entry for given storage and form");` |
| 155 | `solveFlt` | `REGISTERF(solveGetter<Float32>, "solveFlt", "fKey path default=0.0", "attempts to get value associated with path.");` |
| 156 | `solveInt` | `REGISTERF(solveGetter<SInt32>, "solveInt", "fKey path default=0", nullptr);` |
| 157 | `solveStr` | `REGISTERF(solveGetter<skse::string_ref>, "solveStr", "fKey path default=\"\"", nullptr);` |
| 158 | `solveObj` | `REGISTERF(solveGetter<Handle>, "solveObj", "fKey path default=0", nullptr);` |
| 159 | `solveForm` | `REGISTERF(solveGetter<form_ref>, "solveForm", "fKey path default=None", nullptr);` |
| 168 | `solveFltSetter` | `REGISTERF(solveSetter<Float32>, "solveFltSetter", "fKey path value createMissingKeys=false", "Attempts to assign value. Returns false if no such path\n" "With 'createMissingKeys=true' it creates any missing path elements: JFormDB.solveIntSetter(formKey, \".frostfall.keyB\", 10, true) creates {frostfall: {keyB: 10}} structure");` |
| 171 | `solveIntSetter` | `REGISTERF(solveSetter<SInt32>, "solveIntSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 172 | `solveStrSetter` | `REGISTERF(solveSetter<const char*>, "solveStrSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 173 | `solveObjSetter` | `REGISTERF(solveSetter<object_stack_ref&>, "solveObjSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 174 | `solveFormSetter` | `REGISTERF(solveSetter<form_ref>, "solveFormSetter", "fKey path value createMissingKeys=false", nullptr);` |
| 182 | `hasPath` | `REGISTERF2(hasPath, "fKey path", "returns true, if capable resolve given path, e.g. it able to execute solve* or solver*Setter functions successfully");` |
| 191 | `allKeys` | `REGISTERF2(allKeys, "fKey key", "JMap-like interface functions:\n" "\n" "returns new array containing all keys");` |
| 201 | `allValues` | `REGISTERF2(allValues, "fKey key", "returns new array containing all values");` |
| 211 | `getInt` | `REGISTERF(getItem<SInt32>, "getInt", "fKey key", "returns value associated with key");` |
| 212 | `getFlt` | `REGISTERF(getItem<Float32>, "getFlt", "fKey key", "");` |
| 213 | `getStr` | `REGISTERF(getItem<skse::string_ref>, "getStr", "fKey key", "");` |
| 214 | `getObj` | `REGISTERF(getItem<object_base *>, "getObj", "fKey key", "");` |
| 215 | `getForm` | `REGISTERF(getItem<form_ref>, "getForm", "fKey key", "");` |
| 224 | `setInt` | `REGISTERF(setItem<SInt32>, "setInt", "fKey key value", "creates key-value association. replaces existing value if any");` |
| 225 | `setFlt` | `REGISTERF(setItem<Float32>, "setFlt", "fKey key value", "");` |
| 226 | `setStr` | `REGISTERF(setItem<const char *>, "setStr", "fKey key value", "");` |
| 227 | `setObj` | `REGISTERF(setItem<object_stack_ref&>, "setObj", "fKey key container", "");` |
| 228 | `setForm` | `REGISTERF(setItem<form_ref>, "setForm", "fKey key value", "");` |

### JLua

Source: `src/JContainers/src/api_3/tes_lua.h`

| Line | Exported/native name | Registration source |
|---:|---|---|
| 20 | `evalLuaFlt` | `REGISTERF(evalLua<Float32>, "evalLuaFlt", ARGNAMES "0.0" ARGNAMES_2, R"===(Evaluates piece of Lua code. The arguments are carried by @transport object. The @transport is any kind of object, not just JMap. If @minimizeLifetime is True the function will invoke JValue.zeroLifetime on the @transport object. It is more than wise to re-use @transport when evaluating lot of lua code at once. Returns @default value if evaluation fails.  WARNING: You can transfer in/out from Lua only 24-bit integers with exact precision (+/- 16 777 216) Anything bigger or smaller than that will have "holes" due to how the floating point rounding works.  Usage example:` |
| 38 | `evalLuaInt` | `REGISTERF(evalLua<SInt32>, "evalLuaInt", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| 39 | `evalLuaStr` | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", ARGNAMES R"("")" ARGNAMES_2, nullptr);` |
| 40 | `evalLuaObj` | `REGISTERF(evalLua<Handle>, "evalLuaObj", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| 41 | `evalLuaForm` | `REGISTERF(evalLua<TESForm*>, "evalLuaForm", ARGNAMES "None" ARGNAMES_2, nullptr);` |
| 58 | `setStr` | `REGISTERF(pushArg<const char*>, "setStr", ARGNAMES, R"===(Inserts new (or replaces existing) {key -> value} pair. Expects that @transport is JMap object, if @transport is 0 it creates new JMap object. Returns @transport)===");` |
| 61 | `setFlt` | `REGISTERF(pushArg<Float32>, "setFlt", ARGNAMES, "");` |
| 62 | `setInt` | `REGISTERF(pushArg<SInt32>, "setInt", ARGNAMES, "");` |
| 63 | `setForm` | `REGISTERF(pushArg<form_ref>, "setForm", ARGNAMES, "");` |
| 64 | `setObj` | `REGISTERF(pushArg<object_base*>, "setObj", ARGNAMES, "");` |


## Core class semantics

### JValue
Common base functionality shared by JArray/JMap/JFormMap/JIntMap:
- lifetime retain/release;
- pools;
- shallow/deep copies;
- existence/type checks;
- clear/count;
- JSON file read/write;
- JSON string serialization;
- path solving/get/set;
- experimental Lua evaluation.

### JArray
Heterogeneous ordered container supporting Int, Float, String, Form and nested JContainer objects. Supports negative indexing in APIs documented by the source, conversion to Papyrus arrays, find/count/set/add/erase, sorting, uniqueness and reverse.

### JMap
String-keyed heterogeneous dictionary.

### JFormMap
Form-keyed heterogeneous dictionary. Form-key iteration includes special handling so unloaded/invalid form keys are not naively exposed as ordinary valid Papyrus Forms.

### JIntMap
Integer-keyed heterogeneous dictionary.

### JAtomic
Atomic read-modify-write operations against values resolved through object paths: add/multiply/mod/divide/bitwise operations, exchange and compare-exchange.

### JDB
Global database rooted in a retained JMap-like structure. Provides path solving and key/value association.

### JFormDB
Persistent Form-keyed storage abstraction layered over named storage and container entries.

### JString
String wrapping/conversion, Form string encode/decode and UUID utilities.

### JContainers
Versioning, install checks, filesystem helpers and user-directory utilities.

### JLua
Experimental Lua evaluation and transport-object helpers.

## Runtime compatibility

Release v4.3.2 provides separate builds:
- AE/64: SKSE 2.3.1 / Skyrim 1.7.104;
- GOG: SKSE 2.2.6 / Skyrim 1.6.1179;
- VR: SKSEVR 2.0.12 / Skyrim VR 1.4.15.

## Source count caution

A registration macro row can expand into one Papyrus function, and template/meta classes can register shared functions into multiple exported classes. Therefore raw macro-row count is not a unique runtime-function count.

Use class + exported function identity as the canonical API key.
