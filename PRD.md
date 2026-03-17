# Product Requirements Document: bookmark-cleaner

## Executive Summary

**bookmark-cleaner** is an open-source Python CLI tool that cleans, deduplicates, and intelligently organizes browser bookmark files. It solves the universal problem of bookmark rot — years of accumulated duplicates, broken import wrappers, empty folders, and uncategorized links that make bookmark collections unusable.

## Problem Statement

Browser bookmarks accumulate entropy over time:

1. **Duplicate imports** — Every time a user switches browsers or syncs devices, Chrome/Edge/Firefox create "Imported from Chrome (2)", "Imported from Chrome (3)" wrapper folders containing identical copies of all bookmarks. A typical user who has switched browsers 3-4 times has 60-80% duplicate bookmarks.

2. **No deduplication** — Browsers do not detect or prevent duplicate URLs. The same link saved from different contexts appears in multiple folders.

3. **Folder chaos** — Duplicate folder names at different nesting levels (e.g., "Social Media" appearing 9 times), unnamed "New folder" placeholders, and empty folders from failed imports.

4. **Uncategorized bookmarks** — Mobile bookmarks, "Other bookmarks", and quick-saves accumulate without any folder organization. Users end up with hundreds of loose bookmarks that are effectively lost.

5. **Dead links** — Bookmarks saved years ago point to domains that no longer exist, pages that have moved, or services that have shut down.

6. **No tooling exists** — There is no widely-adopted, well-designed tool to solve this. Users either spend hours manually cleaning bookmarks or give up entirely.

### Evidence

In a real-world test with a user's Edge bookmark export:
- **2,503 total bookmarks**, but only **970 unique URLs** (61% duplicates)
- **131 folders**, but only **28 meaningful categories** (78% were duplicates/wrappers)
- **11 "Imported from Chrome"** wrapper folders from repeated browser migrations
- **340 loose bookmarks** with no folder assignment
- **31 empty folders**

## Target Users

1. **Power users** — People with 500+ bookmarks accumulated over years who want to clean up and organize their collection before importing into a new browser.
2. **Browser switchers** — Users migrating between Chrome, Firefox, Edge, Brave, or Safari who need to merge and deduplicate imported bookmarks.
3. **Digital organizers** — Users who periodically want to audit, prune, and categorize their bookmarks.
4. **Developers/sysadmins** — Technical users who want scriptable, automatable bookmark management as part of a setup or migration workflow.

## Goals

1. Reduce a typical messy bookmark file by 50-70% while preserving every unique URL
2. Produce clean, well-structured output that imports perfectly into any major browser
3. Provide a transparent, previewable process (users see exactly what will change before committing)
4. Support the three major bookmark formats (Netscape HTML, Chrome JSON, Firefox JSON)
5. Make classification extensible so users can define their own folder categories and rules
6. Be installable via `pip install bookmark-cleaner` or `uvx bookmark-cleaner`

## Non-Goals

1. Real-time browser extension or sync tool — this is a batch processing CLI
2. Cloud service or hosted SaaS — this runs locally on the user's machine
3. Bookmark manager or reader — this is a cleanup/organization tool, not a daily driver
4. Automatic backup management — users are responsible for keeping their original files
5. Social/sharing features — no accounts, no sharing, no telemetry

## Functional Requirements

### FR-1: Bookmark File Parsing

The tool must parse bookmark files from the three major formats:

- **FR-1.1**: Netscape Bookmark HTML — The universal export format supported by all browsers (Chrome, Firefox, Edge, Brave, Safari, Opera). Must handle malformed HTML, missing closing tags, multi-line attributes, HTML entities, and base64-encoded ICON data.
- **FR-1.2**: Chrome JSON — Chrome's native `Bookmarks` file (JSON with `roots.bookmark_bar`, `roots.other`, `roots.synced` nodes, Windows epoch timestamps).
- **FR-1.3**: Firefox JSON — Firefox's `bookmarks-YYYY-MM-DD.json` backup format (`text/x-moz-place` for bookmarks, `text/x-moz-place-container` for folders).
- **FR-1.4**: Auto-detection — The tool must automatically detect the input format based on file content, not just extension.

### FR-2: Bookmark File Export

- **FR-2.1**: Netscape HTML export — Valid, well-indented HTML that imports cleanly into Chrome, Firefox, Edge, and Brave. Must preserve ADD_DATE, ICON, and other standard attributes.
- **FR-2.2**: Chrome JSON export — Valid Chrome Bookmarks JSON file.
- **FR-2.3**: Roundtrip fidelity — Parsing and re-exporting a file in the same format must not lose any bookmark data (URLs, titles, dates, icons, folder structure).

