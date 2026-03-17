# Implementation Plan: 3-netscape-parser

**Feature:** Netscape HTML Parser & Exporter
**Specification:** `.specify/specs/3-netscape-parser/spec.md`
**Branch:** `3-netscape-parser`
**Created:** 2026-03-17

## Executive Summary

Implement a Netscape bookmark HTML parser using stdlib `html.parser.HTMLParser` and a corresponding exporter that produces valid, browser-importable HTML. Add format auto-detection. Validate with roundtrip tests against 4 real-world bookmark files.

Three source files in a `parsers/` package, approximately 250 lines total. Zero external dependencies.

## Architecture Overview

```
src/bookmark_cleaner/
    parsers/
        __init__.py      # detect_format(), re-exports parse_netscape/export_netscape
        netscape.py      # NetscapeParser class, parse_netscape(), export_netscape()
```

Data flow:
```
File on disk → parse_netscape(path) → BookmarkTree
BookmarkTree → export_netscape(tree, path) → File on disk
```

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| HTML parsing | `html.parser.HTMLParser` | Stdlib, zero deps, handles malformed HTML (Constitution Art. VI) |
| Entity decoding | `convert_charrefs=True` (default) | Auto-decodes `&amp;` etc. in handle_data |
| Entity encoding | `html.escape()` | Stdlib, encodes `& < > "` for output |
| File I/O | `open()` with `encoding='utf-8'` | Handles BOM via `encoding='utf-8-sig'` |

See `research.md` for detailed decision rationale.

## Technical Decisions

### TD-1: HTMLParser with Folder Stack

**Context:** Need to build the tree from event-driven callbacks.
**Chosen:** Maintain a mutable `folder_stack: list[_MutableFolder]` during parsing. When `<h3>` is encountered, start accumulating folder name. On `</h3>`, create a folder and push it onto the stack. On `</dl>`, pop the stack. On `<a>`, start accumulating bookmark data. On `</a>`, add bookmark to current folder (top of stack).
**Key insight:** Use mutable intermediate objects (`_MutableFolder` with lists) during parsing, then freeze into immutable `FolderNode`/`BookmarkNode` at the end. This follows Constitution Art. VII exception: "Internal builder patterns during parsing may use mutable state, but MUST produce an immutable tree as output."
**Tradeoffs:** Two representations (mutable during parse, immutable after). Clean boundary.

### TD-2: Known Attribute Extraction

**Context:** `<A>` and `<H3>` tags have many attributes. Some map to model fields, rest go to `attrs`.
**Chosen:** Define known attribute sets:
- BookmarkNode known: `HREF` → url, `ADD_DATE` → add_date (int), `ICON` → icon
- FolderNode known: `ADD_DATE` → add_date (int), `LAST_MODIFIED` → last_modified (int)
- Everything else → attrs tuple (preserves PERSONAL_TOOLBAR_FOLDER, SHORTCUTURL, etc.)
**Tradeoffs:** Hardcoded list of known attrs. Small and stable — the Netscape format hasn't changed in decades.

### TD-3: UTF-8 BOM Handling

**Context:** Some Windows-exported files start with a UTF-8 BOM (`\ufeff`).
**Chosen:** Open files with `encoding='utf-8-sig'` which transparently strips the BOM if present, and reads normally if not.
**Tradeoffs:** None. `utf-8-sig` is strictly better than `utf-8` for reading.

### TD-4: Exporter Indentation

**Context:** Need consistent, readable output with proper nesting.
**Chosen:** Recursive function that takes a `FolderNode` and current depth. Each depth level adds 4 spaces. Bookmarks and folder headers at the same depth get the same indentation. Standard Netscape format:
```html
    <DT><H3 ADD_DATE="...">Folder Name</H3>
    <DL><p>
        <DT><A HREF="..." ADD_DATE="...">Title</A>
    </DL><p>
```
**Tradeoffs:** None. This matches what browsers expect.

### TD-5: Mutable-to-Immutable Conversion

**Context:** Parser uses mutable lists during construction. Must convert to frozen dataclasses.
**Chosen:** A `_freeze()` function that recursively converts `_MutableFolder` tree to `FolderNode` tree. Called once at the end of parsing. This is the single point where immutable tree is created.
**Tradeoffs:** One extra pass over the tree. Negligible for bookmark-scale data.

## Implementation Phases

### Phase A: Format Detection (parsers/__init__.py)

Implement `detect_format(file_path: str) -> str`:
- Read first 1000 bytes
- Check for `<!DOCTYPE NETSCAPE-Bookmark-file-1>` → "netscape"
- Return "unknown" otherwise
- Handle file-not-found and permission errors

**Estimated size:** ~20 lines
**Dependencies:** None

### Phase B: Netscape Parser (parsers/netscape.py)

Implement `parse_netscape(file_path: str) -> BookmarkTree`:
- `_MutableFolder` and `_NetscapeHandler(HTMLParser)` internal classes
- State: folder_stack, pending_folder_name, current_bookmark_attrs, current_bookmark_title
- Event handlers: handle_starttag, handle_data, handle_endtag
- `_freeze()` to convert mutable tree to immutable BookmarkTree
- Open with `utf-8-sig` encoding

