# Task Breakdown: 3-netscape-parser

**Feature:** Netscape HTML Parser & Exporter
**Plan:** `.specify/specs/3-netscape-parser/plan.md`
**Branch:** `3-netscape-parser`
**Created:** 2026-03-17

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 11 |
| Phases | 4 |
| Critical Path | 1.1 → 1.2 → 2.1 → 2.2 → 3.1 → 3.2 → 4.1 → 4.2 |

## User Story → Task Mapping

| User Story | Tasks |
|------------|-------|
| US-1: Parse Bookmark Export | 2.1, 2.2 (parser) |
| US-2: Export Clean Bookmarks | 3.1, 3.2 (exporter) |
| US-3: Roundtrip Without Data Loss | 4.1, 4.2 (roundtrip + real files) |
| US-4: Handle Messy Real-World Files | 2.1, 2.2 (edge case tests), 4.2 (real files) |
| US-5: Format Detection | 1.1, 1.2 (detect_format) |

---

## Phase 1: Format Detection & Test Fixtures

### Task 1.1: Format Detection & Fixtures — Tests
**Status:** 🟡 Ready
**Effort:** 45 minutes
**Dependencies:** None

**Description:**
Create test fixtures (small handcrafted bookmark files) and write tests for format detection. Tests MUST FAIL before implementation.

**Fixtures to create in `tests/fixtures/`:**
- `sample_simple.html` — 3 folders, 5 bookmarks, standard format
- `sample_empty.html` — valid Netscape header, zero bookmarks
- `sample_entities.html` — titles with `&amp;`, `&lt;`, unicode, emoji
- `sample_nested.html` — 5+ levels of folder nesting
- `sample_no_href.html` — includes one `<A>` without HREF attribute
- `sample_bom.html` — UTF-8 BOM before DOCTYPE

**Test cases for `detect_format`:**
- Netscape HTML file → returns "netscape"
- JSON file (any content starting with `{`) → returns "unknown"
- Plain text file → returns "unknown"
- Empty file → returns "unknown"
- Non-existent file → raises FileNotFoundError
- File with UTF-8 BOM + Netscape header → returns "netscape"

**Acceptance Criteria:**
- [ ] 6 fixture files created in `tests/fixtures/`
- [ ] All detect_format test cases written in `tests/test_parsers.py`
- [ ] Tests run and ALL FAIL (no implementation yet)

---

### Task 1.2: Format Detection — Implementation
**Status:** 🔴 Blocked by 1.1
**Effort:** 20 minutes
**Dependencies:** Task 1.1

**Description:**
Implement `detect_format(file_path: str) -> str` in `src/bookmark_cleaner/parsers/__init__.py`.

**Implementation:**
- Read first 1000 bytes of file
- Strip UTF-8 BOM if present
- Check for `NETSCAPE-Bookmark-file-1` in content
- Return "netscape" or "unknown"
- Let FileNotFoundError propagate naturally

**Acceptance Criteria:**
- [ ] All detect_format tests from 1.1 PASS
- [ ] mypy --strict passes

---

## Phase 2: Netscape Parser

### Task 2.1: Parser — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 1 hour
**Dependencies:** Task 1.2 (needs fixtures and parsers package to exist)

**Description:**
Write tests for `parse_netscape()` using the fixtures from Task 1.1. Tests MUST FAIL before implementation.

**Test cases — basic parsing (`sample_simple.html`):**
- Returns a BookmarkTree with source_format="netscape"
- Correct number of top-level folders
- Correct total bookmark count (use `collect_bookmarks`)
- Bookmark URLs extracted correctly
- Bookmark titles extracted correctly
- Bookmark ADD_DATE extracted as int (not string)
- Bookmark ICON data preserved
- Folder names extracted correctly
- Folder ADD_DATE and LAST_MODIFIED extracted as int
- PERSONAL_TOOLBAR_FOLDER stored in folder attrs tuple
- Ordering of bookmarks within a folder matches file order

**Test cases — edge cases:**
- `sample_empty.html` → BookmarkTree with empty root, zero bookmarks
- `sample_nested.html` → all nesting levels preserved (verify deepest folder reachable)
- `sample_entities.html` → `&amp;` decoded to `&` in titles, emoji preserved
- `sample_no_href.html` → bookmark without HREF is skipped, others parsed
- `sample_bom.html` → parses normally despite BOM
- Bookmark with empty title → empty string (not None, not skipped)