### FR-3: Deduplication

- **FR-3.1**: URL deduplication — Remove duplicate bookmarks sharing the same URL. Keep the entry with the most recent ADD_DATE (configurable: newest, oldest, longest title).
- **FR-3.2**: URL normalization — Treat equivalent URLs as duplicates: normalize scheme (http/https), strip trailing slashes, lowercase hostname, sort query parameters.
- **FR-3.3**: Dedup reporting — Report exactly how many duplicates were found and removed, with a list of affected URLs.

### FR-4: Folder Cleanup

- **FR-4.1**: Merge duplicate folders — Folders with the same name (case-insensitive) at the same nesting level must be merged into one, combining their bookmarks and subfolders.
- **FR-4.2**: Canonical folder names — Configurable name normalization (e.g., "business tools" and "BusinessTools" map to the same canonical name).
- **FR-4.3**: Unwrap import wrappers — Detect and unwrap "Imported from Chrome", "Imported from Edge", "Imported From Google Chrome", and numbered variants. Lift their contents into the parent structure, merging with existing folders by name.
- **FR-4.4**: Dissolve generic folders — Merge "New folder", "New folder (2)", etc. into their parent folder.
- **FR-4.5**: Remove empty folders — After all merging/moving operations, remove any folders that contain no bookmarks and no subfolders.
- **FR-4.6**: Configurable wrapper patterns — The list of import wrapper patterns and generic folder names must be configurable, not hardcoded.

### FR-5: Bookmark Classification

- **FR-5.1**: Keyword/domain classification — Score uncategorized bookmarks against folder profiles using URL domain matching, title keyword matching, and URL path analysis. Assign to the highest-scoring folder above a configurable confidence threshold.
- **FR-5.2**: Folder profiles — User-configurable TOML files defining folder categories with: strong keywords (high weight), regular keywords (medium weight), title-only keywords (lower weight), and domain overrides (highest weight, exact match).
- **FR-5.3**: Specificity preference — When a bookmark matches multiple categories with similar scores, prefer the more specific category (e.g., "Deep Learning" over "Development").
- **FR-5.4**: LLM-assisted classification — Optional integration with Claude or OpenAI APIs to classify bookmarks that fall below the keyword classifier's confidence threshold. Must show estimated API cost before execution.
- **FR-5.5**: Uncategorized fallback — Bookmarks that cannot be classified with sufficient confidence go into a configurable "Other" folder rather than being lost.
- **FR-5.6**: Plugin classifiers — Third-party classifiers can be registered via Python entry points without modifying the core package.

### FR-6: Sorting and Formatting

- **FR-6.1**: Alphabetical sorting — Sort folders and bookmarks alphabetically (case-insensitive) within each folder level.
- **FR-6.2**: Icon optimization — Strip base64-encoded ICON data exceeding a configurable size threshold (default 2KB) to reduce file size.
- **FR-6.3**: Consistent indentation — Output files use consistent 4-space indentation for readability.

### FR-7: Validation

- **FR-7.1**: Structure validation — Verify balanced HTML tags (DL open/close), unique URLs (no remaining duplicates), no empty folders, no duplicate folder names at the same level.
- **FR-7.2**: Dead link checking — Optional HTTP HEAD/GET check of all bookmark URLs with configurable timeout and concurrency. Report dead, redirected, and unreachable URLs without automatically removing them.
- **FR-7.3**: Validation reporting — Output a structured report (text or JSON) with bookmark counts, folder counts, duplicate counts, empty folders, and structural issues.

### FR-8: Preview and Safety

- **FR-8.1**: Dry-run mode — Run the full pipeline and display what would change (bookmarks removed, folders merged, bookmarks moved) without modifying any files.
- **FR-8.2**: Automatic backup — Before writing any output file, create a timestamped backup of the original input file (configurable, enabled by default).
- **FR-8.3**: Diff output — Compare two bookmark files and display structural differences (added/removed/moved bookmarks and folders).

### FR-9: CLI Interface

