# Skyrim Modding Terminology — Books, Notes, Read State, and Text Content

Imported: 2026-09-24
Status: sourced deep-ingestion pass 20

## Book records

### Book / BOOK
Game form representing readable book/note/journal/spell tome/skill book.

### Book text
Rich-text content stored/localized in BOOK record.

### Book title
Display name.

### Book model
Inventory/world NIF.

### Inventory art
UI item presentation resource as determined by model/interface.

### Teaches skill
BOOK behavior increasing one associated skill on first qualifying read.

### Teaches spell
BOOK behavior granting a spell on read, making it a spell tome.

### Cannot be taken
Book/reference interaction configuration where it may be read but not picked up depending on base/reference/script setup.

### Note
Book-form convention using note/paper model/text and usually no skill/spell teaching.

### Journal
Narrative BOOK with text, potentially quest item.

### Spell tome
Book that teaches configured SPEL and is generally consumed/removed by vanilla learning flow.

### Skill book
Book associated with one ActorValue skill increase.

## Read state

### OnRead
Papyrus event fired when Book object is read.

### Read
Runtime state indicating player has opened/read book.

### PlayerKnows
Book/SKSE API testing whether book's taught spell/skill knowledge is already known where applicable.

### Skill-book learned state
Per-save/player behavior ensuring same skill book isn't used indefinitely for repeated skill gain.

### Spell-tome known state
If player already knows spell, UI/use behavior changes; modded systems may prevent consumption or change prompt.

### Read tracking
Quest/script/framework stores which BOOK forms the player has read.

### Library collection
Mod tracks read/owned books by FormID/EditorID and organizes them.

### Book pickup vs read
Taking an item and opening its text are separate events/actions.

### Read-or-take interaction
Contextual activation framework lets one input read while alternate input takes item.

### DAK read/take
Dynamic Activation Key integration commonly maps default activate to one book action and modifier to another.

## Text formatting

### Book HTML-like markup
Skyrim book text supports limited markup/layout tags interpreted by book UI.

### Page break
Markup/control splitting content across book pages.

### Font tag
Markup selecting available book font/style.

### Alignment
Left/center/right text layout depending on supported markup.

### Inline image
Book/interface markup can embed supported texture/image resources in some authoring workflows.

### Localization
BOOK title/text can be stored in STRINGS/DLSTRINGS/ILSTRINGS depending on field/plugin localization.

### Dynamic text replacement
Quest text replacement tokens or DSD/runtime string systems can affect displayed text depending on field/path.

## Quest integration

### Quest item book
Book reference/item protected from dropping/removal while quest marks it essential/quest item.

### Quest alias book
Book held in alias for tracking/objective/location.

### OnRead stage
Book script advances quest when read.

### Read objective
Quest objective completed by reading book.

### Courier note
BOOK delivered through courier quest/inventory event.

### Journal fragment
Book used to communicate lore/quest state without dialogue.

### Unique placed book
Specific REFR of BOOK whose location matters to quest.

## Libraries and shelves

### Bookshelf
Container/trigger/script system placing book world models on shelf.

### Bookshelf capacity
Finite marker slots; container may hold more items than visual positions if scripts/patches break assumptions.

### Book marker
Placed slot/marker used by shelf system.

### Book collection display
Museum/library mod stores books and generates visible copies/displays.

### Read/unread icon
UI framework can add icon/classification based on read state, often requiring native/interface data.

## Failure modes

### Blank book
Missing localized string/table or malformed text.

### Missing pages
Markup/page breaks/text truncation/unsupported formatting.

### Tome doesn't teach
SPEL link/known state/script/framework conflict.

### Skill book repeats
Custom script bypasses ordinary one-time behavior or read state not persisted.

### Quest doesn't advance
OnRead script/alias/reference mismatch or player read different copy than tracked reference.

### Shelf swallows book
Bookshelf trigger/container/marker script state inconsistent.

### Can't drop book
Quest-item/alias state still active.

## Diagnostic rules

1. Separate Book base data from placed reference/quest alias.
2. Reading and taking are distinct interactions/events.
3. Blank text in localized mod often means missing string resources, not bad NIF.
4. Spell tome/skill book behavior has engine data plus possible script/runtime changes.
5. Established save preserves learned/read/quest state.
6. Bookshelf bugs require entire linked system, not just BOOK records.
7. Runtime DSD translations can change text even when xEdit shows original embedded/localized string.

## Sources

- Creation Kit Wiki Book Script / SKSE Script Objects: https://ck.uesp.net/wiki/Category:SKSE_Script_Objects
- Creation Kit Wiki Papyrus event listing including OnRead: https://ck.uesp.net/wiki/Category:Scripting
- Dynamic String Distributor tooling and Book translations: DSD current ecosystem
