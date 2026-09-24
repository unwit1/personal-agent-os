# Skyrim Modding Terminology — Native Debugging, Profiling, and In-Game Inspection

Imported: 2026-09-24
Status: sourced deep-ingestion pass 11

## Runtime inspection

### More Informative Console
SKSE plugin extending the in-game console with base/reference FormIDs, form types, defining/last-modifying plugins, scripts, aliases and ExtraData inspection.

### Base FormID
FormID of the selected reference's base object.

### Reference FormID
FormID of the placed/runtime reference itself.

### Defining plugin
Plugin where a form originally originates.

### Last modifying plugin
Last plugin in load order overriding the selected record.

### ExtraData inspection
Viewing runtime per-reference metadata that is not fully represented by the base record.

### Alias inspection
Listing quest aliases currently containing a selected reference.

### Script inspection
Listing scripts attached to a selected form/reference.

### Console selection latency
Inspection can become expensive for references such as the player with many scripts/aliases; More Informative Console exposes settings to suppress costly enumeration.

## Dear ImGui

### Dear ImGui
Immediate-mode C++ GUI library widely used by SKSE plugins for in-game developer/configuration overlays.

### Immediate-mode GUI
UI programming model where interface state is emitted every frame from current application state rather than represented as a persistent retained widget tree.

### ImGui context
Runtime global/state container owning fonts, windows, input state and draw data.

### ImGui frame
One UI update/render cycle.

### ImGui window
Runtime tool/config panel built by Begin/End-style calls.

### Docking
ImGui feature allowing tool windows to be docked into layouts.

### ImGui backend
Platform/render integration translating input and rendering ImGui draw lists.

### DX11 backend
Direct3D 11 rendering integration typically used for Skyrim SE overlays.

### Input capture
ImGui requests mouse/keyboard input so game controls should not simultaneously react.

### io.WantCaptureMouse
ImGui state indicating UI wants mouse input.

### io.WantCaptureKeyboard
ImGui state indicating UI wants keyboard input.

### Overlay conflict
Multiple graphics/UI overlays hook the same DXGI/D3D/input paths and may interfere.

### Metrics/Debugger
Built-in Dear ImGui window exposing windows, draw lists, tables, input and internal state.

### Debug Log
ImGui tool displaying categorized UI/input/focus events.

### Item Picker
Debug tool selecting an on-screen ImGui item and locating the code call stack that created it.

## SKSE Menu Framework

### SKSE Menu Framework
Native framework used by newer SKSE plugins to expose in-game configuration/debug interfaces without each plugin independently reinventing menu/render integration.

### Native menu
C++/ImGui-like runtime interface rather than a SkyUI Papyrus MCM.

### Menu registration
Plugin registers a panel/page with the shared native-menu framework.

### Menu Framework dependency
Native mod can load core gameplay logic yet lack its UI if its menu framework dependency is absent/incompatible, depending on implementation.

## Load-time profiling

### SKSE Load Time Profiler
SKSE/SKSEVR plugin measuring startup time for ESP/ESM modules and SKSE DLL lifecycle callbacks.

### File-open phase
Time spent opening plugin file during game startup.

### Form-load phase
Time spent loading/constructing forms from a plugin.

### File-close phase
Plugin-loading cleanup/close timing.

### DLL lifecycle timing
Time consumed by an SKSE DLL across callbacks such as plugin load, PostLoad and DataLoaded.

### Perfetto trace
JSON trace format viewable in Perfetto/Chrome-style timeline tools for correlating startup events.

### Startup bottleneck
Mod/plugin/DLL phase contributing disproportionately to main-menu load time.

### Warm-cache bias
Repeated startup tests can differ because OS/filesystem cache already contains data. Benchmark methodology should distinguish cold and warm runs.

## Frame profiling

### Frame time
Milliseconds per rendered frame.

### Engine delta
Game engine's time-step value used by simulation.

### Real delta
Unscaled/measured frame delta.

### Active high actors
Engine set/count of high-priority actors currently processed; useful as one indicator of AI/actor workload.

### Working set
Physical RAM currently resident for Skyrim process.

### Asynchronous logging
Writing profiling data from a background thread/buffer to avoid disk I/O perturbing every measured frame.

### Sampling overhead
Profiler itself consumes CPU/time. Measurement tooling must keep overhead low and report methodology.

### Benchmark route
Repeatable in-game path/scenario used to compare mod/settings changes.

### Warmup frames
Initial frames excluded so loading/setup transients do not dominate benchmark.

### CSV trace
Tabular performance data suitable for statistical analysis.

## Papyrus profiling

### StartScriptProfiling
Papyrus/Game API enabling profiling for a script.

### StopScriptProfiling
Stops script profiling.

### StartObjectProfiling
Profiles Papyrus activity associated with an object.

### StartStackProfiling
Profiles one Papyrus stack.

### Papyrus profile log
Profiler output showing script/function/event execution data separate from ordinary error/trace log.

## Native debugger

### Visual Studio debugger
Native source-level debugging for SKSE DLLs when symbols/source/build match.

### WinDbg
Windows low-level debugger suitable for dumps, exceptions, stacks, registers and symbol inspection.

### x64dbg
Interactive user-mode debugger often used for executable/plugin reverse engineering.

### Breakpoint
Debugger instruction stop at a chosen code address/function/source line.

### Conditional breakpoint
Stops only when a supplied expression/condition matches.

### Data breakpoint
Stops when watched memory changes.

### Minidump
Captured process memory/thread/exception state for offline native analysis.

### Symbolized stack
Call stack resolved through PDB symbols.

### Module base
Loaded base address used to convert absolute addresses to RVAs/offsets.

### RVA
Relative virtual address from module base.

### Disassembly
Machine instructions around a fault/hook point.

### Watch expression
Debugger expression inspected while paused.

## Graphics profiling

### RenderDoc
Frame-capture debugger used by graphics developers to inspect draw calls, resources, shaders and render targets.

### Frame capture
Recorded graphics frame containing command/resource state.

### Draw-call inspection
Examining which mesh/material/shader rendered a problematic visual.

### Shader debugging
Inspecting shader inputs/output/resources for rendering problems.

### GPU capture conflict
RenderDoc and other overlays/injectors can conflict with ENB/Community Shaders/Reshade; reproduce with controlled injector stack.

## Diagnostic rules

1. Inspect actual runtime form origin/override rather than relying on memory of load order.
2. Profiling results need repeatable scenes and multiple samples.
3. Keep profiler/logging overhead lower than the effect being measured.
4. Separate startup load time, frame-time performance, Papyrus work, native CPU work and GPU workload.
5. ImGui UI/input issues can be overlay/input-capture problems independent of plugin logic.
6. Preserve matching PDB/build commit for native crash diagnosis.
7. A tool reporting one plugin as slow does not prove it is poorly written; record amount/content loaded and compare controlled baselines.

## Sources

- More Informative Console source: https://github.com/Liolel/More-Informative-Console
- Dear ImGui: https://github.com/ocornut/imgui
- ImGui debug tools: https://github.com/ocornut/imgui/wiki/Debug-Tools
- SKSE Load Time Profiler: https://github.com/QTR-Modding/SKSELoadTimeProfiler
- Skyrim Performance Monitor example: https://github.com/highpower1/skyrim_perf_monitor
- Creation Kit Papyrus debug/profiling API catalog: https://ck.uesp.net/wiki/Category:Scripting