**Acceptance Criteria:**
- [ ] All parser test cases written in `tests/test_parsers.py`
- [ ] Tests use fixtures from Task 1.1
- [ ] Tests import from `bookmark_cleaner.parsers` and `bookmark_cleaner.tree`
- [ ] Tests run and ALL FAIL

---

### Task 2.2: Parser — Implementation
**Status:** 🔴 Blocked by 2.1
**Effort:** 1 hour
**Dependencies:** Task 2.1

**Description:**
Implement `parse_netscape(file_path: str) -> BookmarkTree` in `src/bookmark_cleaner/parsers/netscape.py`.

**Implementation details:**
- `_MutableFolder` class with mutable lists for children and bookmarks
- `_NetscapeHandler(HTMLParser)` with:
  - `folder_stack: list[_MutableFolder]`
  - `_pending_folder_name: str | None`
  - `_pending_folder_attrs: dict | None`
  - `_current_bm_attrs: dict | None`
  - `_current_bm_title: str`
- `handle_starttag`: on `h3` set pending folder attrs; on `a` set current bookmark attrs
- `handle_data`: accumulate text to pending folder name or current bookmark title
- `handle_endtag`: on `</h3>` create folder and push to stack; on `</a>` create bookmark and add to top of stack; on `</dl>` pop stack (guard: never pop past root)
- `_freeze(mutable_folder) -> FolderNode`: recursive conversion to immutable tree
- Known attrs extraction: HREF→url, ADD_DATE→add_date(int), ICON→icon, LAST_MODIFIED→last_modified(int)
- Open file with `encoding='utf-8-sig'`

**Acceptance Criteria:**
- [ ] All parser tests from 2.1 PASS
- [ ] mypy --strict passes on parsers/netscape.py

---

## Phase 3: Netscape Exporter

### Task 3.1: Exporter — Tests
**Status:** 🔴 Blocked by 2.2
**Effort:** 45 minutes
**Dependencies:** Task 2.2 (need working parser to create test trees, and to verify roundtrip)
**Parallel with:** None (depends on parser)

**Description:**
Write tests for `export_netscape()`. Tests MUST FAIL before implementation.

**Test cases:**
- Export simple tree → output starts with `<!DOCTYPE NETSCAPE-Bookmark-file-1>`
- Export simple tree → output contains META charset tag
- Bookmarks have HREF attribute in output
- Bookmarks have ADD_DATE attribute in output
- Bookmarks have ICON attribute in output (when non-empty)
- Folders have ADD_DATE and LAST_MODIFIED attributes in output
- Extra attrs (e.g., PERSONAL_TOOLBAR_FOLDER) appear in folder output
- 4-space indentation: root children at 4 spaces, grandchildren at 8 spaces
- Special characters escaped: `&` → `&amp;` in titles
- Special characters escaped: `<` → `&lt;` in titles
- Export to a new file (verify file is created at given path)
- Export does NOT modify any input file (verify with checksum if practical)
- Empty tree → valid Netscape HTML with just header and empty DL

**Acceptance Criteria:**
- [ ] All exporter test cases written in `tests/test_parsers.py`
- [ ] Tests create BookmarkTree/FolderNode/BookmarkNode directly and export
- [ ] Tests verify output content via reading the written file
- [ ] Tests use `tmp_path` pytest fixture for output files
- [ ] Tests run and ALL FAIL

---

### Task 3.2: Exporter — Implementation
**Status:** 🔴 Blocked by 3.1
**Effort:** 45 minutes
**Dependencies:** Task 3.1

**Description:**
Implement `export_netscape(tree: BookmarkTree, file_path: str) -> None` in `src/bookmark_cleaner/parsers/netscape.py`.

