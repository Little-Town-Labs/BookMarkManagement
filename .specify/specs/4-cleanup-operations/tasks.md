# Task Breakdown: 4-cleanup-operations

**Feature:** Cleanup Operations Pipeline
**Plan:** `.specify/specs/4-cleanup-operations/plan.md`
**Branch:** `4-cleanup-operations`
**Created:** 2026-03-17

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 15 |
| Phases | 5 |
| Critical Path | 1.1 → 1.2 → 3.1 → 3.2 → 4.1 → 4.2 → 5.1 → 5.2 |

## User Story → Task Mapping

| User Story | Tasks |
|------------|-------|
| US-1: Remove Duplicate Bookmarks | 1.1, 1.2 (normalize), 4.1, 4.2 (dedup) |
| US-2: Merge Duplicate Folders | 3.1, 3.2 (merge_folders) |
| US-3: Unwrap Import Wrappers | 3.1, 3.2 (unwrap_wrappers) |
| US-4: Dissolve Generic Folders | 3.1, 3.2 (dissolve_generics) |
| US-5: Remove Empty Folders | 2.1, 2.2 (remove_empty_folders) |
| US-6: Sort Bookmarks and Folders | 2.1, 2.2 (sort_tree) |
| US-7: Strip Oversized Icons | 2.1, 2.2 (strip_icons) |

---

## Phase 1: Foundation Types + URL Normalization

### Task 1.1: Change, OpResult, and normalize_url — Tests
**Status:** 🟡 Ready
**Effort:** 45 minutes
**Dependencies:** None

**Description:**
Write tests for the two new data types (Change, OpResult) and the URL normalization function. Tests MUST FAIL before implementation.

**Test cases for Change and OpResult:**
- Create Change with all fields → immutable, fields accessible
- Create OpResult with tree and changes → immutable
- Change with empty details → valid
- OpResult with empty changes → valid

**Test cases for normalize_url:**
- `http://Example.COM/path` → `https://example.com/path` (scheme upgrade + host lowercase)
- `https://example.com/path/` → `https://example.com/path` (trailing slash stripped)
- `https://example.com/path?b=2&a=1` → `https://example.com/path?a=1&b=2` (query sorted)
- `http://example.com:80/path` → `https://example.com/path` (default port stripped)
- `https://example.com:443/path` → `https://example.com/path` (default port stripped)
- `https://example.com:8080/path` → `https://example.com:8080/path` (non-default port kept)
- `https://example.com/path#section` → `https://example.com/path#section` (fragment preserved)
- `https://example.com` → `https://example.com` (no trailing slash added)
- `not-a-url` → `not-a-url` (unparseable returned as-is)
- `ftp://files.example.com/doc` → `ftp://files.example.com/doc` (non-http scheme untouched)
- `HTTPS://EXAMPLE.COM/Path` → `https://example.com/Path` (path case preserved)
- Two URLs that should normalize to the same value → equal after normalization

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_normalize.py`
- [ ] Tests run and ALL FAIL (no implementation yet)

---

### Task 1.2: Change, OpResult, and normalize_url — Implementation
**Status:** 🔴 Blocked by 1.1
**Effort:** 30 minutes
**Dependencies:** Task 1.1

**Description:**
Implement `Change` and `OpResult` frozen dataclasses in `operations.py`, and `normalize_url` in `normalize.py`.

**Implementation details:**
- `Change(op: str, description: str, details: tuple[tuple[str, str], ...] = ())`
- `OpResult(tree: BookmarkTree, changes: tuple[Change, ...])`
- `normalize_url`: use `urllib.parse.urlparse`/`urlunparse`, lowercase scheme+host, strip default ports, strip trailing slash, sort query params, normalize http→https

**Acceptance Criteria:**
- [ ] All tests from 1.1 PASS
- [ ] mypy --strict passes on both files

---

## Phase 2: Simple Per-Folder Operations

### Task 2.1: sort_tree, remove_empty_folders, strip_icons — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 1 hour
**Dependencies:** Task 1.2
**Parallel with:** None

**Description:**
Write tests for the three simple per-folder operations. Tests MUST FAIL before implementation.

**Test cases for sort_tree:**
- Folder with bookmarks in reverse order → sorted alphabetically by title
- Folder with children in reverse order → sorted alphabetically by name
- Case-insensitive: "apple" before "Banana"
- Stable sort: identical titles retain original order
- Nested folders: sorting applies recursively
- Empty tree → unchanged, zero changes
- Already sorted → unchanged, zero changes
- Change log reports reordering count

**Test cases for remove_empty_folders:**
- Folder with one empty child → child removed
- Folder with mix of empty and non-empty children → only empty removed
- Cascading: removing a child makes parent empty → parent also removed
- Root folder never removed even if empty
- Folder with only bookmarks (no children) → not removed
- No empty folders → unchanged, zero changes
- Change log reports each removed folder path

**Test cases for strip_icons:**
- Bookmark with icon > 2048 bytes → icon replaced with ""
- Bookmark with icon = 2048 bytes → icon preserved (not strictly exceeding)
- Bookmark with icon < 2048 bytes → icon preserved
- Bookmark with empty icon → unchanged
- Custom threshold: threshold=100 strips icons > 100 bytes
- Change log reports stripped count and bytes saved
- Nested bookmarks: stripping applies recursively

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_operations.py`
- [ ] Tests use handcrafted fixture trees (not file parsing)
- [ ] Tests verify change log contents
- [ ] Tests verify original tree is unchanged (immutability)
- [ ] Tests run and ALL FAIL

