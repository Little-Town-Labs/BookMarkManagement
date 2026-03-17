# Implementation Plan: 4-cleanup-operations

**Feature:** Cleanup Operations Pipeline
**Specification:** `.specify/specs/4-cleanup-operations/spec.md`
**Branch:** `4-cleanup-operations`
**Created:** 2026-03-17

## Executive Summary

Implement 7 composable cleanup operations as pure functions, each returning an immutable `OpResult(tree, changes)`. A pipeline function chains them in the default order. Two new source files: `operations.py` (~300 lines) for all operations and the pipeline, `normalize.py` (~40 lines) for URL normalization. Zero external dependencies.

## Architecture Overview

```
src/bookmark_cleaner/
    models.py          # existing — BookmarkNode, FolderNode, BookmarkTree
    tree.py            # existing — map_tree, replace_bookmarks, replace_children, etc.
    normalize.py       # NEW — normalize_url()
    operations.py      # NEW — 7 operations + run_pipeline()
```

Data flow:
```
BookmarkTree → operation(tree, **opts) → OpResult(tree, changes)
BookmarkTree → run_pipeline(tree, **opts) → OpResult(tree, combined_changes)
```

Each operation is a standalone pure function:
```
unwrap_wrappers(tree) → OpResult
dissolve_generics(tree) → OpResult
merge_folders(tree) → OpResult
dedup_urls(tree, strategy) → OpResult
strip_icons(tree, threshold) → OpResult
remove_empty_folders(tree) → OpResult
sort_tree(tree) → OpResult
```

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| URL parsing | `urllib.parse` | Stdlib, handles all normalization rules (Constitution Art. I, VI) |
| Tree traversal | `map_tree` from tree.py | Existing utility for per-folder bottom-up transforms |
| Pattern matching | `re` module | Stdlib, for wrapper/generic folder name detection |
| Data types | Frozen dataclasses | Consistent with existing models.py pattern |

See `research.md` for detailed decision rationale.

## Technical Decisions

### TD-1: Two New Data Types (Change, OpResult)

**Context:** Constitution Art. VII mandates operations return new tree + structured change log.
**Chosen:** Two frozen dataclasses in `operations.py`. `Change(op, description, details)` and `OpResult(tree, changes)`. Details is `tuple[tuple[str, str], ...]` for immutability.
**Tradeoffs:** Two new types. Justified — they appear in every operation signature and the pipeline.

### TD-2: URL Normalization as Separate Module

**Context:** URL normalization is used by dedup but is a distinct, independently testable concern.
**Chosen:** `normalize.py` with a single `normalize_url(url: str) -> str` function using `urllib.parse`.
**Rules:** Lowercase scheme+host, strip trailing slash, sort query params, treat http/https as equivalent (normalize to https), strip default ports, preserve fragments and auth info.
**Tradeoffs:** Extra file. Clean separation of concerns.

### TD-3: Per-Folder vs Cross-Tree Operations

**Context:** Some operations transform individual folders (sort, merge children, remove empties). Others need a global view (dedup across all folders).
**Chosen:**
- **Per-folder ops** use `map_tree` — sort, remove empties, merge children within each folder.
- **Cross-tree ops** use collect-filter-rebuild — dedup collects all bookmarks, determines which to keep, then rebuilds the tree excluding removed ones.
- **Structural ops** use direct tree walks — unwrap and dissolve need to modify parent-child relationships, so they walk the tree and reconstruct it.

### TD-4: Dedup Strategy via String Parameter

**Context:** Need configurable retention: newest (default), oldest, longest title.
**Chosen:** `dedup_urls(tree, strategy="newest")` with internal dispatch to a sort key. Raises `ValueError` on unknown strategy.
**Tradeoffs:** No type safety on string. Simple and CLI-friendly.

### TD-5: Default Wrapper and Generic Patterns

**Context:** Need configurable patterns for import wrappers and generic folders.
**Chosen:** Default patterns as module-level tuples of compiled regexes. Functions accept optional `patterns` parameter to override. Defaults detect:
- Wrappers: `r"(?i)^imported\s+from\s+.+$"` (covers Chrome, Edge, Firefox, Safari, Opera, numbered variants)
- Generics: `r"(?i)^(new|untitled)\s+folder(\s*\(\d+\))?$"`
**Tradeoffs:** Regex is overkill for simple string matching, but cleanly handles numbered variants and case-insensitivity in one pattern.

### TD-6: Folder Merge Algorithm

**Context:** Merging folders with the same name at the same level. Must combine bookmarks, recursively merge children, pick best metadata.
**Chosen:** For each folder, group children by `name.lower()`. For each group of 2+ folders with the same name:
1. Combine all bookmarks into one tuple
2. Combine all children, then recursively merge those children
3. Use earliest `add_date`, latest `last_modified`
4. Keep `attrs` from the first folder in the group
5. Keep the name casing from the first folder

Apply this bottom-up via `map_tree` so nested duplicates are merged before parent duplicates.
**Tradeoffs:** Bottom-up means we may merge nested folders that were about to be lifted by unwrap. Ordering the pipeline (unwrap first, then merge) avoids this.

### TD-7: Dedup Collect-Filter-Rebuild

**Context:** Dedup needs to see all bookmarks across the entire tree to detect duplicates, then remove them from their original folder positions.
**Chosen:**
1. Walk the tree, collecting `(normalized_url, bookmark, folder_path)` triples
2. Group by normalized URL
3. For each group, pick the winner based on strategy (newest add_date, etc.)
4. Build a set of "keeper" bookmark identities (url + folder_path combos)
5. Rebuild the tree using `map_tree`, filtering each folder's bookmarks to only keepers