- **FR-9.1**: `clean` command — Run the full cleanup pipeline (unwrap, merge, dedup, strip-icons, remove-empty, sort). Configurable operation selection and order.
- **FR-9.2**: `classify` command — Run bookmark classification separately with strategy selection (keyword, rule-based, LLM).
- **FR-9.3**: `validate` command — Run structural validation and optional dead link checking.
- **FR-9.4**: `convert` command — Convert between supported bookmark formats.
- **FR-9.5**: `info` command — Display bookmark file statistics: format, bookmark count, folder tree with counts, duplicate count, empty folders.
- **FR-9.6**: `diff` command — Compare two bookmark files structurally.
- **FR-9.7**: Rich output — Colored terminal output with progress bars for long operations, folder tree visualization, and clear summary tables.

### FR-10: Configuration

- **FR-10.1**: TOML configuration file — All settings (dedup strategy, canonical names, wrapper patterns, classifier options, icon size threshold) in a single config file with sensible defaults.
- **FR-10.2**: Folder profiles — Separate TOML file(s) defining folder categories, keywords, and domain overrides.
- **FR-10.3**: CLI overrides — All config options overridable via CLI flags.
- **FR-10.4**: Default profiles — Ship with a default profile covering common bookmark categories (development, business, social media, gaming, news, etc.).

## Non-Functional Requirements

### NFR-1: Performance
- Must process a 10,000-bookmark file in under 10 seconds (excluding network operations like dead link checking)
- Dead link checking must support configurable concurrency (default 20 concurrent requests)

### NFR-2: Compatibility
- Python 3.10+ support
- Cross-platform: Linux, macOS, Windows
- Output files must import successfully into Chrome 120+, Firefox 120+, Edge 120+, Brave 1.60+

### NFR-3: Installability
- Installable via `pip install bookmark-cleaner`
- Runnable via `uvx bookmark-cleaner` without installation
- Zero required runtime dependencies beyond Python stdlib where possible; optional dependencies for LLM classification and dead link checking

### NFR-4: Extensibility
- Custom classifiers via Python entry points
- Custom operations via Python entry points
- Profile files can be shared independently of the tool

### NFR-5: Reliability
- 80%+ test coverage (unit + integration + e2e)
- Roundtrip parsing tests for all supported formats
- No data loss — every unique URL in the input must appear in the output
- Graceful handling of malformed input files with clear error messages

### NFR-6: Security
- No telemetry or data collection
- LLM classification sends only bookmark titles and URLs (no icons, no file paths, no user data)
- API keys read from environment variables, never from config files
- No network requests unless explicitly invoked (dead link checking, LLM classification)

## Technical Constraints

- **Language**: Python 3.10+
- **CLI framework**: Typer (type-hint driven, auto-completion support)
- **Output formatting**: Rich (colored output, tables, trees, progress bars)
- **Config format**: TOML (human-readable, stdlib support in 3.11+)
- **HTTP client**: httpx (async support for concurrent dead link checking)
- **Testing**: pytest with pytest-cov
- **Linting**: ruff
- **Type checking**: mypy
- **Packaging**: pyproject.toml with hatchling or setuptools

## Success Metrics

1. Can clean a real-world 2,500-bookmark file down to ~970 unique bookmarks across ~28 well-organized folders (matching our manual results)
2. Cleaned output imports successfully into Chrome, Firefox, and Edge without errors
3. `--dry-run` accurately predicts all changes made by the actual run
4. Keyword classifier correctly categorizes 70%+ of previously-uncategorized bookmarks
5. Roundtrip test passes for all three formats (parse -> export -> reparse = equivalent tree)
6. 80%+ test coverage
7. `pip install bookmark-cleaner && bookmark-cleaner clean bookmarks.html` works on a fresh machine

## Appendix: Sample Data

The following real-world files are available for testing and development:

| File | Source | Bookmarks | Unique URLs | Folders |
|---|---|---|---|---|
| `favorites_3_17_26.html` | Edge export (raw) | 2,503 | 970 | 131 |
| `favorites_3_17_26_cleaned.html` | After cleanup | 970 | 970 | 28 |
| `bookmarks_1_23_26.html` | Chrome export (raw) | ~2,200 | ~880 | ~100 |
| `bookmarks_cleaned.html` | After cleanup | ~880 | ~880 | ~20 |

## Appendix: Competitive Landscape

No widely-adopted open-source tool exists for this problem. Existing options:
- **Browser built-in**: No dedup, no classification, no merge across imports
- **Online bookmark managers** (Raindrop.io, Pocket): Require uploading bookmarks to a third-party cloud service
- **One-off scripts on GitHub**: Fragmented, unmaintained, handle only dedup or only one format
- **Manual cleanup**: Hours of tedious work that most users never complete

bookmark-cleaner fills a clear gap as a local, privacy-respecting, comprehensive CLI tool.
