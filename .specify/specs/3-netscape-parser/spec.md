# Feature Specification: Netscape HTML Parser & Exporter

**Feature Number:** 3
**Branch:** 3-netscape-parser
**Status:** Draft
**Created:** 2026-03-17
**Last Updated:** 2026-03-17

## Overview

The Netscape Bookmark HTML format is the universal bookmark exchange format supported by every major browser (Chrome, Firefox, Edge, Brave, Safari, Opera). This feature provides the ability to read a Netscape bookmark file into the immutable tree model (Feature 1) and write a tree back to a valid, well-formatted Netscape HTML file.

This is the primary I/O path for bookmark-cleaner — the vast majority of users will export bookmarks from their browser as HTML, process them with this tool, and import the cleaned HTML back into a browser. Correctness and browser compatibility are paramount.

## User Stories

### User Story 1: Parse Bookmark Export
**As a** user who exported bookmarks from a browser
**I want** the tool to read my bookmark HTML file into memory
**So that** it can analyze and clean up my bookmarks

**Acceptance Criteria:**
- [ ] The parser reads a standard Netscape bookmark HTML file and produces a BookmarkTree
- [ ] Every bookmark URL, title, add date, and icon is captured
- [ ] Every folder name, nesting level, and metadata (add date, last modified, toolbar flag) is captured
- [ ] The folder hierarchy in the tree matches the nesting in the file
- [ ] The parser auto-detects Netscape format (vs Chrome JSON, Firefox JSON) based on file content

**Priority:** High

### User Story 2: Export Clean Bookmarks
**As a** user who has cleaned their bookmarks
**I want** the tool to write the result as a valid HTML file
**So that** I can import it into any browser without errors

**Acceptance Criteria:**
- [ ] The exporter produces valid Netscape Bookmark HTML that imports into Chrome, Firefox, Edge, and Brave
- [ ] All bookmark attributes (HREF, ADD_DATE, ICON) are preserved in the output
- [ ] All folder attributes (ADD_DATE, LAST_MODIFIED, PERSONAL_TOOLBAR_FOLDER) are preserved
- [ ] The output uses consistent 4-space indentation for human readability
- [ ] Special characters in titles and folder names are properly escaped as HTML entities

**Priority:** High

### User Story 3: Roundtrip Without Data Loss
**As a** user
**I want** parsing and re-exporting my file to produce an equivalent result
**So that** I can trust the tool is not silently losing or corrupting data

**Acceptance Criteria:**
- [ ] Parsing a file, then exporting it, then reparsing produces a tree with the same URLs, titles, and folder structure
- [ ] The unique URL count is identical before and after roundtrip
- [ ] Bookmark ordering within folders is preserved through roundtrip
- [ ] Folder ordering is preserved through roundtrip

**Priority:** High

### User Story 4: Handle Messy Real-World Files
**As a** user with a bookmark file that has been through multiple browser migrations
**I want** the parser to handle imperfect HTML gracefully
**So that** it doesn't crash or skip bookmarks due to minor formatting issues

**Acceptance Criteria:**
- [ ] The parser handles files from Chrome, Firefox, Edge, and Brave without errors
- [ ] Files with embedded base64 icon data (potentially very long lines) are parsed correctly
- [ ] Files with HTML entities in titles (e.g., `&amp;`, `&lt;`, `&quot;`) are decoded properly
- [ ] The parser reports a clear error message if the file is not a bookmark file at all

**Priority:** Medium

### User Story 5: Format Detection
**As a** user who may not know what format their bookmark file is in
**I want** the tool to figure it out automatically
**So that** I don't have to specify the format manually

**Acceptance Criteria:**
- [ ] A file starting with `<!DOCTYPE NETSCAPE-Bookmark-file-1>` is detected as Netscape HTML
- [ ] A JSON file with Chrome's bookmark structure is not misidentified as Netscape
- [ ] Detection is based on file content, not file extension
- [ ] If the format cannot be determined, a clear error message is shown

**Priority:** Medium

## Functional Requirements

### FR-1: Netscape HTML Parser
**Description:** The system must read a Netscape Bookmark HTML file and produce a BookmarkTree.

