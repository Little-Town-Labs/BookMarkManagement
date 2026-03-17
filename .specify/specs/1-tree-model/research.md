# Technology Research: 1-tree-model

## Decision 1: Immutability Mechanism

**Context:** The model must be immutable (Constitution Art. VII). Python offers several approaches.

**Options Considered:**

1. **`@dataclass(frozen=True)`** — Built-in Python 3.7+. Sets `__setattr__` and `__delattr__` to raise `FrozenInstanceError`. Generates `__hash__`. No dependencies.

2. **`NamedTuple`** — Built-in. Immutable by nature (tuple subclass). Less readable for complex types. No default values before 3.6.1.

3. **`attrs` with `frozen=True`** — Third-party library. More features (validators, converters). Adds a dependency.

4. **`pydantic.BaseModel` with `frozen=True`** — Third-party. Powerful validation. Heavy dependency (~2MB installed). Overkill for data containers.

**Chosen:** `@dataclass(frozen=True)`
**Rationale:** Zero dependencies (stdlib only), clear and readable, standard Python pattern. Satisfies Constitution Art. I (lightweight) and Art. VI (no unnecessary deps). Generates `__eq__` and `__hash__` automatically, which satisfies FR-5 (structural equality) for free.
**Tradeoffs:** No built-in validation (we add a `__post_init__` for type checks). No slot optimization by default (add `slots=True` on Python 3.10+).

## Decision 2: Collection Types for Children

**Context:** Folders contain ordered collections of bookmarks and subfolders. These must be immutable.

**Options Considered:**

1. **`tuple`** — Immutable, hashable, stdlib. Slightly verbose to construct from generators.

2. **`frozenset`** — Immutable, but unordered. Bookmarks and folders have a meaningful order (preserved from source).

3. **`list`** — Mutable. Would break immutability guarantee even inside a frozen dataclass (frozen only prevents reassignment, not mutation of contained lists).

**Chosen:** `tuple`
**Rationale:** Only immutable ordered collection in stdlib. Preserves insertion order (spec FR-2: "ordering is preserved from the source"). Hashable, which enables the frozen dataclass `__hash__`. Lists inside frozen dataclasses are a known gotcha — a `frozen=True` dataclass with a list field is not truly immutable.
**Tradeoffs:** Slightly more verbose (`tuple(...)` wrapping) when constructing trees in parsers. Acceptable.

## Decision 3: Flexible Attributes Storage

**Context:** Bookmark files contain browser-specific attributes (PERSONAL_TOOLBAR_FOLDER, SHORTCUTURL, etc.) that vary by browser. The model needs a catch-all for these.

**Options Considered:**

1. **`dict[str, str]`** — Simple, familiar. But mutable inside frozen dataclass.

2. **`types.MappingProxyType(dict)`** — Read-only view of a dict. Not hashable. Prevents mutation.

3. **`tuple[tuple[str, str], ...]`** — Fully immutable and hashable. Less ergonomic for lookups.

4. **Store known attrs as explicit fields, ignore unknown ones** — Simpler but loses data.

**Chosen:** `tuple[tuple[str, str], ...]` for storage, with a helper property or function to convert to dict for lookups
**Rationale:** Truly immutable and hashable, consistent with the tuple approach for children. A utility function `attrs_to_dict()` provides convenient lookup when needed. This preserves all attributes without data loss (spec FR-1) while maintaining true immutability.
**Tradeoffs:** Slightly less ergonomic than dict access. Acceptable since attribute lookup is infrequent (mostly during export).

## Decision 4: File Organization

**Context:** Where to put the model and utility code. Constitution Art. III says flat structure, max 3 directory levels under `src/`.

**Options Considered:**

1. **Single file `models.py`** — Everything in one file: types + utilities + equality.

2. **Two files: `models.py` + `tree.py`** — Types in models, traversal/utility functions in tree.

3. **Three files: `models.py` + `tree.py` + `compare.py`** — Separate comparison logic.

**Chosen:** Two files: `models.py` + `tree.py`
**Rationale:** Models are pure data definitions (~50 lines). Tree utilities are standalone functions (~100-150 lines). Two focused files is cleaner than one large file, and simpler than three tiny files. Equality comparison fits naturally in tree.py alongside other tree operations. Follows Constitution Art. III (simplicity, flat structure).
**Tradeoffs:** None significant. If tree.py grows past 400 lines in later features, it can be split then.
