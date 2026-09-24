# Skyrim Modding Terminology — Audio, Voice, Dialogue Assets, Localization, Strings, and Archives

Imported: 2026-09-24
Status: sourced encyclopedia pass 3

This module covers voice and sound asset formats, dialogue-lip synchronization, localization files, BSA packaging, and the relationship between plugin records and external text/audio assets.

## Audio and voice formats

### WAV
Uncompressed/PCM-oriented waveform audio format commonly used as an intermediate/source format during Skyrim voice and sound authoring.

### XWM
Microsoft xWMA-derived compressed audio format used by Skyrim for many sound/voice assets.

### FUZ
Bethesda voice container used by Skyrim. A FUZ commonly combines compressed voice audio with optional lip-synchronization data.

### LIP
Lip-sync data used by Bethesda dialogue playback to animate mouth movement in correspondence with spoken dialogue.

### FUZ unpacking
Extracting the audio payload and LIP data from a FUZ container.

### FUZ packing
Combining compatible audio and lip data into a FUZ container for game use.

### xWMAEncode
Microsoft command-line encoder historically used in Skyrim audio workflows to convert WAV audio to/from XWM.

### Voice asset
Audio file associated with a specific dialogue INFO/response, voice type and plugin naming/path convention.

### Sound asset
General non-dialogue audio such as effects, ambience, UI sounds, footsteps or music-related resources.

### Dialogue audio
Spoken voice asset associated with dialogue records rather than general SoundDescriptor playback.

### Voice folder
Data path structure under Sound/Voice that organizes spoken dialogue by plugin and VoiceType.

### Plugin-name voice path
Voice assets are conventionally grouped under a folder corresponding to the plugin that owns the dialogue records.

### VoiceType
Game form/category used to determine which voice set an actor/talking activator uses and which dialogue audio path/naming applies.

### Shared VoiceType
Multiple actors using one VoiceType can share generated/recorded dialogue availability where conditions permit.

### Unique voice type
Voice type created for a specific actor/group so dialogue/audio can be targeted independently.

### Silent voice
Technique using silent audio of sufficient duration so subtitle-only custom dialogue remains displayed/advances predictably.

### Lip-sync generation
Process creating LIP data from dialogue audio/text through FaceFX/Creation Kit-compatible tooling.

### FaceFX
Middleware/tooling lineage used by Bethesda games for facial/lip animation generation.

### FaceFXWrapper
Community wrapper/tool component commonly used by modern LIP-generation utilities to invoke Bethesda-compatible lip-generation functionality.

### Runalip
Community utility for generating LIP/FUZ assets from source dialogue audio.

### Yakitori Audio Converter
Community tool capable of converting among FUZ/XWM/WAV and handling LIP alongside audio, including assets inside archives.

### Audio bitrate
Compression bitrate controlling XWM size/quality; encoder/file limitations can matter for long voice files.

### Sampling rate
Number of audio samples per second; source/encoder compatibility can depend on supported rates.

### Mono voice
Single-channel voice source commonly used for dialogue generation.

### Voice normalization
Adjusting loudness/peak characteristics so custom dialogue sits consistently with existing game audio.

### Clipping
Audio distortion caused when signal amplitude exceeds representable limits.

### Noise floor
Background noise level in recorded dialogue.

### Room tone
Ambient recording noise/profile that can help voice edits sound natural between phrases.

## Dialogue asset mapping

### Dialogue INFO / INFO record
Individual dialogue response record whose response text, conditions, speaker context and generated voice files are linked.

### Response
One spoken text response associated with INFO data.

### Response number
Identifier/index for multiple response lines within a dialogue info, relevant to generated file naming.

### Dialogue filename
Game/tool-generated filename derived from dialogue form identity and response metadata. Exact convention must be generated/verified rather than guessed.

### VoiceType path resolution
Runtime selects audio based on owning plugin/dialogue identity and speaker VoiceType.

### Missing voice
Dialogue text/INFO exists but expected audio asset cannot be found.

### Mismatched voice path
Audio exists but under the wrong plugin or VoiceType directory and therefore does not resolve.

### Stale voice file
Dialogue record changed or moved/renumbered but old voice assets remain under obsolete generated names.

### Subtitle fallback
Player may see subtitle text despite missing voice, depending on settings/dialogue timing; this does not prove voice files are correctly installed.

### Voice asset conflict
Two mods provide the same voice-relative file path; asset priority selects the winner.

### Voice replacer
Mod replacing dialogue audio while leaving underlying INFO text/logic mostly intact.

## Sound records

### SoundDescriptor
Game form defining playback characteristics and referenced audio for a sound.

### SoundMarker
Placed/runtime object used to emit sound from a location.

### SoundCategory
Category controlling groups of sounds, volume and related mixer behavior.

### Sound output model
Record/data controlling spatialization and attenuation characteristics for sounds.

### Looping sound
Sound configured to repeat continuously while active.

### 2D sound
Audio played without ordinary 3D positional attenuation.

### 3D sound
Positional audio whose volume/panning/attenuation depends on listener/source location.

### Attenuation
How sound volume changes with distance.

### Reverb
Environment processing simulating reflections/space acoustics.

### MusicType
Game form controlling music tracks/conditions/transitions.

## Localization

### Localization
Separating player-visible text from plugin binary fields into language-specific external string tables.

### Localized plugin
Plugin whose header/record strings are represented through external string IDs/files rather than storing all text directly inline.

### STRINGS
Bethesda localization file containing one class of localized strings used by a plugin/game.

### DLSTRINGS
Localization file class used for strings requiring length-prefixed/different storage, commonly dialogue/descriptive text categories.