**Acceptance Criteria:**
- [ ] Parses the standard Netscape bookmark format as exported by Chrome, Firefox, Edge, Brave, and Safari
- [ ] Extracts bookmark attributes: HREF (url), title (text content), ADD_DATE, ICON, and any other attributes present
- [ ] Extracts folder attributes: name (H3 text content), ADD_DATE, LAST_MODIFIED, PERSONAL_TOOLBAR_FOLDER, and any other attributes present
- [ ] Builds correct parent-child folder hierarchy from DL/DT nesting
- [ ] Multiple top-level folders (e.g., Bookmarks bar, Other bookmarks, Mobile bookmarks) are represented as children of the root FolderNode
- [ ] HTML entities in text content are decoded (e.g., `&amp;` → `&`, `&lt;` → `<`)
- [ ] Takes a file path as input and returns a BookmarkTree
- [ ] Sets `source_format = "netscape"` on the returned tree

**Dependencies:** Feature 1 (Tree Model)

### FR-2: Netscape HTML Exporter
**Description:** The system must write a BookmarkTree to a valid Netscape Bookmark HTML file.

**Acceptance Criteria:**
- [ ] Produces output starting with `<!DOCTYPE NETSCAPE-Bookmark-file-1>` and the standard header
- [ ] Writes each bookmark as a `<DT><A>` element with HREF, ADD_DATE, ICON, and any stored attributes
- [ ] Writes each folder as a `<DT><H3>` element with ADD_DATE, LAST_MODIFIED, and any stored attributes
- [ ] Folder contents are wrapped in `<DL><p>` and `</DL><p>` tags
- [ ] Output uses 4-space indentation, with depth increasing for each nesting level
- [ ] Special characters in bookmark titles and folder names are escaped: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`
- [ ] Takes a BookmarkTree and a file path as input, writes the file
- [ ] The output file is a new file — the tool never overwrites the input (per Constitution Art. IV)

**Dependencies:** Feature 1 (Tree Model)

### FR-3: Format Auto-Detection
**Description:** The system must determine the format of a bookmark file from its content.

**Acceptance Criteria:**
- [ ] Returns "netscape" for files starting with `<!DOCTYPE NETSCAPE-Bookmark-file-1>`
- [ ] Returns "unknown" for files that don't match any known format
- [ ] Does not rely on file extension — only inspects content
- [ ] Reads at most the first 1000 bytes to determine format (no need to read entire file)

**Dependencies:** None

### FR-4: Roundtrip Fidelity
**Description:** Parsing a Netscape file and re-exporting it must not lose data.

**Acceptance Criteria:**
- [ ] Roundtrip preserves every unique URL
- [ ] Roundtrip preserves every bookmark title (including Unicode and special characters)
- [ ] Roundtrip preserves folder names and nesting hierarchy
- [ ] Roundtrip preserves bookmark ordering within folders
- [ ] Roundtrip preserves ADD_DATE values on bookmarks and folders
- [ ] Roundtrip preserves ICON data on bookmarks
- [ ] Roundtrip preserves PERSONAL_TOOLBAR_FOLDER attribute on folders

**Dependencies:** FR-1, FR-2

## Non-Functional Requirements

### NFR-1: Correctness
- The parser must handle the 4 real-world sample files in the project without errors
- Every bookmark in each sample file must be captured (verified by URL count)
- Expected counts: `favorites_3_17_26.html` = 2503 bookmarks, `bookmarks_1_23_26.html` ≈ 2200 bookmarks

### NFR-2: Robustness
- The parser must not crash on malformed HTML — it should extract as much data as possible and skip unparseable elements
- The parser must handle files up to 10MB without running out of memory
- The parser must handle lines exceeding 100KB (common with base64-encoded icons)

### NFR-3: Error Reporting
- If the file does not exist, the error message must include the file path
- If the file is not valid bookmark HTML, the error message must say so clearly
- If a bookmark is missing an HREF attribute, it should be skipped with a warning (not crash)

## Edge Cases & Error Handling

### Edge Case 1: File with No Bookmarks
**Situation:** Valid Netscape HTML file with the header but no bookmarks or folders
**Expected Behavior:** Returns a valid BookmarkTree with an empty root folder

### Edge Case 2: Bookmarks Outside Any Folder
**Situation:** Bookmarks at the top level, not inside any named folder
**Expected Behavior:** These bookmarks appear directly on the root FolderNode's bookmarks list

### Edge Case 3: Deeply Nested Folders (20+ levels)
**Situation:** Folders nested more than 20 levels deep
**Expected Behavior:** All nesting levels are preserved faithfully in the tree

### Edge Case 4: HTML Entities in Titles
**Situation:** Bookmark title contains `Banks &amp; Credit Cards` or `AT&amp;T`
**Expected Behavior:** The model stores the decoded text: `Banks & Credit Cards`, `AT&T`. The exporter re-encodes them on output.

### Edge Case 5: Missing or Empty Title
**Situation:** A bookmark `<DT><A HREF="..."></A>` with no text between the tags
**Expected Behavior:** The bookmark is captured with an empty string title

### Edge Case 6: Missing HREF Attribute
**Situation:** A `<DT><A>` element with no HREF (malformed)
**Expected Behavior:** The element is skipped. A warning is logged or reported.

### Edge Case 7: Very Large ICON Data
**Situation:** A bookmark with a 100KB base64-encoded ICON attribute
**Expected Behavior:** The icon data is stored in full. No truncation during parsing.

### Edge Case 8: Mixed Separators / Varied Formatting
**Situation:** File uses `<DL><p>` on one line, or split across lines, or without the `<p>`
**Expected Behavior:** The parser handles all common variations of Netscape HTML formatting

### Edge Case 9: Non-Bookmark File
**Situation:** User provides a random HTML page, a text file, or a JSON file
**Expected Behavior:** Format detection returns "unknown". Parser raises a clear error.

### Edge Case 10: UTF-8 BOM
**Situation:** File starts with a UTF-8 BOM (byte order mark) before the DOCTYPE
**Expected Behavior:** The BOM is ignored; the file is parsed normally

### Error Handling
- **File not found:** Raise an error with the file path in the message
- **Permission denied:** Raise an error indicating the file cannot be read
- **Not a bookmark file:** Raise an error indicating the format is not recognized
- **Malformed bookmark entry:** Skip the entry, continue parsing the rest of the file

## Clarifications Needed

None — the Netscape bookmark format is well-established and the requirements are clear from the real-world sample files and the PRD.

## Success Metrics

- All 4 sample files parse without errors
- URL counts match expected values (2503 for favorites_3_17_26.html, verified against grep)
- Roundtrip test passes: parse → export → reparse → trees_equal returns True (with ignore_metadata for any normalization differences)
- Exported file imports successfully into Chrome (manual verification with sample files)

## Out of Scope

- **Chrome JSON parsing** — Feature 8
- **Firefox JSON parsing** — Feature 8
- **Dead link checking** — Feature 9
- **Cleanup operations** (dedup, merge, etc.) — Feature 4
- **CLI interface** — Feature 5
- **Handling of bookmark separators** (`<HR>` elements sometimes used by Firefox) — can be added later if needed
- **Writing directly to stdout** — always writes to a file path

## References

- PRD: `PRD.md` — FR-1.1, FR-1.4, FR-2.1, FR-2.3
- Constitution: `.specify/memory/constitution.md` — Art. IV (non-destructive), Art. VI (stdlib HTMLParser), Art. VIII (browser compat)
- Roadmap: `.specify/roadmap.md` — Feature 3
- Sample files: `favorites_3_17_26.html`, `bookmarks_1_23_26.html`

---

## Validation Checklist

Before moving to planning phase:

- [x] All user stories have clear acceptance criteria
- [x] Requirements are testable and measurable
- [x] No implementation details in specification
- [x] Edge cases documented (10 cases)
- [x] Non-functional requirements defined
- [x] 0 `[NEEDS CLARIFICATION]` markers remaining
- [x] Success metrics defined
- [x] Out of scope items documented
