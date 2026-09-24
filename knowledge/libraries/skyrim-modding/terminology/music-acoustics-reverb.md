# Skyrim Modding Terminology — Music, Acoustic Spaces, Reverb, and Ambient Audio

Imported: 2026-09-24
Status: sourced deep-ingestion pass 19

## Music records

### MusicType / MUSC
Record containing rules/track lists used by game contexts such as exploration, combat, towns or special locations.

### MusicTrack / MUST
Record representing a playable music track/resource and playback-related metadata.

### Track list
Collection of MusicTrack entries inside one MusicType.

### Priority
MusicType relationship controlling which music context can replace/interfere with another.

### Ducking
Lowering other audio/music volume while higher-priority sound/music/dialogue plays.

### Music transition
Engine changing between active MusicTypes/tracks.

### Looping music
Track configured to repeat.

### One-shot music
Track intended to play once then return/transition.

### Combat music
MusicType selected during combat.

### Explore music
World/region/location exploration music.

### Dungeon music
Music associated with dungeon/interior context.

### Location music
MusicType associated with Location.

### Region music
MusicType associated with Region.

### Cell music
Cell-specific music assignment.

## Music Type Distributor / MTD

### MTD
**Expansion:** Music Type Distributor. SKSE framework adding tracks to MusicType lists and assigning MusicTypes to Locations/Regions at runtime.

### _MUS.ini
MTD config suffix.

### MusicType distribution
Add tracks to existing music type.

### MusicType replacement
Clear existing tracklist before adding configured set.

### Dynamic MusicType
MTD can create a new MusicType list at runtime using configured EditorID.

### Location assignment
Assign one MusicType to one Location at runtime.

### Region assignment
Assign MusicType to Region.

### Alphabetical config order
Current MTD processes `_MUS.ini` files in alphabetical order, with uppercase sorting before lowercase according to documentation.

### Music dump
Framework debug option outputting known tracks/types/locations/regions to log for config authoring.

### Runtime music merge
Combining multiple music mods without static MUSC conflicts.

### GF Music Manager
2026 external tool scanning MO2 music mods, allowing track selection and generating managed output using MTD/SkyPatcher integrations.

## Acoustic spaces

### Acoustic space
Cell/reference acoustic environment controlling reverberation/output behavior.

### Acoustic template
Reusable audio/reverb profile assigned to interiors/areas.

### Reverb
Reflected/delayed sound simulating room/environment acoustics.

### ReverbParameters / REVB
Record defining reverb characteristics.

### SoundOutputModel / SOPM
Record controlling 2D/3D attenuation, reverb send and output routing.

### SoundCategory / SNCT
Audio category controlling group volume/behavior.

### Interior ambience
Looping/subtle environmental sound inside cells.

### Exterior ambience
Regional/world ambient audio.

### Interior weather audio
Rain/wind/thunder ambience heard inside buildings according to current weather.

### Room size
Acoustic-space/reverb characteristic determining reflection/delay feeling.

### Surface material
Conceptual acoustic input affecting room sound; mods may classify spaces according to material/layout.

### Acoustic mismatch
Two visually similar interiors use inconsistent acoustic spaces.

### Cell acoustic field
CELL-level reference to acoustic space/template; can conflict with lighting/cell-overhaul edits.

### SkyPatcher acoustic forwarding
Runtime patch reapplies desired acoustic space to cells so lighting/cell mods do not overwrite audio fix.

## Sound Record Distributor relationship

### SRD region audio
Runtime distribution of sound descriptors into REGN/weather-related data without static record conflicts.

### SRD weapon audio
Runtime sound field patching for weapon records.

### SRD acoustic integration
Audio overhaul can use runtime sound distribution plus static/runtime cell acoustic-space corrections.

## Audio formats

### XWM
Compressed Bethesda audio format often used for music/voice.

### WAV
PCM authoring/source format.

### FUZ
Dialogue voice+lip container, not ordinary background music format.

### Music file path
Resource path referenced by MUST/sound records.

### Loose music
Audio file installed directly in Data.

### Packed music
Audio archive member loaded from BSA.

## Failure patterns

### Music silence
No eligible MusicType/track, missing audio file, wrong path/format, priority state or broken runtime config.

### Music overlap
Two systems play/transition simultaneously or one framework doesn't stop another type.

### Stuck combat music
Combat/music state fails to transition after combat ends.

### Wrong interior music
Cell/Location assignment overwritten or runtime distributor applies unintended type.

### No reverb
Cell acoustic space/output model absent/overwritten.

### Excessive reverb
Wrong acoustic profile for room/cell.

### Missing interior rain
Weather/ambient sound path/category/runtime distribution mismatch.

### Duplicate ambience
Static audio overhaul and SRD/runtime config both add same loop.

## Diagnostic rules

1. Separate MusicType selection from actual audio file/resource availability.
2. Cell acoustic space and Location/Region music are different systems.
3. Runtime music/audio distributors can override static xEdit winners.
4. Check MusicType priority/context before editing track files.
5. If an interior lighting overhaul breaks reverb, inspect CELL acoustic field/runtime SkyPatch.
6. Avoid duplicating the same ambient track through static and SRD distribution.
7. Music mod merging must preserve permissions/provenance of source audio.

## Sources

- Music Type Distributor: https://www.nexusmods.com/skyrimspecialedition/mods/119571
- GF Music Manager: https://www.nexusmods.com/skyrimspecialedition/mods/190329
- Reverb Interior Sounds Expansion: https://www.nexusmods.com/skyrimspecialedition/mods/77947
- Acoustic Space Improvement Fixes: https://www.nexusmods.com/skyrimspecialedition/mods/78992
- Sound Record Distributor: https://www.nexusmods.com/skyrimspecialedition/mods/77815

## Dated note

A dedicated Music Type Distributor build for Skyrim 1.7.104 was published in September 2026 after runtime changes. Framework DLL compatibility should be checked separately from `_MUS.ini` config compatibility.
