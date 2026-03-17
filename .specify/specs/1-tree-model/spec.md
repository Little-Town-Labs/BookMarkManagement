# Feature Specification: Immutable Bookmark Tree Model

**Feature Number:** 1
**Branch:** 1-tree-model
**Status:** Draft
**Created:** 2026-03-17
**Last Updated:** 2026-03-17

## Overview

The bookmark tree model is the core data structure that represents a user's bookmark collection in memory. It must faithfully capture everything a bookmark file contains — folders, bookmarks, their nesting relationships, and metadata — so that operations (dedup, merge, sort) can transform the tree and exporters can write it back to a file with zero data loss.

The model must be immutable so that every operation produces a new tree rather than modifying the original. This enables dry-run/preview mode (compare before vs after) and makes operations composable and independently testable.

## User Stories

### User Story 1: Lossless Representation
**As a** user who exports bookmarks from a browser
**I want** the tool to capture every piece of data in my bookmark file
**So that** nothing is lost or corrupted when the tool processes and re-exports my bookmarks

**Acceptance Criteria:**
- [ ] Every bookmark URL from the input is represented in the tree
- [ ] Every bookmark title is preserved exactly (including special characters and Unicode)
- [ ] Every folder name and its nesting position is captured
- [ ] Bookmark metadata (add date, icon data, other attributes) is preserved
- [ ] Folder metadata (add date, last modified, toolbar flag) is preserved
- [ ] The parent-child relationship between folders and bookmarks matches the original file structure

**Priority:** High

### User Story 2: Immutable Transformation
**As a** user running `--dry-run`
**I want** the tool to show me what would change without actually changing anything
**So that** I can review the proposed cleanup before committing to it

**Acceptance Criteria:**
- [ ] Operations produce a new tree, leaving the original tree unchanged
- [ ] The original tree and the new tree can be compared to enumerate differences
- [ ] Multiple operations can be chained, each receiving the output of the previous
- [ ] No operation can accidentally modify a tree that was already created

**Priority:** High

### User Story 3: Tree Inspection
**As a** user running `bookmark-cleaner info`
**I want** to see a summary of my bookmark collection (total bookmarks, folder tree, duplicate count)
**So that** I understand the state of my bookmarks before and after cleanup

**Acceptance Criteria:**
- [ ] Total bookmark count can be computed from the tree
- [ ] Total unique URL count can be computed from the tree
- [ ] Folder count (including nested) can be computed from the tree
- [ ] A flat list of all bookmarks can be extracted from the tree regardless of nesting depth
- [ ] A list of all folder paths (e.g., "Favorites bar > Development > EveOnline") can be generated

**Priority:** Medium

### User Story 4: Equality and Comparison
**As a** developer writing tests
**I want** to compare two bookmark trees for structural equality
**So that** roundtrip tests (parse → export → reparse) can verify no data was lost

**Acceptance Criteria:**
- [ ] Two trees with identical structure and data compare as equal
- [ ] Two trees that differ in any bookmark URL, title, folder name, or nesting compare as not equal
- [ ] Metadata differences (dates, icons) are detectable but can be optionally ignored in comparison
- [ ] Comparison is not affected by internal IDs or object identity — only content matters

**Priority:** Medium

## Functional Requirements

### FR-1: Bookmark Node
**Description:** The system must represent an individual bookmark with all data from the source file.

**Acceptance Criteria:**
- [ ] A bookmark stores: URL, title, add date, icon data, and a flexible key-value store for any additional attributes
- [ ] All fields are read-only after creation
- [ ] Bookmarks with identical URLs and titles are considered content-equal
- [ ] A bookmark can be created with just a URL (all other fields have sensible defaults: empty title, no icon, zero date)

**Dependencies:** None

### FR-2: Folder Node
**Description:** The system must represent a bookmark folder containing zero or more bookmarks and zero or more subfolders.

**Acceptance Criteria:**
- [ ] A folder stores: name, add date, last modified date, a collection of child bookmarks, a collection of child folders, and a flexible key-value store for additional attributes
- [ ] All fields are read-only after creation
- [ ] A folder with no bookmarks and no subfolders is considered empty
- [ ] Folders support arbitrary nesting depth (folder within folder within folder)
- [ ] The ordering of bookmarks and subfolders within a folder is preserved from the source

**Dependencies:** FR-1

### FR-3: Bookmark Tree (Root Container)
**Description:** The system must provide a root container that holds the top-level folder structure and metadata about the source.

**Acceptance Criteria:**
- [ ] The tree stores the root folder(s) and the detected source format (e.g., "netscape", "chrome_json", "firefox_json")
- [ ] The tree can represent multiple root-level folders (as browsers do: bookmark bar, other bookmarks, mobile bookmarks)
- [ ] The tree is read-only after creation

**Dependencies:** FR-2

### FR-4: Tree Traversal Utilities
**Description:** The system must provide utilities for common tree queries and transformations.

**Acceptance Criteria:**
- [ ] A function collects all bookmarks across the entire tree into a flat list
- [ ] A function collects all unique URLs across the entire tree
- [ ] A function counts total bookmarks and total folders
- [ ] A function applies a transformation to every folder in the tree (bottom-up), producing a new tree
- [ ] A function creates a new folder with replaced bookmarks (leaving other fields unchanged)
- [ ] A function creates a new folder with replaced child folders (leaving other fields unchanged)
- [ ] A function finds a folder by name (case-insensitive) anywhere in the tree

