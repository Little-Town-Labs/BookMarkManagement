# Task Breakdown: 1-tree-model

**Feature:** Immutable Bookmark Tree Model
**Plan:** `.specify/specs/1-tree-model/plan.md`
**Branch:** `1-tree-model`
**Created:** 2026-03-17

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 9 |
| Phases | 3 |
| Critical Path | 1.1 → 1.2 → 2.1 → 2.2 → 3.1 |

## User Story → Task Mapping

| User Story | Tasks |
|------------|-------|
| US-1: Lossless Representation | 1.1, 1.2 (model stores all data) |
| US-2: Immutable Transformation | 1.1, 1.2, 2.1, 2.2 (frozen types + map_tree/replace) |
| US-3: Tree Inspection | 2.1, 2.2 (collect, count, paths utilities) |
| US-4: Equality and Comparison | 2.3, 2.4 (trees_equal, first_difference) |

---

## Phase 1: Core Types (models.py)

### Task 1.1: BookmarkNode, FolderNode, BookmarkTree — Tests
**Status:** 🟡 Ready
**Effort:** 1 hour
**Dependencies:** None
**Covers:** FR-1, FR-2, FR-3, NFR-2

**Description:**
Write tests for all three frozen dataclasses. Tests MUST be written FIRST and confirmed to FAIL before any implementation.

**Test cases to write:**

BookmarkNode:
- Create with just URL → defaults applied (title="", add_date=0, icon="", attrs=())
- Create with all fields → all stored correctly
- Frozen: `node.url = "x"` raises `FrozenInstanceError`
- Equality: same fields → equal; different url → not equal
- Validation: `BookmarkNode(url="")` raises `ValueError`
- Unicode title preserved (e.g., Japanese, emoji)
- Large icon string (50KB+) stored without truncation
- Attrs tuple accessible and iterable

FolderNode:
- Create empty folder → children=(), bookmarks=()
- Create with nested children and bookmarks
- Frozen: `folder.name = "x"` raises `FrozenInstanceError`
- Empty check: folder with no children and no bookmarks
- Deep nesting: 20-level folder chain creates without error
- Order: bookmarks and children maintain insertion order
- Equality: identical structure → equal; different bookmark order → not equal

BookmarkTree:
- Create with default root → root is empty FolderNode
- Create with populated root and source_format
- Frozen: `tree.root = x` raises `FrozenInstanceError`

**Acceptance Criteria:**
- [ ] All test cases above written in `tests/test_models.py`
- [ ] Tests run and ALL FAIL (no implementation yet)
- [ ] Each test has a clear, descriptive name

---

### Task 1.2: BookmarkNode, FolderNode, BookmarkTree — Implementation
**Status:** 🔴 Blocked by 1.1
**Effort:** 45 minutes
**Dependencies:** Task 1.1

**Description:**
Implement the three frozen dataclasses in `src/bookmark_cleaner/models.py` to pass all tests from Task 1.1.

**Implementation details:**
- `@dataclass(frozen=True, slots=True)` for all three types
- `from __future__ import annotations` for forward references
- `BookmarkNode.__post_init__`: validate url is non-empty string
- `FolderNode`: `name` field first (required), rest have defaults
- `BookmarkTree`: `root` defaults to `FolderNode(name="")`
- Full type annotations compatible with mypy strict mode

**Acceptance Criteria:**
- [ ] All tests from Task 1.1 PASS
- [ ] `mypy --strict src/bookmark_cleaner/models.py` passes with no errors
- [ ] No implementation beyond what tests require

---

## Phase 2: Tree Utilities (tree.py)

### Task 2.1: Traversal & Query Functions — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 1 hour
**Dependencies:** Task 1.2
**Covers:** FR-4

**Description:**
Write tests for traversal and query utility functions. Tests MUST FAIL before implementation.

**Test cases to write:**

`collect_bookmarks(folder)`:
- Empty folder → empty tuple
- Folder with 3 bookmarks → tuple of 3
- Nested: parent has 1, child has 2 → tuple of 3 (depth-first: child bookmarks after recursing)
- Duplicate URLs across folders → all returned (not deduplicated)

