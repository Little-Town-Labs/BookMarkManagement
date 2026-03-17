# Feature Specification: Cleanup Operations Pipeline

**Feature Number:** 4
**Branch:** 4-cleanup-operations
**Status:** Draft
**Created:** 2026-03-17
**Last Updated:** 2026-03-17

## Overview

The cleanup operations pipeline is the core value proposition of bookmark-cleaner. It takes a messy bookmark tree — riddled with duplicate URLs, redundant import wrapper folders, duplicate folder names, generic "New folder" placeholders, and empty folders — and produces a clean, well-organized tree with every unique URL preserved.

Each operation is a pure function: it takes a tree and returns a new tree plus a structured change log. Operations are composable and can be run individually or as a pipeline. The change log is what powers `--dry-run` — there is no separate preview code path.

In a real-world test with 2,503 bookmarks across 131 folders, the pipeline reduces to ~970 unique bookmarks across ~28 meaningful folders by removing 1,533 duplicates, unwrapping 11 import wrapper folders, merging 20+ duplicate folder names, dissolving 7 generic folders, and removing 31 empty folders.

## User Stories

### User Story 1: Remove Duplicate Bookmarks
**As a** user with years of accumulated bookmarks
**I want** duplicates removed while keeping the best version of each URL
**So that** my bookmark collection contains only unique, useful links

**Acceptance Criteria:**
- [ ] Bookmarks sharing the same normalized URL are identified as duplicates
- [ ] URL normalization treats http/https, trailing slashes, and hostname case as equivalent
- [ ] When duplicates exist, the bookmark with the most recent add date is kept by default
- [ ] The user can choose an alternative retention strategy (oldest, longest title)
- [ ] The change log reports exactly how many duplicates were removed and lists affected URLs
- [ ] Every unique URL from the input exists in the output (zero data loss)

**Priority:** High

### User Story 2: Merge Duplicate Folders
**As a** user whose bookmarks contain the same folder name appearing multiple times (e.g., "Social Media" appears 9 times)
**I want** identically-named folders merged into one
**So that** each category exists exactly once

**Acceptance Criteria:**
- [ ] Folders with the same name (case-insensitive) at the same nesting level are merged into one folder
- [ ] Merging combines bookmarks from all duplicate folders into the surviving folder
- [ ] Merging combines subfolders from all duplicate folders, recursively merging nested duplicates
- [ ] The surviving folder retains the earliest add date and latest last-modified date
- [ ] The change log reports each merge: which folders were combined and how many bookmarks moved

**Priority:** High

### User Story 3: Unwrap Import Wrappers
**As a** user who has switched browsers multiple times, creating "Imported from Chrome", "Imported from Chrome (2)", etc. wrapper folders
**I want** those wrapper folders dissolved, lifting their contents into the parent structure
**So that** my bookmarks are organized by topic, not by import history

**Acceptance Criteria:**
- [ ] Folders matching known import wrapper patterns are identified (e.g., "Imported from Chrome", "Imported From Google Chrome", "Imported from Edge", numbered variants)
- [ ] The wrapper folder's children and bookmarks are moved into the wrapper's parent folder
- [ ] If the wrapper contains subfolders that match existing folders in the parent, they are merged by name
- [ ] The change log reports each unwrapped folder and how many items were lifted
- [ ] The wrapper patterns are configurable (not hardcoded)

**Priority:** High

### User Story 4: Dissolve Generic Folders
**As a** user with multiple "New folder", "New folder (2)", and similar placeholder folders
**I want** those dissolved into their parent folder
**So that** bookmarks are not hidden inside meaningless containers

**Acceptance Criteria:**
- [ ] Folders matching generic name patterns are identified (e.g., "New folder", "New folder (2)", "Untitled folder")
- [ ] The generic folder's bookmarks and children are moved into its parent
- [ ] The generic folder patterns are configurable
- [ ] The change log reports each dissolved folder

**Priority:** Medium

### User Story 5: Remove Empty Folders
**As a** user
**I want** folders containing no bookmarks and no subfolders to be removed
**So that** my folder tree is clean and meaningful

**Acceptance Criteria:**
- [ ] After all other operations, folders with zero bookmarks and zero children are removed
- [ ] Removal is recursive: if removing a folder makes its parent empty, the parent is also removed
- [ ] The change log reports each removed folder path
- [ ] The root folder is never removed, even if empty

**Priority:** Medium

### User Story 6: Sort Bookmarks and Folders
**As a** user
**I want** my bookmarks and folders sorted alphabetically
**So that** I can find items quickly when browsing the imported tree

**Acceptance Criteria:**
- [ ] Folders within each parent are sorted alphabetically (case-insensitive)
- [ ] Bookmarks within each folder are sorted alphabetically by title (case-insensitive)
- [ ] Sorting is stable: items with identical names retain their original relative order
- [ ] The change log reports how many items were reordered

**Priority:** Medium