---

### Task 2.2: sort_tree, remove_empty_folders, strip_icons — Implementation
**Status:** 🔴 Blocked by 2.1
**Effort:** 45 minutes
**Dependencies:** Task 2.1

**Description:**
Implement the three simple operations in `operations.py`.

**Implementation details:**
- `sort_tree`: use `map_tree` with a function that sorts `folder.children` by `name.lower()` and `folder.bookmarks` by `title.lower()`. Use `sorted(..., key=...)` for stability.
- `remove_empty_folders`: use `map_tree` bottom-up. Filter out children with zero bookmarks and zero children.
- `strip_icons`: use `map_tree`. For each folder, replace bookmarks that have `len(icon) > threshold` with icon="".

**Acceptance Criteria:**
- [ ] All tests from 2.1 PASS
- [ ] mypy --strict passes

---

## Phase 3: Structural Operations

### Task 3.1: unwrap_wrappers, dissolve_generics, merge_folders — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 1.5 hours
**Dependencies:** Task 1.2
**Parallel with:** Task 2.1

**Description:**
Write tests for the three structural operations. These are the most complex operations. Tests MUST FAIL before implementation.

**Test cases for unwrap_wrappers:**
- Root has "Imported from Chrome" child with bookmarks → bookmarks moved to root
- Root has "Imported from Chrome" child with subfolders → subfolders become root children
- Numbered variant "Imported from Chrome (2)" → detected and unwrapped
- Case-insensitive: "imported from chrome" → detected
- "Imported From Google Chrome" → detected
- "Imported from Edge" → detected
- Nested wrappers: wrapper inside wrapper → both unwrapped
- Wrapper child overlaps with existing folder → merged by name
- Non-wrapper folder → untouched
- Custom patterns parameter → uses provided patterns instead of defaults
- Change log reports each unwrapped folder and item count
- Empty tree → unchanged

**Test cases for dissolve_generics:**
- "New folder" with bookmarks → bookmarks moved to parent
- "New folder (2)" with subfolders → subfolders become siblings
- "Untitled folder" → detected
- Case-insensitive: "NEW FOLDER" → detected
- Generic child overlaps with existing sibling → merged
- Non-generic folder → untouched
- Custom patterns parameter
- Change log reports each dissolved folder