`collect_urls(folder)`:
- Empty folder → empty frozenset
- 3 bookmarks with unique URLs → frozenset of 3
- 5 bookmarks with 2 duplicate URLs → frozenset of 3
- Nested folders → URLs from all levels

`count_items(folder)`:
- Empty folder → (0, 0)
- 3 bookmarks, no subfolders → (3, 0)
- 2 bookmarks, 1 subfolder with 3 bookmarks → (5, 1)
- Nested: counts all levels recursively

`folder_paths(folder)`:
- Empty folder (no children) → empty tuple
- Folder "A" with child "B" → ("A", "A > B")
- Deeper: "A > B > C" included
- Root with empty name → children paths don't start with " > "

`find_folder(folder, name)`:
- Exact match → returns folder
- Case-insensitive: "social media" finds "Social Media"
- Not found → returns None
- Nested match → finds folder inside subfolder
- Multiple matches → returns first found (depth-first)

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_tree.py`
- [ ] Tests run and ALL FAIL
- [ ] Test fixtures use realistic bookmark data (not just "test1", "test2")

---

### Task 2.2: Traversal & Query Functions — Implementation
**Status:** 🔴 Blocked by 2.1
**Effort:** 45 minutes
**Dependencies:** Task 2.1

**Description:**
Implement `collect_bookmarks`, `collect_urls`, `count_items`, `folder_paths`, and `find_folder` in `src/bookmark_cleaner/tree.py`.

**Implementation notes:**
- All functions take `FolderNode` as first argument
- All functions are pure (no side effects, no mutation)
- `folder_paths` takes optional `prefix` parameter for recursive path building
- `find_folder` uses `name.lower()` comparison

**Acceptance Criteria:**
- [ ] All tests from Task 2.1 PASS
- [ ] `mypy --strict src/bookmark_cleaner/tree.py` passes
- [ ] No implementation beyond what tests require

---

### Task 2.3: Transformation Functions — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 45 minutes
**Dependencies:** Task 1.2
**Parallel with:** Task 2.1

**Description:**
Write tests for tree transformation utility functions. Tests MUST FAIL before implementation.

**Test cases to write:**

`replace_bookmarks(folder, new_bookmarks)`:
- Returns new folder with different bookmarks
- Original folder unchanged (same bookmarks as before)
- Name, children, dates, attrs all preserved on new folder

`replace_children(folder, new_children)`:
- Returns new folder with different children
- Original folder unchanged
- Name, bookmarks, dates, attrs all preserved on new folder

`map_tree(folder, fn)`:
- Identity function `lambda f: f` → result equals original
- Rename function → all folder names changed
- Bottom-up order: child folders processed before parent
- Original tree completely unchanged after map
- Works on deeply nested tree (3+ levels)

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_tree.py` (same file as 2.1)
- [ ] Tests run and ALL FAIL
- [ ] Tests verify original trees are NOT modified (immutability check)

---

### Task 2.4: Transformation Functions — Implementation
**Status:** 🔴 Blocked by 2.3
**Effort:** 30 minutes
**Dependencies:** Task 2.3

**Description:**
Implement `replace_bookmarks`, `replace_children`, and `map_tree` in `src/bookmark_cleaner/tree.py`.

**Implementation notes:**
- `replace_bookmarks`/`replace_children` use `dataclasses.replace()` or manual construction
- `map_tree` recurses into children first (bottom-up), then applies `fn` to the current folder
- All return new FolderNode instances

**Acceptance Criteria:**
- [ ] All tests from Task 2.3 PASS
- [ ] `mypy --strict` passes
- [ ] No mutation of input arguments

---

### Task 2.5: Equality & Comparison Functions — Tests
**Status:** 🔴 Blocked by 1.2
**Effort:** 45 minutes
**Dependencies:** Task 1.2
**Parallel with:** Task 2.1, Task 2.3
**Covers:** FR-5

**Description:**
Write tests for structural equality and difference reporting. Tests MUST FAIL before implementation.

**Test cases to write:**

`trees_equal(tree_a, tree_b, ignore_metadata=False)`:
- Identical trees → True
- Different bookmark URL → False
- Different bookmark title → False
- Different folder name → False
- Different folder structure (extra subfolder) → False
- Different bookmark order within folder → False
- `ignore_metadata=True`: same structure, different add_dates → True
- `ignore_metadata=True`: same structure, different icons → True
- `ignore_metadata=True`: different URLs → still False

