# Implementation Plan: 1-tree-model

**Feature:** Immutable Bookmark Tree Model
**Specification:** `.specify/specs/1-tree-model/spec.md`
**Branch:** `1-tree-model`
**Created:** 2026-03-17

## Executive Summary

Implement the core immutable data model for bookmark-cleaner: three frozen dataclasses (`BookmarkNode`, `FolderNode`, `BookmarkTree`) and a set of standalone utility functions for tree traversal, transformation, and comparison. This is the foundation every other feature builds on.

Two source files, approximately 200 lines total. No dependencies beyond Python stdlib.

## Architecture Overview

```
src/bookmark_cleaner/
    __init__.py          # Package root, re-exports public API
    models.py            # BookmarkNode, FolderNode, BookmarkTree (frozen dataclasses)
    tree.py              # Standalone utility functions for traversal/transformation/comparison
```

No external dependencies. No configuration. No I/O. Pure data types and pure functions.

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Immutability | `@dataclass(frozen=True, slots=True)` | Stdlib, zero deps, generates `__eq__`/`__hash__` |
| Collections | `tuple` for ordered children | Only immutable ordered type in stdlib |
| Flexible attrs | `tuple[tuple[str, str], ...]` | Truly immutable + hashable, unlike dict |
| Type hints | Full annotations, `from __future__ import annotations` | Required by Constitution Art. VI (mypy strict) |

See `research.md` for detailed decision rationale.

## Technical Decisions

### TD-1: Frozen Dataclasses with Slots

**Context:** Need immutable, hashable, equatable data types.
**Chosen:** `@dataclass(frozen=True, slots=True)` — Python 3.10+ feature. `slots=True` prevents `__dict__` creation, saving memory and further preventing dynamic attribute addition.
**Tradeoffs:** Requires Python 3.10+ (matches our floor). Cannot add attributes dynamically (desired — enforces immutability).

### TD-2: Root Folder Instead of Root List

**Context:** Browsers have multiple root-level containers (bookmark bar, other bookmarks, mobile). Should the tree root be a list of folders or a single folder?
**Chosen:** Single root FolderNode with children. The root folder has an empty name and serves as the implicit container.
**Rationale:** Simpler — every traversal function works on FolderNode. No special case for "is this a tree or a folder?" The root is just a folder. Parsers create root children for each browser container.
**Tradeoffs:** One extra nesting level that must be unwrapped during export. Simple and consistent.

### TD-3: Utility Functions, Not Methods

**Context:** Where do traversal/transformation functions live?
**Chosen:** Standalone functions in `tree.py`, not methods on the dataclasses.
**Rationale:** Constitution Art. III says "utility functions should be standalone functions, not methods on a base class hierarchy." Frozen dataclasses stay pure data. Functions are independently testable and don't bloat the type definitions. New utilities can be added without modifying the core types.
**Tradeoffs:** Slightly less discoverable than methods. Mitigated by clear module naming and re-exports from `__init__.py`.

### TD-4: Equality Semantics

**Context:** FR-5 requires structural equality with optional metadata ignoring.
**Chosen:** Default `__eq__` from frozen dataclass compares all fields (full equality). A separate `trees_equal(a, b, ignore_metadata=False)` function provides configurable comparison. A `first_difference(a, b)` function returns a human-readable description of the first difference.
**Rationale:** Default equality is strict (correct for most uses). The utility function handles the roundtrip testing case where metadata may differ.
**Tradeoffs:** Two equality mechanisms. Clear naming prevents confusion.

## Implementation Phases

### Phase A: Core Types (models.py)

Implement the three frozen dataclasses:

1. `BookmarkNode` — url, title, add_date, icon, attrs
2. `FolderNode` — name, children, bookmarks, add_date, last_modified, attrs
3. `BookmarkTree` — root, source_format

Include `__post_init__` validation on BookmarkNode (url must be non-empty string).

**Estimated size:** ~60 lines
**Dependencies:** None

### Phase B: Tree Utilities (tree.py)

Implement standalone functions:

1. `collect_bookmarks(folder)` — depth-first collection of all bookmarks
2. `collect_urls(folder)` — unique URLs as frozenset
3. `count_items(folder)` — (bookmark_count, folder_count) tuple
4. `folder_paths(folder)` — all folder paths as strings
5. `map_tree(folder, fn)` — bottom-up transformation, returns new folder
6. `replace_bookmarks(folder, bookmarks)` — new folder with replaced bookmarks
7. `replace_children(folder, children)` — new folder with replaced children
8. `find_folder(folder, name)` — case-insensitive folder search
9. `trees_equal(tree_a, tree_b, ignore_metadata)` — structural comparison
10. `first_difference(tree_a, tree_b)` — human-readable diff description