**Dependencies:** FR-1, FR-2, FR-3

### FR-5: Structural Equality
**Description:** The system must support comparing two trees for content equality.

**Acceptance Criteria:**
- [ ] Two trees are equal if they have the same folder structure, same bookmarks in the same positions, with the same URLs and titles
- [ ] Equality comparison supports an option to ignore metadata (dates, icons) for roundtrip testing where parsers may normalize metadata
- [ ] Inequality produces a meaningful description of the first difference found

**Dependencies:** FR-1, FR-2, FR-3

## Non-Functional Requirements

### NFR-1: Correctness
- The model must handle bookmark collections of at least 10,000 bookmarks and 500 folders without errors
- Unicode titles, URLs with query strings, and URLs with special characters must be represented without corruption
- Folder nesting depth of at least 20 levels must be supported

### NFR-2: Immutability Guarantee
- It must not be possible to modify any field of a bookmark or folder after creation through the public interface
- Attempting to set an attribute on a frozen node must raise an error

### NFR-3: Simplicity
- The model should consist of no more than 3 core types (bookmark, folder, tree)
- Utility functions should be standalone functions, not methods on a base class hierarchy
- No abstract base classes or metaclasses — use frozen dataclasses and typing.Protocol only where needed

## Edge Cases & Error Handling

### Edge Case 1: Empty Bookmark File
**Situation:** User provides a bookmark file with no bookmarks and no folders
**Expected Behavior:** The tree is valid with an empty root folder. Traversal utilities return empty collections. Counts return zero.

### Edge Case 2: Deeply Nested Folders
**Situation:** Bookmark file has folders nested 20+ levels deep
**Expected Behavior:** The tree faithfully represents all nesting levels. No stack overflow or recursion limit on typical Python configurations (default recursion limit ~1000).

### Edge Case 3: Bookmarks with No Title
**Situation:** Some bookmarks have an empty title (common with quick-saved mobile bookmarks)
**Expected Behavior:** The bookmark is represented with an empty string title. It is not discarded or treated as invalid.

### Edge Case 4: Duplicate URLs in Different Folders
**Situation:** The same URL appears in multiple folders (this is normal in messy bookmark files)
**Expected Behavior:** Both bookmarks are represented separately in their respective folders. The "collect all bookmarks" utility returns all of them. The "unique URLs" utility returns the deduplicated set.

### Edge Case 5: Folders with Identical Names at Same Level
**Situation:** Two sibling folders share the same name (e.g., two "Social Media" folders inside "Favorites bar")
**Expected Behavior:** Both folders are represented separately. The model does not merge them — that is the job of a cleanup operation, not the data model.

### Edge Case 6: Special Characters in Folder Names and Titles
**Situation:** Folder names or bookmark titles contain HTML entities (`&amp;`), Unicode characters, or emoji
**Expected Behavior:** The model stores the decoded/unescaped text. Entity escaping is the exporter's responsibility, not the model's.

### Edge Case 7: Very Large Icon Data
**Situation:** A bookmark has a base64-encoded ICON attribute that is 50KB+
**Expected Behavior:** The model stores it as-is. Icon stripping is the job of a cleanup operation.

### Error Handling
- **Invalid construction:** If a bookmark is created with a non-string URL or a folder with a non-string name, a clear error should be raised at creation time
- **Mutation attempts:** Attempting to modify a frozen node should raise `FrozenInstanceError` (standard dataclass behavior)

## Clarifications Needed

None — this feature has clear requirements derived from the constitution (Article VII) and the PRD parsing/export requirements.

## Success Metrics

- Roundtrip fidelity: a tree constructed from parsing a file, when exported and reparsed, produces an equal tree (validated in Feature 3 integration tests)
- All 4 sample bookmark files can be represented without data loss
- Zero mutations possible through public API
- Tree traversal utilities work correctly on trees with 0, 1, 100, and 10,000 bookmarks

## Out of Scope

Explicitly excluded from this feature:
- **Parsing** — how to construct the tree from a file (Feature 3: Netscape Parser)
- **Exporting** — how to write the tree to a file (Feature 3: Netscape Exporter)
- **Operations** — dedup, merge, sort, etc. (Feature 4: Cleanup Operations)
- **Classification** — assigning bookmarks to folders (Feature 6: Keyword Classifier)
- **Serialization** — the model does not need to serialize itself to JSON/TOML/etc.
- **Change tracking** — the operation result type (tree + change log) is defined in Feature 4, not here

## References

- PRD: `PRD.md` — FR-1, FR-2 (parsing/export foundations)
- Constitution: `.specify/memory/constitution.md` — Article VII (Immutable Data Model)
- Roadmap: `.specify/roadmap.md` — Feature 1

---

## Validation Checklist

Before moving to planning phase:

- [x] All user stories have clear acceptance criteria
- [x] Requirements are testable and measurable
- [x] No implementation details in specification
- [x] Edge cases documented (7 cases)
- [x] Non-functional requirements defined
- [x] 0 `[NEEDS CLARIFICATION]` markers remaining
- [x] Success metrics defined
- [x] Out of scope items documented