`first_difference(tree_a, tree_b)`:
- Identical trees → None
- Different root folder name → string mentioning the folder names
- Different bookmark count in folder → string mentioning the folder and counts
- Different bookmark URL → string mentioning the URL difference
- Nested difference → string includes path to the differing location

**Acceptance Criteria:**
- [ ] All test cases written in `tests/test_tree.py`
- [ ] Tests run and ALL FAIL
- [ ] Difference descriptions are human-readable (tested via `assert "Social Media" in diff`)

---

### Task 2.6: Equality & Comparison Functions — Implementation
**Status:** 🔴 Blocked by 2.5
**Effort:** 45 minutes
**Dependencies:** Task 2.5

**Description:**
Implement `trees_equal` and `first_difference` in `src/bookmark_cleaner/tree.py`.

**Implementation notes:**
- `trees_equal` with `ignore_metadata=False` can delegate to dataclass `__eq__`
- `trees_equal` with `ignore_metadata=True` compares url+title for bookmarks, name+children structure for folders
- `first_difference` walks both trees in parallel, returns description of first mismatch
- Path tracking via recursive `prefix` parameter for meaningful messages

**Acceptance Criteria:**
- [ ] All tests from Task 2.5 PASS
- [ ] `mypy --strict` passes
- [ ] Difference messages are clear and include folder/bookmark context

---

## Phase 3: Package & Quality Gate

### Task 3.1: Package Init & Public API
**Status:** 🔴 Blocked by 2.2, 2.4, 2.6
**Effort:** 15 minutes
**Dependencies:** Tasks 2.2, 2.4, 2.6

**Description:**
Create `src/bookmark_cleaner/__init__.py` with re-exports and verify the complete package works.

**Implementation:**
- Re-export `BookmarkNode`, `FolderNode`, `BookmarkTree` from models
- Re-export all 10 utility functions from tree
- Add `__version__ = "0.1.0"`

**Acceptance Criteria:**
- [ ] `from bookmark_cleaner import BookmarkNode, FolderNode, BookmarkTree` works
- [ ] `from bookmark_cleaner import collect_bookmarks, map_tree, trees_equal` works (all 10 functions)
- [ ] All existing tests still pass
- [ ] `mypy --strict src/bookmark_cleaner/` passes on entire package

---

### Task 3.2: Coverage & Quality Gate
**Status:** 🔴 Blocked by 3.1
**Effort:** 15 minutes
**Dependencies:** Task 3.1

**Description:**
Run full test suite with coverage reporting. Verify all quality gates pass.

**Acceptance Criteria:**
- [ ] `pytest --cov=bookmark_cleaner --cov-report=term-missing` shows 80%+ coverage
- [ ] `mypy --strict src/bookmark_cleaner/` passes with zero errors
- [ ] `ruff check src/ tests/` passes with zero warnings
- [ ] All 30+ tests pass
- [ ] No `# type: ignore` comments in source code

---

## Dependency Graph

```
Task 1.1 (model tests)
    │
    ▼
Task 1.2 (model impl)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Task 2.1           Task 2.3           Task 2.5
(traversal tests)  (transform tests)  (equality tests)
    │                  │                  │
    ▼                  ▼                  ▼
Task 2.2           Task 2.4           Task 2.6
(traversal impl)   (transform impl)   (equality impl)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                   Task 3.1 (package init)
                       │
                       ▼
                   Task 3.2 (quality gate)
```

## Parallelization Opportunities

- **Tasks 2.1, 2.3, 2.5** can all run in parallel (all depend only on 1.2, independent of each other)
- **Tasks 2.2, 2.4, 2.6** can run in parallel once their respective test tasks complete
- **Critical path:** 1.1 → 1.2 → 2.5 → 2.6 → 3.1 → 3.2 (longest chain)

## Quality Gates

- [x] TDD enforced: every implementation task blocked by its test task
- [ ] Coverage gate at Task 3.2: 80%+ required
- [ ] Type safety gate at Task 3.2: mypy strict, zero errors
- [ ] Lint gate at Task 3.2: ruff clean

## Next Steps

1. Review task breakdown
2. Run `/speckit-implement` to begin TDD execution