### User Story 7: Strip Oversized Icons
**As a** user whose bookmark file is bloated with embedded icon data
**I want** oversized base64-encoded icons removed
**So that** the file size is manageable and import performance is fast

**Acceptance Criteria:**
- [ ] Bookmark icons exceeding a size threshold (default 2KB) are replaced with an empty string
- [ ] The threshold is configurable
- [ ] Icons below the threshold are preserved unchanged
- [ ] The change log reports how many icons were stripped and the total bytes saved

**Priority:** Low

## Functional Requirements

### FR-1: Operation Result Type
**Description:** Every cleanup operation must return a consistent result containing the new tree and a change log.

**Acceptance Criteria:**
- [ ] Each operation returns both a new BookmarkTree and a structured list of changes
- [ ] Each change entry describes what happened (e.g., "removed duplicate", "merged folder")
- [ ] Change entries include enough detail for human-readable dry-run output (affected URLs, folder names, counts)
- [ ] The original tree passed to an operation is never modified

### FR-2: URL Deduplication
**Description:** Identify and remove bookmarks that share the same URL after normalization.

**Acceptance Criteria:**
- [ ] URL normalization: lowercase the scheme and hostname, strip trailing slash from path, sort query parameters alphabetically, treat http:// and https:// as equivalent
- [ ] When duplicates are found, keep the one with the most recent add_date (default strategy)
- [ ] Alternative strategies: keep oldest, keep the entry with the longest title
- [ ] Deduplication operates across the entire tree — duplicates in different folders are detected
- [ ] After dedup, the unique URL count equals the number of bookmarks remaining

### FR-3: Folder Merging
**Description:** Merge folders with the same name at the same nesting level.

**Acceptance Criteria:**
- [ ] Name comparison is case-insensitive ("Social Media" and "social media" are the same)
- [ ] Merging combines bookmarks from all matching folders into one
- [ ] Merging combines child folders, recursively merging nested duplicates
- [ ] The merged folder's add_date is the earliest among the duplicates
- [ ] The merged folder's last_modified is the latest among the duplicates
- [ ] Custom attributes from the first matching folder are preserved

### FR-4: Import Wrapper Unwrapping
**Description:** Detect and dissolve import wrapper folders, lifting their contents into the parent.

**Acceptance Criteria:**
- [ ] Default wrapper patterns detect: "Imported from Chrome", "Imported From Google Chrome", "Imported from Edge", "Imported from Firefox", "Imported from Safari", "Imported from Opera", and numbered variants like "(2)", "(3)"
- [ ] Wrapper detection is case-insensitive
- [ ] When unwrapping, the wrapper's children and bookmarks are added to the wrapper's parent
- [ ] If the wrapper's children overlap with existing folders in the parent, they are merged (invokes folder merging logic)

### FR-5: Generic Folder Dissolution
**Description:** Dissolve placeholder folders with generic names.

**Acceptance Criteria:**
- [ ] Default generic patterns detect: "New folder", "New folder (N)", "Untitled folder", "Untitled folder (N)"
- [ ] Generic detection is case-insensitive
- [ ] The generic folder's contents are moved to its parent
- [ ] If the generic folder's children overlap with existing siblings, they are merged

### FR-6: Empty Folder Removal
**Description:** Remove folders that contain no bookmarks and no subfolders.

**Acceptance Criteria:**
- [ ] A folder is empty if it has zero bookmarks and zero children
- [ ] Removal is applied bottom-up (leaf folders first) so cascading empties are caught
- [ ] The root folder is never removed

### FR-7: Alphabetical Sorting
**Description:** Sort folders and bookmarks alphabetically within each folder.

**Acceptance Criteria:**
- [ ] Folders are sorted by name (case-insensitive)
- [ ] Bookmarks are sorted by title (case-insensitive)
- [ ] Sorting is stable
- [ ] Sorting applies recursively to all levels

### FR-8: Icon Stripping
**Description:** Remove oversized embedded icon data from bookmarks.

**Acceptance Criteria:**
- [ ] Icons are measured by byte length of the icon string
- [ ] Icons exceeding the threshold are replaced with empty string
- [ ] Default threshold is 2048 bytes (2KB)
- [ ] The threshold is configurable

### FR-9: Pipeline Composition
**Description:** Operations must be composable into an ordered pipeline.

**Acceptance Criteria:**
- [ ] The default pipeline order is: unwrap wrappers, dissolve generics, merge folders, deduplicate URLs, strip icons, remove empty folders, sort
- [ ] Each operation's output tree feeds into the next operation's input
- [ ] Change logs from all operations are accumulated into a combined log
- [ ] Individual operations can be included or excluded from the pipeline
- [ ] The pipeline returns the final tree and the combined change log

## Non-Functional Requirements

### NFR-1: Data Safety
- Every unique URL in the input must be present in the output after the full pipeline
- URL count validation must run automatically after the pipeline completes
- If validation fails, the pipeline must report the discrepancy and refuse to write output