### ILSTRINGS
Localization file class used for another length-prefixed localized string category.

### String ID
Numeric lookup identifier connecting a plugin field to an entry in external localization files.

### Lookup failure
Localized plugin refers to a string ID that is absent from the active language's string files, causing missing/placeholder text.

### Language suffix
Localization filename component selecting language, such as English/German/etc.

### Hybrid translation mode
xTranslator workflow loading plugin record structure and associated localization files together so strings can be edited with record context.

### xTranslator
Specialized Bethesda translation/localization editor capable of translating ESP/ESM fields and STRINGS/DLSTRINGS/ILSTRINGS data.

### SST dictionary
xTranslator translation-memory/dictionary format used to reuse known translations.

### Translation cache
Tool-maintained mapping of source/target game strings used to accelerate/standardize translation.

### Localized ESP
ESP/ESM flagged/configured so appropriate textual fields use external string lookup data.

### Delocalization
Converting localized external-string fields back to inline text in a plugin, where supported/appropriate.

### Relocalization
Generating/reconnecting external string files and IDs for a localized plugin.

### String-table conflict
Different packages provide same localization filename/path; asset priority decides the active string table.

## Bethesda archives

### BSA
Bethesda Softworks Archive used by Skyrim to package Data-relative game/mod resources.

### Archive
Container file holding many game assets while preserving Data-relative paths.

### Loose asset
Asset installed directly under Data/effective VFS rather than stored inside an archive.

### Archive member
One file/path stored inside a BSA.

### Archive path
Data-relative path recorded for an archive member.

### BSA extraction
Unpacking archive members to loose files.

### BSA packing
Creating a BSA from a folder/file set.

### Archive.exe
Bethesda Creation Kit archive tool historically used for creating BSA packages.

### BSA Browser
Community archive browser/extractor supporting BSA and related Bethesda archive formats.

### BSArch
Command-line Bethesda archive packing/extraction tool used by several modern modding workflows.

### Cathedral Assets Optimizer / CAO
Community asset-processing tool commonly used for mesh/texture optimization and BSA creation/packing.

### Archive compression
Per-file/archive compression reducing storage size at cost of decompression work and format constraints.

### Archive flag
Header/settings indicating classes of content or behavior in BSA metadata.

### Archive loading
Engine process mounting BSA content associated with game/mod configuration.

### Plugin-associated BSA
Archive named/associated so the engine loads it with a corresponding plugin according to Skyrim's archive-loading rules.

### Loose-over-archive precedence
Loose assets can override equivalent paths from loaded archives under Skyrim's normal resource lookup behavior. Mod-manager virtualization may additionally determine which loose file exists.

### Archive conflict
Same relative path exists in multiple loaded archives and/or loose files; final resource resolution depends on engine/archive ordering and loose-file precedence.

### Packed script
PEX stored inside BSA rather than loose under Scripts.

### Packed FaceGen
FaceGen mesh/tint stored inside BSA; troubleshooting still requires matching effective plugin record and archive/loose winner.

### Packed voice
FUZ/XWM/LIP voice assets stored in voice archives.

## Asset packaging diagnostics

### Missing archive member
Plugin references/assumes asset path that was not packed into distributed archive.

### Wrong archive path
Asset is present but internal archive directory differs from expected Data-relative path.

### Stale packed asset
BSA contains an older file while a mod author tests against a newer loose file, causing distributed users to receive different behavior.

### Loose development residue
Author's local Data/VFS contains loose files absent from published archive, masking packaging bugs.

### Archive/loose mismatch
The author or user has both packed and loose versions of a resource and the unintended one wins.

### Voice packaging omission
Custom dialogue plugin ships without corresponding Sound/Voice assets.

### FaceGen packaging omission
NPC appearance plugin ships without generated FaceGeom/FaceTint assets, a classic source of appearance mismatch on other systems.

## Diagnostic rules encoded for Agent OS

1. A dialogue INFO record and its voice assets are separate layers; inspect both.
2. FUZ is a container relationship, not synonymous with raw audio; it can contain XWM plus LIP.
3. When dialogue text works but audio does not, verify VoiceType and exact generated voice path before changing quest conditions.
4. Localization lookup failures are not necessarily missing dialogue records.
5. For localized plugins, inspect STRINGS/DLSTRINGS/ILSTRINGS asset winners as well as ESP load order.
6. When a mod works only on the author's machine, check for loose development residue not included in its archive.
7. Treat BSA contents as Data-relative assets; archive packaging does not eliminate normal path/overwrite reasoning.
8. Generated FaceGen and voice resources should be validated from a clean installed package, not only the developer workspace.
9. Do not assume BA2 terminology from Fallout 4 applies to Skyrim SE packaging; Skyrim's normal mod archive format is BSA.
10. Preserve original high-quality voice sources separately from compressed game-delivery XWM/FUZ files.

## Sources

- Creation Kit Wiki File Menu / localization export: https://ck.uesp.net/wiki/File_menu
- xTranslator: https://github.com/MGuffin/xTranslator
- Yakitori Audio Converter: https://www.nexusmods.com/skyrimspecialedition/mods/17765
- Runalip: https://www.nexusmods.com/skyrimspecialedition/mods/98931
- BSA Browser: https://github.com/AlexxEG/BSA_Browser
- Bethesda Modding Library archive overview: https://baddogskyrim.github.io/BethesdaLibrary/file-formats/archives/
- Creation Kit Wiki Retexture Tutorial/BSA context: https://ck.uesp.net/wiki/Retexture_Tutorial