**Test cases for merge_folders:**
- Two children named "Social Media" (same case) → merged into one
- Two children named "social media" vs "Social Media" → merged (case-insensitive)
- Merged folder has combined bookmarks from both sources
- Merged folder has combined children, with nested duplicates also merged
- Merged folder: earliest add_date, latest last_modified
- Merged folder: attrs from first folder preserved
- Three folders with same name → all merged into one
- No duplicate folder names → unchanged
- Deeply nested duplicates (3 levels) → all merged
- Change log reports each merge with folder name and source count

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_operations.py`
- [ ] Tests use handcrafted fixture trees with realistic folder names
- [ ] Tests verify bookmark counts before and after
- [ ] Tests verify change log contents
- [ ] Tests run and ALL FAIL

---

### Task 3.2: unwrap_wrappers, dissolve_generics, merge_folders — Implementation
**Status:** 🔴 Blocked by 3.1
**Effort:** 1.5 hours
**Dependencies:** Task 3.1

**Description:**
Implement the three structural operations in `operations.py`.

**Implementation details:**

**unwrap_wrappers / dissolve_generics** (share a pattern):
- Walk tree recursively, rebuilding each folder's children
- For each child matching the pattern: extract its bookmarks and children, add to parent's lists
- For non-matching children: keep as-is, recurse into them
- After lifting, run merge logic on the parent's children to handle overlaps
- Default patterns as module-level compiled regexes

**merge_folders:**
- Use `map_tree` bottom-up
- For each folder, group children by `name.lower()`
- For groups with 2+ entries: combine bookmarks, combine children (then recursively merge those children), pick earliest add_date, latest last_modified, attrs from first
- Replace children tuple with merged result

**Acceptance Criteria:**
- [ ] All tests from 3.1 PASS
- [ ] mypy --strict passes

---

## Phase 4: Cross-Tree Deduplication

### Task 4.1: dedup_urls — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 1 hour
**Dependencies:** Task 1.2
**Parallel with:** Tasks 2.1, 3.1

**Description:**
Write tests for URL deduplication. Tests MUST FAIL before implementation.

**Test cases — basic:**
- Two bookmarks with same URL in same folder → one removed
- Two bookmarks with same URL in different folders → one removed
- Strategy "newest": bookmark with higher add_date kept
- Strategy "oldest": bookmark with lower add_date kept
- Strategy "longest_title": bookmark with longer title kept
- Invalid strategy → raises ValueError
- No duplicates → unchanged, zero changes

**Test cases — normalization:**
- `http://example.com` and `https://example.com` → treated as duplicate
- `https://Example.COM/path/` and `https://example.com/path` → treated as duplicate
- `https://example.com?b=2&a=1` and `https://example.com?a=1&b=2` → treated as duplicate
- `https://example.com/path#a` and `https://example.com/path#b` → NOT duplicate (different fragments)

**Test cases — data safety:**
- Unique URL count after dedup equals number of remaining bookmarks
- Every unique normalized URL from input has exactly one bookmark in output
- Original tree is unchanged after operation

**Test cases — change log:**
- Change log reports each removed duplicate with URL
- Change log includes total duplicates removed count

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_operations.py`
- [ ] Tests cover all three strategies
- [ ] Tests verify URL preservation (zero data loss)
- [ ] Tests run and ALL FAIL

---

### Task 4.2: dedup_urls — Implementation
**Status:** 🔴 Blocked by 4.1
**Effort:** 1 hour
**Dependencies:** Task 4.1

**Description:**
Implement URL deduplication in `operations.py`.

**Implementation details:**
1. Walk tree with `_collect_all_bookmarks(folder, path)` → list of `(normalized_url, bookmark, folder_path_tuple)`
2. Group by normalized URL using a dict
3. For each group with 2+ entries, select winner:
   - "newest": `max(group, key=lambda x: x[1].add_date)`
   - "oldest": `min(group, key=lambda x: x[1].add_date)`
   - "longest_title": `max(group, key=lambda x: len(x[1].title))`
4. Build a set of keeper identities: `{(bookmark.url, folder_path_tuple)}`
5. Use `map_tree` to filter each folder's bookmarks, keeping only those in the keeper set
6. Track path context so the correct bookmark-in-folder is kept

**Acceptance Criteria:**
- [ ] All tests from 4.1 PASS
- [ ] mypy --strict passes
- [ ] Unique URL count preserved (verified by tests)

---

## Phase 5: Pipeline, Package Exports & Quality Gate

### Task 5.1: run_pipeline and integration — Tests
**Status:** 🔴 Blocked by 2.2, 3.2, 4.2
**Effort:** 1 hour
**Dependencies:** Tasks 2.2, 3.2, 4.2

**Description:**
Write tests for the pipeline function and real-file integration. Tests MUST FAIL first (pipeline not implemented yet), then pass.

**Test cases — pipeline:**
- Default pipeline on handcrafted tree with wrappers, duplicates, empties → all cleaned
- Pipeline change log contains entries from all operations
- Pipeline with custom operations list (subset) → only those operations run
- Pipeline with empty tree → unchanged
- Pipeline URL count validation: unique URLs in = unique URLs out
- Pipeline preserves source_format

**Test cases — real-file integration:**
- Pipeline on `favorites_3_17_26.html` → 970 unique URLs preserved
- Pipeline on `favorites_3_17_26.html` → 0 import wrapper folders remain
- Pipeline on `favorites_3_17_26.html` → 0 empty folders remain
- Pipeline on `favorites_3_17_26.html` → 0 "New folder" instances remain
- Pipeline on `bookmarks_1_23_26.html` → unique URL count preserved

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_operations.py`
- [ ] Real-file tests use `pytest.mark.skipif` for missing files
- [ ] Tests verify data safety (URL preservation)
- [ ] Tests run and pipeline tests FAIL (not yet implemented)

