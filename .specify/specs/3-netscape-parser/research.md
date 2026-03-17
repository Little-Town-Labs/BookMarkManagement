# Technology Research: 3-netscape-parser

## Decision 1: Parsing Approach

**Context:** Need to parse Netscape bookmark HTML into the immutable tree model.

**Options Considered:**

1. **`html.parser.HTMLParser`** — Stdlib event-driven parser. Handles malformed HTML. Calls `handle_starttag`, `handle_data`, `handle_endtag` for each element. No dependencies.

2. **Regex line-by-line** — Pattern match `<DT><A HREF=...>` and `<DT><H3...>` lines. Simpler mental model. Fragile on multi-line attributes or unexpected whitespace.

3. **BeautifulSoup** — Full DOM parser. Very robust. But adds a heavy dependency (~500KB) and is overkill for the structured Netscape format. Prohibited by Constitution Art. VI.

4. **lxml** — C-extension XML/HTML parser. Fast and robust. But requires C compiler for installation. Prohibited by Constitution Art. VI.

**Chosen:** `html.parser.HTMLParser`
**Rationale:** Stdlib (zero deps, Constitution Art. I and VI), event-driven (low memory), handles malformed HTML gracefully. The existing v2 script (`cleanup_bookmarks_v2.py`) already demonstrates this works well with real bookmark files. Key insight from v2: push folder onto stack at `</h3>` end tag, not during `handle_data`, to handle multi-word folder names that arrive as multiple `handle_data` calls.
**Tradeoffs:** Requires manual state management (folder stack, pending data). More code than regex but far more robust.

## Decision 2: State Machine Design

**Context:** HTMLParser is event-driven. Need to track which element we're inside to correctly assign text content.

**Options Considered:**

1. **Boolean flags** (`in_h3`, `in_a`) — Simple. Used by existing v2 script. Gets messy with more states.

2. **Enum state machine** — Explicit states: IDLE, IN_FOLDER_TITLE, IN_BOOKMARK_TITLE. Clearer. Slightly more code.

3. **Pending object pattern** — Set `pending_folder_name` or `current_bookmark` to non-None when inside an element. Check in `handle_data`. Used by v2 script.

**Chosen:** Pending object pattern (matching v2 script)
**Rationale:** Already proven to work with real files. Handles the key subtleties: `handle_data` can be called multiple times for a single text node (HTMLParser splits on entities), so we need to accumulate text. Using `pending_folder_name: str | None` and `current_attrs: dict | None` is simple and explicit.
**Tradeoffs:** Slightly implicit (None checks) vs explicit state enum. Acceptable for this small parser.

## Decision 3: Attribute Handling

**Context:** Need to capture all attributes from `<A>` and `<H3>` tags, mapping known ones (HREF, ADD_DATE, ICON) to model fields and storing the rest in the `attrs` tuple.

**Options Considered:**

1. **Extract known attrs, store rest in attrs** — HREF→url, ADD_DATE→add_date (int), ICON→icon, everything else→attrs tuple. Clean separation.

2. **Store everything in attrs, extract at access time** — Simpler parser. But means URL is buried in attrs, which contradicts the model design.

**Chosen:** Option 1: Extract known attrs, store rest
**Rationale:** The model already has explicit fields for url, title, add_date, icon. The parser should populate them directly. Remaining attrs (SHORTCUTURL, PERSONAL_TOOLBAR_FOLDER, LAST_MODIFIED, etc.) go into the attrs tuple. This keeps the model clean and avoids post-parsing transformation.
**Tradeoffs:** Parser has to know which attrs are "known" vs "extra". Small list, manageable.

## Decision 4: File Layout

**Context:** Where to put parser, exporter, and format detection code.

**Options Considered:**

1. **Single file `parsers.py`** — Parser + exporter + detection in one file. Simple.

2. **`parsers/` package** — Separate modules per format. More structure for when Chrome/Firefox parsers arrive in Feature 8.

3. **Two files: `parser.py` + `exporter.py`** — Separate concerns. But adds files that are tightly related.

**Chosen:** `parsers/` package with `netscape.py` and `__init__.py`
**Rationale:** Feature 8 will add `chrome_json.py` and `firefox_json.py` to this same package. Better to set up the structure now. The `__init__.py` re-exports the public API (`parse_netscape`, `export_netscape`, `detect_format`). Format detection lives in `__init__.py` since it spans formats. Each format module contains both parser and exporter since they're tightly coupled. Stays within Constitution Art. III limit of 3 directory levels (`src/bookmark_cleaner/parsers/`).
**Tradeoffs:** Slightly more structure than needed for just Netscape. But Feature 8 is planned, and the package is only 2 files for now.

## Decision 5: Entity Handling

**Context:** Bookmark titles contain HTML entities (`&amp;`, `&lt;`, `&quot;`). Model stores decoded text. Exporter must re-encode.

**Options Considered:**

1. **Let HTMLParser decode automatically** — HTMLParser calls `handle_entityref` and `handle_charref`, but with `convert_charrefs=True` (default since Python 3.4), entities are decoded before reaching `handle_data`. Exporter uses `html.escape()` for encoding.

2. **Manual decode/encode** — Use `html.unescape()` in parser, `html.escape()` in exporter.

**Chosen:** Option 1: HTMLParser auto-decodes with `convert_charrefs=True`
**Rationale:** Zero extra code in the parser. `convert_charrefs=True` is the default since Python 3.4 and handles all standard HTML entities. Exporter uses `html.escape()` (stdlib) for re-encoding. Clean separation: model stores real text, exporter handles encoding.
**Tradeoffs:** None. This is the intended usage of HTMLParser.
