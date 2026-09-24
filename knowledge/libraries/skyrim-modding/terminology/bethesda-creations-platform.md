# Skyrim Modding Terminology — Bethesda Creations, Creation Kit Publishing, and Official Content

Imported: 2026-09-24
Status: sourced deep-ingestion pass 10

## Creations ecosystem

### Bethesda Game Studios Creations
Unified Skyrim Special Edition in-game/content platform combining the former Mods/Creation Club experiences with newer community and Verified Creator content.

### Creation
Content published through Bethesda's Creations ecosystem.

### Creation Club
Earlier curated paid-content program whose items are now surfaced through the broader Creations system.

### Verified Creator
Creator accepted into Bethesda's program enabling approved paid Creations subject to platform terms/review.

### Creation Credits
Bethesda virtual currency used for eligible paid Creations.

### Creations menu
In-game browser/download/load-order surface for Bethesda-hosted content.

### Creations library
User's subscribed/owned Creations associated with Bethesda.net account.

### Subscribe
Associate a Creation with user library so game can download/install it.

### Missing Creation check
Game feature detecting Creation dependencies missing when loading a save and offering resolution path.

### Stored Active Load Order
Feature allowing active Creations load order to be stored/retrieved from Bethesda.net.

## Official included content

### Anniversary Upgrade
Paid bundle/content entitlement containing Creation Club content; separate concept from executable runtime version.

### Fishing
Official Creation included as baseline/free content in modern SSE installs.

### Rare Curios
Official Creation included as baseline/free content.

### Saints & Seducers
Official Creation included as baseline/free content.

### Survival Mode
Official Creation included as baseline/free content.

### cc-prefixed plugin
Filename convention used by official Creation Club/Creation content.

### Official master/content
Bethesda-distributed plugin/assets that can act as dependencies like other masters.

### Missing official content
Save/mod requires a Creation/plugin not currently installed.

### Creation update
Bethesda-hosted content version changes independently from user's third-party mod setup and can invalidate patches.

## Resource Pack / modern CK

### Resource Pack
Bethesda creator resource introduced with Creations-era update containing art/script assets intended for creators.

### _ResourcePack.esl
Plugin component of Resource Pack distributed with modern Skyrim/Creation Kit ecosystem.

### _ResourcePack.bsa
Archive component containing Resource Pack assets.

### MarketplaceTextures.bsa
Creations-era Bethesda resource archive supplied as part of updated creator ecosystem.

### ESL range expansion
2023 Creations update doubled light-plugin local record capacity to 4096 records, changing older guidance that assumed the narrower pre-update range.

### ESL compliance indicator
Modern Creation Kit titlebar/status can indicate whether active plugin is ESL compliant based on last save.

### Show Edited Forms Only
Modern CK Object Window filtering option introduced in Creations-era update.

### Modified Date column
CK Data menu enhancement for plugin metadata.

### RoboVoice
Temporary voice-line generation tool included with modern CK update for authoring/testing.

### LipFuzer
Tool bundled with modern CK for creating game-ready FUZ files.

### 64-bit LipGenerator
Updated lip-generation tool included with modern CK.

## Publishing

### Bethesda.net login
CK authentication required to upload through official platform.

### Upload Plugin and Archives
CK publishing command packaging/uploading plugin/assets to Bethesda.net.

### Create New Mod
Publishing flow requiring title, description, category and target platform.

### Platform target
PC/Xbox/PlayStation destination with different content/technical restrictions.

### Console test
Testing uploaded Creation on actual target console because PC CK validation cannot prove console compatibility.

### Binary pending
Bethesda publishing state where uploaded binary processing has not completed.

### Publishing metadata
Title, overview, description, category, screenshots and platform data attached to Creation.

### Storage/unpack limit
Console constraints where downloaded archive may need additional free space during installation/unpacking.

## Load-order interaction

### Creations load order
Ordering controlled through in-game Creations menu.

### External mod-manager load order
MO2/Vortex/LOOT-managed plugin ordering on PC.

### Dual-management hazard
Using in-game Creations manager and external manager can change plugins/files outside expected external profile state. Avoid uncontrolled simultaneous management.

### Creation list mutation
Opening/updating Creations can download/update/remove content or alter load order; preserve reproducible modlists by controlling this behavior.

### Missing Creation dependency
Plugin/save references official Creation master not present on user's installation.

## Platform restrictions

### Xbox Creation
Console mod allowing Bethesda-permitted assets/scripts/plugins but no arbitrary native SKSE DLL execution.

### PlayStation Creation
More restrictive asset/mod platform limitations; exact current policy/platform capabilities should be checked before authoring.

### PC Creation
Bethesda-hosted PC content still differs from Nexus/manual distribution in native DLL/tool ecosystem support and packaging workflow.

### Cross-platform Creation
Content built to function on multiple Bethesda-supported platforms within each platform's limitations.

## Diagnostic rules

1. Distinguish executable runtime version from Anniversary Upgrade/Creation ownership.
2. Record exact official Creation files and versions used as masters.
3. Treat Bethesda content updates as dependency updates requiring patch validation.
4. On PC modlists, avoid letting in-game manager silently mutate an externally managed setup.
5. Old ESL-capacity guidance may be outdated after Creations-era ESL range changes; scope advice to runtime/format generation.
6. Creation Kit publishing success does not prove console runtime compatibility.
7. Resource Pack is a creator dependency/resource and should be explicitly recorded if a mod uses it.

## Sources

- Bethesda Creations announcement: https://bethesda.net/en-US/news/build-share-and-find-creations-skyrim-special-edition
- Creations update patch notes: https://bethesda.net/en-US/news/the-elder-scrolls-v-skyrim-special-edition-creations-update-patch-notes
- Bethesda upload instructions: https://help.bethesda.net/app/answers/detail/a_id/36342
- Bethesda installation/load-order support: https://help.bethesda.net/app/answers/detail/a_id/36360
- Bethesda modding guidelines: https://help.bethesda.net/app/answers/detail/a_id/51731
