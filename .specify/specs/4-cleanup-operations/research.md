# Technology Research: 4-cleanup-operations

## Decision 1: Operation Result Type

**Context:** Constitution Art. VII requires every operation to return a new tree + structured change log. Need a consistent return type.

**Options Considered:**

1. **Named tuple** — `OperationResult(tree, changes)`. Lightweight, immutable. No dependencies.

2. **Frozen dataclass** — `@dataclass(frozen=True) class OpResult`. Consistent with existing model pattern. Named fields.

3. **Plain tuple** — `tuple[BookmarkTree, tuple[Change, ...]]`. No new types. Less readable.

**Chosen:** Frozen dataclass `OpResult`
**Rationale:** Matches the existing pattern in models.py. Named fields make code self-documenting. Frozen ensures immutability. The `Change` type is also a frozen dataclass with operation name, description, and affected items.
**Tradeoffs:** Two new types (OpResult, Change). Justified by clarity.

## Decision 2: URL Normalization Approach

**Context:** Need to normalize URLs so http://Example.com/ and https://example.com are treated as equivalent duplicates.

**Options Considered:**

1. **`urllib.parse`** — Stdlib. `urlparse` + `urlunparse`. Handles scheme, host, path, query, fragment. No dependencies.

2. **Third-party URL library (yarl, furl)** — Richer API, better edge case handling. Adds a dependency.

3. **Regex-based normalization** — Simple string operations. Fragile on edge cases.

**Chosen:** `urllib.parse` (stdlib)
**Rationale:** Zero dependencies (Constitution Art. I). Handles all the normalization rules in the spec: lowercase scheme/host, strip trailing slash, parse and sort query params. Well-tested stdlib module.
**Tradeoffs:** Some edge cases (IDN domains, punycode) aren't handled automatically. Acceptable per spec — "if URL cannot be parsed, treat as-is."

## Decision 3: Deduplication Strategy Pattern

**Context:** Need configurable retention strategies: newest (default), oldest, longest title.

**Options Considered:**

1. **Strategy string parameter** — `dedup(tree, strategy="newest")`. Simple. String-based dispatch.

2. **Callable key function** — `dedup(tree, key=lambda bm: -bm.add_date)`. Flexible. Harder to document.

3. **Enum** — `DedupStrategy.NEWEST`. Type-safe. Discoverable.

**Chosen:** String parameter with validation
**Rationale:** Simplest approach. The CLI will pass strings from user input. Only 3 strategies needed. Internal dispatch to a sort key function. Constitution Art. III: no premature abstraction.
**Tradeoffs:** No type safety on strategy name. Mitigated by raising ValueError on unknown strategy.

## Decision 4: Tree Traversal Pattern for Operations

**Context:** Operations need to transform the tree. Some operate on individual folders (merge, sort), others on the whole tree (dedup across folders).

**Options Considered:**

1. **Use existing `map_tree`** — Bottom-up folder transformation. Works for per-folder operations (sort, empty removal). Doesn't work for cross-folder dedup.

2. **Collect-modify-rebuild** — Collect all bookmarks, process, rebuild tree. Works for dedup. Loses folder-level context.

3. **Two patterns** — `map_tree` for per-folder ops, custom traversal for cross-tree ops (dedup).

**Chosen:** Two patterns
**Rationale:** Per-folder operations (merge children, sort, remove empties, unwrap) naturally use `map_tree`. Cross-tree operations (dedup) need to see all bookmarks at once to detect duplicates, then rebuild the tree. Both patterns already have precedent in the codebase (`map_tree` exists; `collect_bookmarks` + rebuild is straightforward).
**Tradeoffs:** Two traversal patterns. Acceptable — they solve genuinely different problems.

## Decision 5: File Layout

**Context:** Where to put operations code.

**Options Considered:**

1. **Single `operations.py`** — All 7 operations in one file. Simple.

2. **`operations/` package** — Separate modules per operation type. More files.

3. **Two files** — `operations.py` (core ops) + `normalize.py` (URL normalization).

**Chosen:** Single `operations.py` + `normalize.py`
**Rationale:** The 7 operations are all pure functions, each 20-50 lines. A single file stays well under the 800-line guideline. URL normalization is a distinct concern used by dedup — cleaner as a separate module. Constitution Art. III: flat structure preferred.
**Tradeoffs:** `operations.py` might reach ~300 lines. Acceptable.

## Decision 6: Change Log Structure

**Context:** Each operation produces changes. The change log powers dry-run output. Need enough detail for human-readable reporting.

**Options Considered:**

1. **Flat list of strings** — Simple. `["Removed duplicate: https://example.com"]`. Not structured.

2. **Typed change entries** — `Change(op="dedup", description="...", details={...})`. Structured. Enables filtering and formatting.

3. **Hierarchical log** — Nested per-operation. More complex.

**Chosen:** Typed change entries (frozen dataclass)
**Rationale:** The CLI needs to format changes differently for dry-run vs summary vs verbose output. Structured entries with `op` (operation name), `description` (human-readable), and optional `details` dict enable this. Constitution Art. VII requires structured change logs.
**Tradeoffs:** Slightly more code than plain strings. Worth it for dry-run formatting.