### NFR-2: Correctness
- Pipeline must produce identical results on the 4 real-world sample files each run (deterministic)
- `favorites_3_17_26.html`: 2503 bookmarks → ~970 unique URLs preserved
- The merge/unwrap operations must handle the 20+ duplicate folder names and 11 import wrappers in the sample files

### NFR-3: Composability
- Each operation must be independently testable
- Each operation must work correctly when run in isolation or as part of a pipeline
- Operations must not depend on execution order (though the default order produces best results)

## Edge Cases & Error Handling

### Edge Case 1: Bookmark URL is Only Difference
**Situation:** Two bookmarks have identical titles but different URLs
**Expected Behavior:** Both are kept (dedup is by URL, not title)

### Edge Case 2: Same URL, Different Folders
**Situation:** The same URL appears in "Development" and "Reference"
**Expected Behavior:** Only one copy is kept (in whichever folder has the more recent add_date entry). The change log notes the removal from the other folder.

### Edge Case 3: Nested Import Wrappers
**Situation:** "Imported from Chrome" contains "Imported from Chrome (2)" which contains actual bookmarks
**Expected Behavior:** Both wrapper levels are unwrapped. Bookmarks end up at the grandparent level.

### Edge Case 4: Circular Folder Merging
**Situation:** After unwrapping wrappers, folder "Social Media" now appears at the same level from two different sources
**Expected Behavior:** The merge operation combines them into one "Social Media" folder

### Edge Case 5: All Bookmarks are Duplicates of One URL
**Situation:** Extreme case where every bookmark in the file points to the same URL
**Expected Behavior:** One bookmark survives. All folders that become empty are removed.

### Edge Case 6: Canonical Name Collision
**Situation:** "BusinessTools" and "Business Tools" are considered the same folder name
**Expected Behavior:** They are merged. Canonical name mapping is configurable for Feature 7 (out of scope here — for now, use case-insensitive comparison only).

### Edge Case 7: Empty Tree Input
**Situation:** A tree with no bookmarks and no folders
**Expected Behavior:** Pipeline returns the tree unchanged with an empty change log

### Edge Case 8: Icon Exactly at Threshold
**Situation:** A bookmark icon is exactly 2048 bytes
**Expected Behavior:** It is preserved (threshold is strictly "exceeding", not "equal to")

### Edge Case 9: URL Normalization Edge Cases
**Situation:** URLs with fragments (#section), authentication info (user:pass@host), ports, or unicode characters
**Expected Behavior:** Fragments are preserved (different fragments = different bookmarks). Auth info is preserved. Port 80/443 is stripped for http/https. Unicode is preserved as-is.

### Edge Case 10: Wrapper Contains Only Empty Folders
**Situation:** "Imported from Chrome (5)" contains subfolders but no bookmarks at any level
**Expected Behavior:** After unwrapping and empty folder removal, nothing from this wrapper survives

### Error Handling
- **Invalid tree structure:** Operations must handle trees with any structure without crashing
- **URL parsing failure:** If a URL cannot be parsed for normalization, treat it as-is (no normalization, no crash)

## Clarifications Needed

None — the PRD is clear on all requirements, and the real-world sample files provide concrete validation targets.

## Success Metrics

- `favorites_3_17_26.html`: 2503 bookmarks → 970 unique bookmarks after full pipeline
- `favorites_3_17_26.html`: 131 folders → ~28 folders after full pipeline
- Zero unique URLs lost in any pipeline run (automated validation)
- All 11 import wrapper folders unwrapped
- All 31 empty folders removed
- All 7 generic "New folder" instances dissolved
- Deterministic: running the pipeline twice on the same input produces identical output

## Out of Scope

- **CLI interface** — Feature 5 (consumes this pipeline)
- **Bookmark classification** — Feature 6 (runs after cleanup)
- **Configuration system** — Feature 7 (provides configurable patterns; for now defaults are in code)
- **Canonical name mapping** — Feature 7 (beyond case-insensitive comparison)
- **Format conversion** — Feature 8
- **Dead link checking** — Feature 9

## References

- PRD: `PRD.md` — FR-3 (dedup), FR-4 (folder cleanup), FR-6 (sort/format)
- Constitution: `.specify/memory/constitution.md` — Art. IV (non-destructive), Art. VII (immutable + change logs)
- Roadmap: `.specify/roadmap.md` — Feature 4
- Feature 1: `.specify/specs/1-tree-model/spec.md` — tree model this operates on
- Sample data: `favorites_3_17_26.html` (2503 bookmarks, 131 folders, 970 unique URLs)

---

## Validation Checklist

Before moving to planning phase:

- [x] All user stories have clear acceptance criteria
- [x] Requirements are testable and measurable
- [x] No implementation details in specification
- [x] Edge cases documented (10 cases)
- [x] Non-functional requirements defined
- [x] 0 `[NEEDS CLARIFICATION]` markers remaining
- [x] Success metrics defined with concrete numbers from real data
- [x] Out of scope items documented
