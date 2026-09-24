# JContainers Current Papyrus Registration API — Utilities, Lua, Strings, and Atomics

Imported: 2026-09-24
Source: https://github.com/SilverIce/JContainers · ref `master`
Registration statements cataloged: **40**
API metadata source: `consts::api_version (resolved at build time)`
Status: current-source C++ Papyrus registration metadata catalog

This companion to `jcontainers-collections-databases.md` covers the remaining classes registered from `JContainers/src/api_3/`.

## JContainers

Source: `JContainers/src/api_3/tes_jcontainers.h` · blob `2b07b7b22219b47d030de568d7369d8804e9d7ed`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `__isInstalled` | 17 | `REGISTERF2_STATELESS(__isInstalled, nullptr, "It's NOT part of public API");` |
| `APIVersion` | 22 | `REGISTERF2_STATELESS(APIVersion, nullptr, []() { std::stringstream comm; comm << "Version information.\n" "It's a good practice to validate installed JContainers version with the following code:\n" " bool isJCValid = JContainers.APIVersion() == AV && JContainers.featureVersion() >= FV\n" "where AV and FV are hardcoded API and feature version numbers.\n"; comm << "Current API version is " << APIVersion() << std::endl; comm << "Current feature version is " << featureVersion(); return comm.str(); });` |
| `featureVersion` | 36 | `REGISTERF2_STATELESS(featureVersion, nullptr, nullptr);` |
| `fileExistsAtPath` | 47 | `REGISTERF2_STATELESS(fileExistsAtPath, "path", "Returns true if the file at a specified @path exists");` |
| `contentsOfDirectoryAtPath` | 82 | `REGISTERF_STATELESS( contentsOfDirectoryAtPath<VMResultArray<skse::string_ref>>, "contentsOfDirectoryAtPath", "directoryPath extension=\"\"", nullptr);` |
| `removeFileAtPath` | 91 | `REGISTERF2_STATELESS(removeFileAtPath, "path", "Deletes the file or directory identified by the @path");` |
| `userDirectory` | 112 | `REGISTERF_STATELESS(_userDirectory, "userDirectory", "", "A path to user-specific directory - "JC_USER_FILES);` |
| `lastError` | 117 | `REGISTERF2_STATELESS(lastError, nullptr, []() { std::stringstream comm; comm << "DEPRECATED. Returns last occured error (error code):"; for (int i = 0; i < JErrorCount; ++i) { comm << std::endl << i << " - " << JErrorCodeToString((JErrorCode)i); } return comm.str(); });` |
| `lastErrorString` | 129 | `REGISTERF2_STATELESS(lastErrorString, nullptr, "DEPRECATED. Returns string that describes last error");` |

## JLua