**Implementation details:**
- Write standard Netscape header (DOCTYPE, META, TITLE, H1)
- Recursive `_write_folder(folder, depth, lines)` function
- For each folder: write `<DT><H3 attrs>name</H3>`, `<DL><p>`, recurse children, write bookmarks, write `</DL><p>`
- For each bookmark: write `<DT><A HREF="url" ADD_DATE="date" ICON="icon" ...attrs>title</A>`
- Use `html.escape()` on title and folder name text
- Reconstruct attrs string: known fields first, then extras from attrs tuple
- Skip ICON attribute if empty (don't write `ICON=""`)
- Open output file with `encoding='utf-8'`, `newline='\n'`
- Join lines with `\n` and write

**Acceptance Criteria:**
- [ ] All exporter tests from 3.1 PASS
- [ ] mypy --strict passes

---

## Phase 4: Roundtrip, Real Files & Quality Gate

### Task 4.1: Roundtrip Tests
**Status:** 🔴 Blocked by 3.2
**Effort:** 30 minutes
**Dependencies:** Task 3.2

**Description:**
Write roundtrip tests: parse → export → reparse → compare. Tests MUST FAIL first, then pass after any needed fixes.

**Test cases:**
- Roundtrip `sample_simple.html` → trees_equal(original, reparsed, ignore_metadata=True)
- Roundtrip `sample_simple.html` → same URL count before and after
- Roundtrip `sample_simple.html` → same folder count before and after
- Roundtrip `sample_entities.html` → entities survive roundtrip
- Roundtrip `sample_nested.html` → deep nesting preserved

**Acceptance Criteria:**
- [ ] All roundtrip tests written and PASSING
- [ ] Uses `tmp_path` for intermediate export file
- [ ] Uses `trees_equal` with `ignore_metadata=True` for comparison
- [ ] Uses `collect_urls` and `count_items` for count verification

---

### Task 4.2: Real-File Integration Tests
**Status:** 🔴 Blocked by 4.1
**Effort:** 30 minutes
**Dependencies:** Task 4.1

**Description:**
Test parser and roundtrip against the 4 real-world bookmark files in the project root.

**Test cases:**
- Parse `favorites_3_17_26.html` → 2503 bookmarks (verified by collect_bookmarks count)
- Parse `bookmarks_1_23_26.html` → count matches `grep -c '<DT><A ' file`
- Roundtrip `favorites_3_17_26.html` → same unique URL count (collect_urls)
- Roundtrip `bookmarks_1_23_26.html` → same unique URL count
- Both parse without raising any exception

**Acceptance Criteria:**
- [ ] All real-file tests written and PASSING
- [ ] Tests skip gracefully if fixture files are missing (pytest.mark.skipif)
- [ ] URL count assertions match verified values

---

### Task 4.3: Package Exports & Quality Gate
**Status:** 🔴 Blocked by 4.2
**Effort:** 20 minutes
**Dependencies:** Task 4.2

**Description:**
Update `bookmark_cleaner/__init__.py` to export parser functions. Run full quality gate.

**Implementation:**
- Add `detect_format`, `parse_netscape`, `export_netscape` to `__init__.py` exports
- Verify all imports work: `from bookmark_cleaner import parse_netscape`

**Acceptance Criteria:**
- [ ] `from bookmark_cleaner import parse_netscape, export_netscape, detect_format` works
- [ ] `pytest --cov=bookmark_cleaner --cov-report=term-missing` shows 80%+ coverage
- [ ] `mypy --strict src/bookmark_cleaner/` passes with zero errors
- [ ] `ruff check src/ tests/` passes
- [ ] All tests pass (Feature 1 + Feature 3)

---

## Dependency Graph

```
Task 1.1 (detect tests + fixtures)
    │
    ▼
Task 1.2 (detect impl)
    │
    ▼
Task 2.1 (parser tests)
    │
    ▼
Task 2.2 (parser impl)
    │
    ▼
Task 3.1 (exporter tests)
    │
    ▼
Task 3.2 (exporter impl)
    │
    ▼
Task 4.1 (roundtrip tests)
    │
    ▼
Task 4.2 (real-file tests)
    │
    ▼
Task 4.3 (package + quality gate)
```

This feature is strictly sequential — each phase depends on the previous (exporter needs parser, roundtrip needs both, real files need roundtrip).

## Critical Path

1.1 → 1.2 → 2.1 → 2.2 → 3.1 → 3.2 → 4.1 → 4.2 → 4.3

## Quality Gates

- [x] TDD enforced: every impl task blocked by its test task
- [ ] Coverage gate at Task 4.3: 80%+ required
- [ ] Type safety gate at Task 4.3: mypy strict, zero errors
- [ ] Lint gate at Task 4.3: ruff clean
- [ ] Real-file validation at Task 4.2: known bookmark counts match

## Next Steps

1. Review task breakdown
2. Run `/speckit-implement` to begin TDD execution