---

### Task 5.2: run_pipeline — Implementation
**Status:** 🔴 Blocked by 5.1
**Effort:** 30 minutes
**Dependencies:** Task 5.1

**Description:**
Implement the pipeline function and URL count validation.

**Implementation details:**
- `run_pipeline(tree, operations=None, *, strategy="newest", icon_threshold=2048, wrapper_patterns=None, generic_patterns=None) -> OpResult`
- Default operations: `[unwrap_wrappers, dissolve_generics, merge_folders, dedup_urls, strip_icons, remove_empty_folders, sort_tree]`
- Chain: each operation's result tree feeds the next
- Accumulate all changes into a combined tuple
- After pipeline: count unique URLs in input vs output. If output < input, raise `ValueError` with the discrepancy.
- Return `OpResult(final_tree, all_changes)`

**Acceptance Criteria:**
- [ ] All pipeline and integration tests PASS
- [ ] URL count validation works (tested with a mock that loses URLs)

---

### Task 5.3: Package Exports & Quality Gate
**Status:** 🔴 Blocked by 5.2
**Effort:** 20 minutes
**Dependencies:** Task 5.2

**Description:**
Update `bookmark_cleaner/__init__.py` to export operations. Run full quality gate.

**Implementation:**
- Add `Change`, `OpResult`, `normalize_url`, all 7 operations, and `run_pipeline` to `__init__.py`
- Verify `from bookmark_cleaner import run_pipeline, dedup_urls` works

**Acceptance Criteria:**
- [ ] `from bookmark_cleaner import run_pipeline, dedup_urls, merge_folders` works (all operations importable)
- [ ] `pytest --cov=bookmark_cleaner --cov-report=term-missing` shows 80%+ coverage
- [ ] `mypy --strict src/bookmark_cleaner/` passes with zero errors
- [ ] `ruff check src/ tests/` passes
- [ ] All tests pass (Feature 1 + Feature 3 + Feature 4)

---

## Dependency Graph

```
Task 1.1 (foundation types + normalize tests)
    │
    ▼
Task 1.2 (foundation types + normalize impl)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Task 2.1           Task 3.1           Task 4.1
(simple op tests)  (structural tests) (dedup tests)
    │                  │                  │
    ▼                  ▼                  ▼
Task 2.2           Task 3.2           Task 4.2
(simple op impl)   (structural impl)  (dedup impl)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                   Task 5.1 (pipeline + integration tests)
                       │
                       ▼
                   Task 5.2 (pipeline impl)
                       │
                       ▼
                   Task 5.3 (exports + quality gate)
```

## Parallelization Opportunities

- **Tasks 2.1, 3.1, 4.1** can all run in parallel (all depend only on 1.2)
- **Tasks 2.2, 3.2, 4.2** can run in parallel once their test tasks complete
- **Critical path:** 1.1 → 1.2 → 3.1 → 3.2 → 5.1 → 5.2 → 5.3 (structural ops are the longest)

## Quality Gates

- [x] TDD enforced: every implementation task blocked by its test task
- [ ] Coverage gate at Task 5.3: 80%+ required
- [ ] Type safety gate at Task 5.3: mypy strict, zero errors
- [ ] Lint gate at Task 5.3: ruff clean
- [ ] Data safety gate: URL count validation in pipeline
- [ ] Real-file validation at Task 5.1: known counts match

## Next Steps

1. Review task breakdown
2. Run `/speckit-implement` to begin TDD execution