**Estimated size:** ~120 lines
**Dependencies:** Feature 1 models

### Phase C: Netscape Exporter (parsers/netscape.py)

Implement `export_netscape(tree: BookmarkTree, file_path: str) -> None`:
- Write standard Netscape header
- Recursive `_write_folder()` function with depth tracking
- HTML entity escaping for titles and folder names via `html.escape()`
- Reconstruct attribute strings from model fields + attrs tuple
- Write with `encoding='utf-8'`, newline='\n'

**Estimated size:** ~80 lines
**Dependencies:** Feature 1 models

### Phase D: Package Init (parsers/__init__.py)

Re-export public API: `detect_format`, `parse_netscape`, `export_netscape`
Update `bookmark_cleaner/__init__.py` to expose parser functions.

**Estimated size:** ~15 lines
**Dependencies:** Phase A, B, C

## Testing Strategy

**Framework:** pytest
**Coverage target:** 80%+
**Approach:** TDD — tests first

### Test Files

```
tests/
    test_parsers.py          # detect_format, parse_netscape, export_netscape
    fixtures/                # Test bookmark files
        sample_simple.html   # Small handcrafted file for unit tests
        sample_empty.html    # Valid header, no bookmarks
        sample_entities.html # Titles with &amp; &lt; unicode emoji
        sample_nested.html   # 5+ nesting levels
        sample_no_href.html  # Malformed bookmark without HREF
```

### test_parsers.py — Test Cases

**detect_format:**
- Netscape file → "netscape"
- JSON file → "unknown"
- Empty file → "unknown"
- Non-existent file → raises FileNotFoundError
- File with UTF-8 BOM + Netscape header → "netscape"

**parse_netscape — basic:**
- Parse simple file → correct bookmark count
- Parse simple file → correct folder structure
- Bookmark URLs extracted correctly
- Bookmark titles extracted correctly
- Bookmark ADD_DATE extracted as int
- Bookmark ICON preserved
- Folder names extracted correctly
- Folder ADD_DATE and LAST_MODIFIED extracted as int
- PERSONAL_TOOLBAR_FOLDER stored in folder attrs

**parse_netscape — edge cases:**
- Empty file (header only) → empty root folder
- Bookmarks outside any folder → on root's bookmarks
- Deep nesting (5+ levels) → all levels preserved
- HTML entities in titles decoded (`&amp;` → `&`)
- Unicode titles (Japanese, emoji) preserved
- Empty bookmark title → empty string
- Missing HREF → bookmark skipped
- Large ICON data → not truncated

**parse_netscape — real files:**
- Parse `favorites_3_17_26.html` → 2503 bookmarks
- Parse `bookmarks_1_23_26.html` → count matches grep

**export_netscape:**
- Export simple tree → valid Netscape HTML format
- Output starts with DOCTYPE header
- Bookmarks have HREF, ADD_DATE, ICON attributes
- Folders have ADD_DATE, LAST_MODIFIED attributes
- 4-space indentation per depth level
- Special characters escaped in titles (`&` → `&amp;`)
- Extra attrs preserved in output

**roundtrip:**
- Parse → export → reparse → trees_equal (ignore_metadata) for handcrafted fixture
- Parse → export → reparse → same URL count for real files
- Parse → export → reparse → same folder count for real files

## Security Considerations

- File paths provided by user — no path traversal risk since we only read/write specified paths
- No execution of HTML content — HTMLParser does not execute scripts
- No network access
- Large icon data could consume memory — acceptable per Constitution Art. V (no perf SLAs, files under 10MB)

## Performance Strategy

No optimization needed (Constitution Art. V). HTMLParser is efficient. Real files (2500 bookmarks) parse in milliseconds.

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Browser-specific HTML variations | Medium | Medium | Test against real exports from Chrome, Edge, Firefox. HTMLParser handles variations gracefully. |
| `handle_data` called multiple times per text node | Medium | High | Accumulate text with `+=`, don't overwrite. The v2 script had this right. |
| DL/H3 nesting inconsistency across browsers | Low | Medium | Pop stack on `</dl>`, not on next `<h3>`. Defensive: never pop past root. |
| Encoding issues on Windows | Low | Low | Use `utf-8-sig` to handle BOM. |

## Constitutional Compliance

- [x] **Art. I (Lightweight):** Zero dependencies. Stdlib HTMLParser + html.escape.
- [x] **Art. II (Test-First):** Test cases defined. TDD workflow. Real-file integration tests.
- [x] **Art. III (Simplicity):** 3 files in parsers/ package. ~250 lines total. Mutable builder → immutable output.
- [x] **Art. IV (Non-Destructive):** Exporter writes to specified output path. Never touches input file.
- [x] **Art. V (No Perf SLAs):** No optimization.
- [x] **Art. VI (Tech Constraints):** HTMLParser (stdlib). No BeautifulSoup, no lxml.
- [x] **Art. VII (Immutable Model):** Mutable state during parsing (documented exception). Produces immutable BookmarkTree.
- [x] **Art. VIII (Browser Compat):** Entity escaping. Standard Netscape format. Tested against real files.

No exceptions needed.

## Next Steps

1. Run `/speckit-tasks` to generate task breakdown
2. Implement via TDD (`/speckit-implement`)