Source: `JContainers/src/api_3/tes_lua.h` · blob `74bbf3ecc1176f9840eabd5d9934f2b2d8e65e71`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `evalLuaFlt` | 16 | `REGISTERF(evalLua<Float32>, "evalLuaFlt", ARGNAMES "0.0" ARGNAMES_2, R"===(Evaluates piece of Lua code. The arguments are carried by @transport object. The @transport is any kind of object, not just JMap. If @minimizeLifetime is True the function will invoke JValue.zeroLifetime on the @transport object. It is more than wise to re-use @transport when evaluating lot of lua code at once. Returns @default value if evaluation fails. Usage example: ; 7 from the end until 9 from the end. Returns "Lua" string string input = "Hello Lua user" string s = JLua.evaLuaStr("return string.sub(args.string, args.low, args.high)",\ JLua.setStr("string",input, JLua.setInt("low",7, JLua.setInt("high",9 )))\ ) )===");` |
| `evalLuaInt` | 30 | `REGISTERF(evalLua<SInt32>, "evalLuaInt", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| `evalLuaStr` | 31 | `REGISTERF(evalLua<skse::string_ref>, "evalLuaStr", ARGNAMES R"("")" ARGNAMES_2, nullptr);` |
| `evalLuaObj` | 32 | `REGISTERF(evalLua<Handle>, "evalLuaObj", ARGNAMES "0" ARGNAMES_2, nullptr);` |
| `evalLuaForm` | 33 | `REGISTERF(evalLua<TESForm*>, "evalLuaForm", ARGNAMES "None" ARGNAMES_2, nullptr);` |
| `setStr` | 47 | `REGISTERF(pushArg<const char*>, "setStr", ARGNAMES, R"===(Inserts new (or replaces existing) {key -> value} pair. Expects that @transport is JMap object, if @transport is 0 it creates new JMap object. Returns @transport)===");` |
| `setFlt` | 50 | `REGISTERF(pushArg<Float32>, "setFlt", ARGNAMES, "");` |
| `setInt` | 51 | `REGISTERF(pushArg<SInt32>, "setInt", ARGNAMES, "");` |
| `setForm` | 52 | `REGISTERF(pushArg<form_ref>, "setForm", ARGNAMES, "");` |
| `setObj` | 53 | `REGISTERF(pushArg<object_base*>, "setObj", ARGNAMES, "");` |

## JString

Source: `JContainers/src/api_3/tes_string.h` · blob `4a7c320b1861ddcf316771e0903b09d38530a8b1`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `wrap` | 37 | `REGISTERF2(wrap, "sourceText charactersPerLine=60", "Breaks source text onto set of lines of almost equal size.\n\ Returns JArray object containing lines.\n\ Accepts ASCII and UTF-8 encoded strings only");` |
| `decodeFormStringToFormId` | 55 | `REGISTERF2_STATELESS(decodeFormStringToFormId, "formString", "FormId\|Form <-> \"__formData\|<pluginName>\|<lowFormId>\"-string converisons");` |
| `decodeFormStringToForm` | 56 | `REGISTERF2_STATELESS(decodeFormStringToForm, "formString", "");` |
| `encodeFormToString` | 57 | `REGISTERF2_STATELESS(encodeFormToString, "value", "");` |
| `encodeFormIdToString` | 58 | `REGISTERF2_STATELESS(encodeFormIdToString, "formId", "");` |
| `generateUUID` | 70 | `REGISTERF2_STATELESS(generateUUID, "", "Generates random uuid-string like 2e80251a-ab22-4ad8-928c-2d1c9561270e");` |

## JAtomic

Source: `JContainers/src/api_3/tes_atomic.h` · blob `689c02c43b4f9cd92a312bc4590ab8036bd40687`

| Public name | Source line | Registration metadata |
|---|---:|---|
| `fetchAddInt` | 83 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::plus<SInt32>>), "fetchAddInt", PARAMS_INT, "Performs:\n\ T previous = value.at.path\n\ value.at.path = value.at.path + value\n\ return previous" );` |
| `fetchAddFlt` | 89 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::plus<Float32>>), "fetchAddFlt", PARAMS_FLT, nullptr);` |
| `fetchMultInt` | 91 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::multiplies<SInt32>>), "fetchMultInt", PARAMS_INT, "x *= v");` |
| `fetchMultFlt` | 92 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::multiplies<Float32>>), "fetchMultFlt", PARAMS_FLT, nullptr);` |
| `fetchModInt` | 94 | `REGISTERF(ARGS(performAtomicFunction<int32_t, std::modulus<int32_t>>), "fetchModInt", PARAMS_INT, "x %= v");` |
| `fetchDivInt` | 96 | `REGISTERF(ARGS(performAtomicFunction<SInt32, std::divides<SInt32>>), "fetchDivInt", PARAMS_INT, "x /= v");` |
| `fetchDivFlt` | 97 | `REGISTERF(ARGS(performAtomicFunction<Float32, std::divides<Float32>>), "fetchDivFlt", PARAMS_FLT, nullptr);` |
| `fetchAndInt` | 99 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_and<uint32_t>>), "fetchAndInt", PARAMS_INT, "x &= v");` |
| `fetchXorInt` | 100 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_xor<uint32_t>>), "fetchXorInt", PARAMS_INT, "x ^= v");` |
| `fetchOrInt` | 101 | `REGISTERF(ARGS(performAtomicFunction<uint32_t, std::bit_or<uint32_t>>), "fetchOrInt", PARAMS_INT, "x \|= v");` |
| `exchangeInt` | 107 | `REGISTERF(exchange<SInt32>, "exchangeInt", PARAMS_INT "0", "u");` |
| `exchangeFlt` | 108 | `REGISTERF(exchange<Float32>, "exchangeFlt", PARAMS_INT "0.0", nullptr);` |
| `exchangeStr` | 109 | `REGISTERF(exchange<std::string>, "exchangeStr", PARAMS_INT "\"\"", nullptr);` |
| `exchangeForm` | 111 | `REGISTERF(exchange<form_ref>, "exchangeForm", PARAMS_INT "None", nullptr);` |
| `exchangeObj` | 112 | `REGISTERF(exchange<object_base*>, "exchangeObj", PARAMS_INT "0", nullptr);` |

## Semantic class map

### JContainers
Framework/environment utilities: installation/API/feature version probes, filesystem existence/removal helpers, user directory, and error reporting.

### JLua
Experimental Lua bridge: typed Lua evaluation plus typed argument transport into a JContainers object.

### JString
String utilities including line wrapping, Form ↔ serialized form-string conversion, and UUID generation.

### JAtomic
Atomic typed updates/exchanges for JContainers values, including arithmetic and bitwise integer operations plus typed exchange.

## Stability notes

- JLua source explicitly describes its API as unstable and subject to change/removal.
- Internal/private helpers such as `__isInstalled` must not be promoted as ordinary public API merely because they are registered.
- `lastErrorString` is marked deprecated in current source.
- The generated Papyrus signature's exact return/parameter types come from the reflection binder; this catalog intentionally preserves registration metadata instead of guessing types from C++ template syntax.

## Complete current JContainers registration surface

Together with `jcontainers-collections-databases.md`, the catalog covers:
- JValue;
- JArray;
- JMap;
- JFormMap;
- JIntMap;
- JDB;
- JFormDB;
- JContainers;
- JLua;
- JString;
- JAtomic.

The source tree also contains generated/internal Lua/C APIs, but those are separate interfaces and should not be mislabeled as Papyrus functions.