**Tradeoffs:** Two tree passes (collect + rebuild). Negligible for bookmark-scale data.

### TD-8: Pipeline Composition

**Context:** Need a default pipeline that chains all operations.
**Chosen:** `run_pipeline(tree, operations=None, **opts) -> OpResult`. Default operations list:
1. `unwrap_wrappers`
2. `dissolve_generics`
3. `merge_folders`
4. `dedup_urls`
5. `strip_icons`
6. `remove_empty_folders`
7. `sort_tree`

Each operation's output tree feeds into the next. Change logs are concatenated. URL count validation runs at the end — if unique URLs decreased, raise an error.
**Tradeoffs:** Fixed function signatures mean each operation needs consistent `(tree, **kwargs) -> OpResult`. Kwargs are forwarded by name.

## Implementation Phases

### Phase A: Foundation Types + URL Normalization

**Files:** `operations.py` (Change, OpResult), `normalize.py`

**Scope:**
- `Change` frozen dataclass
- `OpResult` frozen dataclass
- `normalize_url(url: str) -> str` function

**Estimated size:** ~60 lines
**Dependencies:** None (only stdlib)

### Phase B: Simple Per-Folder Operations

**Files:** `operations.py`

**Scope:**
- `sort_tree(tree) -> OpResult` — sort folders and bookmarks alphabetically within each folder
- `remove_empty_folders(tree) -> OpResult` — remove folders with no children and no bookmarks
- `strip_icons(tree, threshold=2048) -> OpResult` — replace oversized icons with empty string

**Estimated size:** ~80 lines
**Dependencies:** Phase A (OpResult, Change), tree.py (map_tree, replace_bookmarks, replace_children)

### Phase C: Structural Operations

**Files:** `operations.py`

**Scope:**
- `unwrap_wrappers(tree, patterns=None) -> OpResult` — dissolve import wrapper folders
- `dissolve_generics(tree, patterns=None) -> OpResult` — dissolve generic placeholder folders
- `merge_folders(tree) -> OpResult` — merge same-name folders at each level

**Estimated size:** ~120 lines
**Dependencies:** Phase A, tree.py

### Phase D: Cross-Tree Deduplication

**Files:** `operations.py`

**Scope:**
- `dedup_urls(tree, strategy="newest") -> OpResult` — URL deduplication with normalization

**Estimated size:** ~60 lines
**Dependencies:** Phase A (OpResult), normalize.py

### Phase E: Pipeline + Package Exports

**Files:** `operations.py`, `__init__.py`

**Scope:**
- `run_pipeline(tree, operations=None, **opts) -> OpResult`
- URL count validation after pipeline
- Update `__init__.py` exports

**Estimated size:** ~40 lines
**Dependencies:** Phases A-D

## Testing Strategy

**Framework:** pytest
**Coverage target:** 80%+
**Approach:** TDD — tests first, per the tasks breakdown

### Test Files

```
tests/
    test_normalize.py      # URL normalization tests
    test_operations.py     # All 7 operations + pipeline tests
```

### Key Test Categories

**URL normalization (~15 tests):**
- Scheme normalization (http → https)
- Host lowercasing
- Trailing slash stripping
- Query param sorting
- Default port stripping
- Fragment preservation
- Unparseable URLs returned as-is

**Per-operation tests (~10-15 tests each):**
- Each operation has basic functionality tests
- Each operation verifies change log contents
- Each operation verifies original tree is unchanged
- Each operation has edge case tests (empty tree, no changes needed)

**Pipeline tests (~10 tests):**
- Full pipeline on handcrafted fixture tree
- Full pipeline on real `favorites_3_17_26.html` → verify 970 unique URLs
- Pipeline with custom operation subset
- Pipeline URL count validation

**Real-file integration tests (~5 tests):**
- Pipeline on `favorites_3_17_26.html` → 2503 → 970 bookmarks
- Pipeline on `bookmarks_1_23_26.html` → verify URL count preserved
- Verify all 11 wrappers unwrapped
- Verify all 31 empty folders removed

## Security Considerations

- No network access
- No file I/O (operations are pure tree transformations)
- URL normalization uses stdlib `urllib.parse` — no risk of code execution
- No user-provided regexes (patterns are code-defined defaults or explicit overrides)

## Performance Strategy

No optimization needed (Constitution Art. V). Operations are O(n) or O(n log n) for sorting. The real file (2503 bookmarks) will process in milliseconds.

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Folder merge loses bookmarks | Medium | High | Test with real file, verify bookmark count before/after each merge |
| URL normalization false positives | Low | Medium | Conservative normalization — only well-defined transformations. Test with real URLs from sample files |
| Unwrap ordering matters | Medium | Medium | Pipeline order: unwrap before merge. Test with nested wrapper + duplicate folder scenario |
| Dedup keeper selection wrong | Low | Medium | Test all three strategies with known data |

## Constitutional Compliance

- [x] **Art. I (Lightweight):** Zero dependencies. stdlib only.
- [x] **Art. II (Test-First):** TDD workflow. Tests before implementation.
- [x] **Art. III (Simplicity):** Two files. Pure functions. No class hierarchies.
- [x] **Art. IV (Non-Destructive):** Operations return new trees. Originals never modified. URL count validation.
- [x] **Art. V (No Perf SLAs):** No optimization.
- [x] **Art. VI (Tech Constraints):** stdlib only (urllib.parse, re).
- [x] **Art. VII (Immutable Model):** Frozen OpResult and Change. Operations return new trees + change logs.
- [x] **Art. VIII (Browser Compat):** N/A — operations don't produce HTML (that's the exporter).

No exceptions needed.

## Next Steps

1. Run `/speckit-tasks` to generate task breakdown
2. Implement via TDD (`/speckit-implement`)