**Estimated size:** ~140 lines
**Dependencies:** Phase A

### Phase C: Package Init (__init__.py)

Re-export public API:
- `BookmarkNode`, `FolderNode`, `BookmarkTree` from models
- All utility functions from tree

**Estimated size:** ~15 lines
**Dependencies:** Phase A, Phase B

## Testing Strategy

**Framework:** pytest
**Coverage target:** 80%+ (Constitution Art. II)
**Approach:** TDD — write tests first, then implement

### Test Files

```
tests/
    __init__.py
    test_models.py       # BookmarkNode, FolderNode, BookmarkTree
    test_tree.py         # All utility functions
```

### test_models.py — Test Cases

**BookmarkNode:**
- Create with just URL (defaults applied)
- Create with all fields
- Frozen: setting attribute raises FrozenInstanceError
- Equality: same url+title = equal
- Equality: different url = not equal
- Validation: empty URL raises ValueError
- Unicode title preserved
- Large icon data stored as-is
- Extra attrs stored and accessible

**FolderNode:**
- Create empty folder (no children, no bookmarks)
- Create with children and bookmarks
- Frozen: setting attribute raises FrozenInstanceError
- Nested folders (folder in folder in folder)
- Order preserved (children and bookmarks maintain insertion order)
- Equality: same structure = equal
- Equality: different bookmark order = not equal

**BookmarkTree:**
- Create with default root
- Create with populated root
- Frozen: setting attribute raises FrozenInstanceError
- source_format stored correctly

### test_tree.py — Test Cases

**collect_bookmarks:**
- Empty folder returns empty tuple
- Flat folder returns its bookmarks
- Nested folders returns all bookmarks depth-first
- Duplicate URLs returned as separate entries

**collect_urls:**
- Empty folder returns empty frozenset
- Duplicates deduplicated in result
- URLs from nested folders included

**count_items:**
- Empty tree returns (0, 0)
- Flat folder counts correctly
- Nested folders counted recursively

**folder_paths:**
- Empty tree returns empty
- Single folder returns its name
- Nested paths use " > " separator

**map_tree:**
- Identity function returns equal tree
- Transformation applied bottom-up
- Original tree unchanged after map

**replace_bookmarks / replace_children:**
- Returns new folder with replaced field
- Other fields unchanged
- Original folder unchanged

**find_folder:**
- Finds by exact name
- Case-insensitive matching
- Returns None if not found
- Finds nested folder

**trees_equal:**
- Identical trees are equal
- Different bookmark = not equal
- ignore_metadata=True skips dates and icons
- Different folder structure = not equal

**first_difference:**
- Returns None for equal trees
- Returns meaningful string for first difference

## Security Considerations

None — this feature is pure data types with no I/O, no network, no file access, no user input processing.

## Performance Strategy

No optimization needed (Constitution Art. V). Frozen dataclasses with slots are already memory-efficient. Recursive traversal handles 10,000+ bookmarks with Python's default recursion limit of 1,000 (typical nesting depth is under 10).

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Tuple verbosity makes parser code ugly | Medium | Low | Parsers (Feature 3) can build with mutable lists then convert to tuples in a final step. `__post_init__` can coerce lists to tuples. |
| `slots=True` breaks pickle/copy | Low | Low | We don't need pickle or deep copy. Immutable objects don't need copying. |
| Recursive traversal hits recursion limit on pathological input | Very Low | Medium | Real bookmark files have <10 nesting levels. Add a note in docs. |

## Constitutional Compliance

- [x] **Art. I (Lightweight):** Zero dependencies. Pure stdlib.
- [x] **Art. II (Test-First):** Test cases defined above. TDD workflow.
- [x] **Art. III (Simplicity):** 3 types, standalone functions, 2 files, ~200 lines.
- [x] **Art. IV (Data Safety):** Model stores all data losslessly. Immutability prevents corruption.
- [x] **Art. V (No Perf SLAs):** No optimization. Reasonable algorithms.
- [x] **Art. VI (Tech Constraints):** Python stdlib only. Frozen dataclasses. mypy-strict compatible.
- [x] **Art. VII (Immutable Model):** Frozen dataclasses, tuple collections, no mutation possible.
- [x] **Art. VIII (Browser Compat):** Model preserves all attributes needed for browser import.

No exceptions needed.

## Next Steps

1. Run `/speckit-tasks` to generate task breakdown
2. Implement via TDD (`/speckit-implement`)
