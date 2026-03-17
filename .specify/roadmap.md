# Implementation Roadmap: bookmark-cleaner

**PRD Source:** `PRD.md`
**Constitution:** `.specify/memory/constitution.md` v1.0.0
**Created:** 2026-03-17

## Executive Summary

**Product:** bookmark-cleaner — open-source Python CLI for cleaning, deduplicating, and organizing browser bookmarks
**Total Features:** 10
**Phases:** 4
**Critical Path:** Feature 1 → Feature 3 → Feature 4 → Feature 5 → Feature 7

## Feature Inventory

### Feature 1: Immutable Bookmark Tree Model
**Source:** FR-1 (parsing foundation), FR-2 (export foundation), Constitution Art. VII
**Description:** Frozen dataclass tree model (BookmarkNode, FolderNode, BookmarkTree) with tree traversal utilities. The foundation every other feature builds on.
**Complexity:** Small
**Priority:** P0 (Critical — blocks everything)

### Feature 2: Project Scaffolding & Packaging
**Source:** NFR-3, Constitution Art. I, Art. VI
**Description:** pyproject.toml, hatchling build, CLI entry point, dependency declarations (core vs extras), `pip install` / `uvx` support. Includes ruff, mypy, pytest config.
**Complexity:** Small
**Priority:** P0 (Critical — needed for any runnable code)

### Feature 3: Netscape HTML Parser & Exporter
**Source:** FR-1.1, FR-1.4, FR-2.1, FR-2.3, Constitution Art. VIII
**Description:** HTMLParser-based parser for Netscape bookmark HTML. Exporter producing valid, well-indented HTML with proper entity escaping. Auto-format detection. Roundtrip fidelity tests against real browser exports.
**Complexity:** Medium
**Priority:** P0 (Critical — Netscape HTML is the universal format, covers 90%+ of users)

### Feature 4: Cleanup Operations Pipeline
**Source:** FR-3 (dedup), FR-4 (folder cleanup), FR-6 (sort/format), Constitution Art. VII
**Description:** Composable pipeline of pure-function operations, each returning a new tree + change log:
- URL deduplication with normalization (FR-3.1, FR-3.2)
- Merge duplicate folders (FR-4.1, FR-4.2)
- Unwrap import wrappers (FR-4.3)
- Dissolve generic folders (FR-4.4)
- Remove empty folders (FR-4.5)
- Alphabetical sorting (FR-6.1)
- Strip oversized icons (FR-6.2)
**Complexity:** Large
**Priority:** P0 (Critical — this IS the core product)

### Feature 5: CLI Interface (clean, info, validate)
**Source:** FR-9.1, FR-9.5, FR-9.7, FR-8.1, Constitution Art. I, Art. IV
**Description:** Typer CLI with three core commands:
- `clean` — run cleanup pipeline with `--dry-run`, `--output`, `--operations` flags
- `info` — display file stats, folder tree, duplicate count
- `validate` — structure validation (balanced tags, unique URLs, no empty folders)
Rich terminal output with colored tables and tree visualization. Non-destructive: always writes to separate output file.
**Complexity:** Medium
**Priority:** P0 (Critical — user-facing entry point)

### Feature 6: Keyword/Domain Bookmark Classifier
**Source:** FR-5.1, FR-5.2, FR-5.3, FR-5.5, Constitution Art. III
**Description:** Weighted scoring classifier using domain matching, keyword matching, and specificity preferences. Built-in default profiles shipped as Python dicts. `classify` CLI command. Configurable via optional TOML override file.
**Complexity:** Medium
**Priority:** P1 (High — major differentiator, but tool is useful without it)

### Feature 7: Configuration System
**Source:** FR-10.1, FR-10.3, FR-4.6, Constitution Art. I, Art. III
**Description:** Optional TOML config file for overriding defaults (dedup strategy, canonical names, wrapper patterns, icon threshold, classifier options). CLI flags override config. Zero config required — all defaults in code.
**Complexity:** Small
**Priority:** P1 (High — needed for customization, but defaults work without it)

### Feature 8: Chrome JSON & Firefox JSON Parsers
**Source:** FR-1.2, FR-1.3, FR-1.4, FR-2.2, FR-2.3
**Description:** Chrome native Bookmarks JSON parser/exporter. Firefox bookmarks backup JSON parser. Format auto-detection. Roundtrip tests. `convert` CLI command.
**Complexity:** Medium
**Priority:** P2 (Nice to have — Netscape HTML covers all browsers already since they all export to it)

### Feature 9: Dead Link Checker
**Source:** FR-7.2, Constitution Art. I (optional extra)
**Description:** Async HTTP HEAD/GET checking of bookmark URLs using httpx. Configurable timeout and concurrency. Reports dead/redirected/unreachable without removing. Declared as pip extra `bookmark-cleaner[links]`.
**Complexity:** Medium
**Priority:** P2 (Nice to have — useful but not core cleanup)

### Feature 10: LLM-Assisted Classification
**Source:** FR-5.4, FR-5.6, Constitution Art. I (optional extra), Art. IV
**Description:** Optional classifier using Claude or OpenAI APIs for bookmarks below keyword threshold. Batch API calls. Cost estimation before execution. Plugin entry point system for third-party classifiers. Declared as pip extra `bookmark-cleaner[llm]`.
**Complexity:** Medium
**Priority:** P3 (Future — keyword classifier handles most cases)

## Dependency Graph

```
Feature 1 (Tree Model)       → Blocks: 3, 4, 6, 8
Feature 2 (Scaffolding)      → Blocks: 3, 4, 5, 6, 7, 8, 9, 10
Feature 3 (Netscape Parser)  → Blocks: 4, 5
Feature 4 (Operations)       → Blocks: 5
Feature 5 (CLI)              → Blocks: none (but enriched by 6, 7, 8, 9, 10)
Feature 6 (Classifier)       → Blocks: 10
Feature 7 (Config)           → Blocks: none (enhances 4, 5, 6)
Feature 8 (JSON Parsers)     → Blocks: none (independent after Feature 1)
Feature 9 (Dead Links)       → Blocks: none (independent after Feature 2)
Feature 10 (LLM)             → Blocks: none (extends Feature 6)

Independent features (can parallelize):
- Feature 8 (JSON Parsers) — after Phase 1
- Feature 9 (Dead Links) — after Phase 1
```

## Implementation Phases

### Phase 1: Foundation (Features 1, 2, 3)
**Goal:** Runnable package that can parse and re-export Netscape bookmark files with zero data loss

**Features:**
1. Feature 1: Immutable Bookmark Tree Model (P0, Small)
2. Feature 2: Project Scaffolding & Packaging (P0, Small)
3. Feature 3: Netscape HTML Parser & Exporter (P0, Medium)

**Dependencies:** None
**Why this grouping:** Nothing useful can happen without a data model, a parser, and a runnable package. The roundtrip test (parse → export → reparse = equivalent) is the first real validation that the foundation works.
**Exit criteria:**
- `pip install -e .` works
- `bookmark-cleaner --help` shows version
- Roundtrip test passes on all sample files
- 80%+ coverage on models, parser, exporter

### Phase 2: Core Value (Features 4, 5)
**Goal:** The tool does what it promises — cleans messy bookmark files

**Features:**
4. Feature 4: Cleanup Operations Pipeline (P0, Large)
5. Feature 5: CLI Interface — clean, info, validate (P0, Medium)

**Dependencies:** Phase 1 complete
**Why this grouping:** Operations + CLI together make the tool usable end-to-end. The `clean` command running the full pipeline on a real file is the core value proposition.
**Exit criteria:**
- `bookmark-cleaner clean favorites_3_17_26.html --dry-run` shows accurate preview
- `bookmark-cleaner clean favorites_3_17_26.html` produces output matching our manual cleanup (2503 → 970 bookmarks, 131 → ~28 folders)
- `bookmark-cleaner info` shows folder tree with counts
- `bookmark-cleaner validate` reports structural issues
- 80%+ coverage on all operations

### Phase 3: Intelligence (Features 6, 7)
**Goal:** The tool organizes loose bookmarks into meaningful categories

**Features:**
6. Feature 6: Keyword/Domain Bookmark Classifier (P1, Medium)
7. Feature 7: Configuration System (P1, Small)

**Dependencies:** Phase 2 complete
**Why this grouping:** Classification needs working operations to be testable. Config enhances both operations and classification. Together they make the tool smart and customizable.
**Exit criteria:**
- `bookmark-cleaner classify` sorts 70%+ of loose bookmarks into correct folders
- Optional TOML config overrides defaults
- CLI flags override config
- Built-in profiles cover common categories
- 80%+ coverage

### Phase 4: Extras (Features 8, 9, 10)
**Goal:** Broader format support and advanced features

**Features:**
8. Feature 8: Chrome JSON & Firefox JSON Parsers (P2, Medium)
9. Feature 9: Dead Link Checker (P2, Medium)
10. Feature 10: LLM-Assisted Classification (P3, Medium)

**Dependencies:** Phase 1 for Feature 8; Phase 1 for Feature 9; Phase 3 for Feature 10
**Why this grouping:** All optional/nice-to-have features. Can be implemented in any order. Features 8 and 9 can start as soon as Phase 1 completes.
**Exit criteria:**
- Chrome JSON and Firefox JSON roundtrip tests pass
- `bookmark-cleaner convert` works between all format pairs
- `bookmark-cleaner validate --check-links` reports dead URLs
- LLM classifier handles bookmarks below keyword threshold
- Plugin entry point system works for third-party classifiers

## Risk Assessment

### Feature 3: Netscape HTML Parser
**Technical Risk:** Medium — Browser-exported HTML is inconsistent. Chrome, Firefox, Edge, and Brave each produce slightly different markup. Multi-line attributes, missing closing tags, and HTML entities are common edge cases.
**Mitigation:** Collect real export files from each browser for the test fixture set. Use stdlib HTMLParser (event-driven, handles malformed HTML) instead of regex. Test against all sample files in integration tests.

### Feature 4: Cleanup Operations
**Technical Risk:** Low-Medium — The folder merging logic (especially import wrapper unwrapping with nested duplicate names) was the hardest part of our ad-hoc scripts. The immutable model makes it safer but requires careful tree traversal.
**Mitigation:** Port logic from existing `clean_bookmarks.py` which already handles these cases. Extensive test fixtures covering nested duplicates, import wrappers, and edge cases.

### Feature 6: Keyword Classifier
**Technical Risk:** Low — The scoring system from `sort_bookmarks.py` already works well (334/491 bookmarks correctly classified). Main risk is profile quality, not algorithm.
**Mitigation:** Ship the battle-tested profiles from our existing scripts. Allow users to override with TOML config.

### Feature 8: JSON Parsers
**Technical Risk:** Low — Chrome and Firefox JSON formats are well-documented and simple to parse. JSON is unambiguous unlike HTML.
**Mitigation:** Collect real JSON files from Chrome and Firefox for test fixtures.

### Feature 9: Dead Link Checker
**Technical Risk:** Medium — False positives from sites blocking HEAD requests, rate limiting, and geo-blocking. Slow for large collections.
**Mitigation:** Fall back HEAD → GET. Browser-like User-Agent. Report as "possibly dead" not "dead". Configurable concurrency and timeout. Never auto-remove — report only.

### Feature 10: LLM Classification
**Technical Risk:** Low-Medium — API costs, rate limits, response parsing. User needs API key.
**Mitigation:** Cost estimation before execution. Batch requests. Only send bookmarks below keyword threshold. Pip extra so most users never install it.

## Constitutional Compliance Validation

### Article I: Lightweight-First
- [x] Core features (1-5) use only stdlib + typer + rich
- [x] httpx (Feature 9) and anthropic/openai (Feature 10) declared as pip extras
- [x] Zero config required — sensible defaults for everything
- [x] Built-in profiles as Python dicts (Feature 6), not external files

### Article II: Test-First Imperative
- [x] Every phase has explicit coverage requirements (80%+)
- [x] Roundtrip tests required for all parsers
- [x] Data loss prevention tests on all operations
- [x] Real-world sample files used in integration tests

### Article III: Simplicity Enforcement
- [x] Single Python package
- [x] No premature abstractions — operations are simple functions
- [x] Plugin system only where justified (classifiers)

### Article IV: Non-Destructive Operation & Data Safety
- [x] Output always to separate file
- [x] Dry-run as encouraged workflow
- [x] No network without explicit opt-in
- [x] No telemetry
- **NOTE:** PRD FR-8.2 (automatic backup) conflicts with Art. IV ("no writing outside explicit output path"). **Resolution:** Drop auto-backup. The tool already never modifies the input file, making backup unnecessary. Users keep their original.

### Article V: No Formal Performance SLAs
- [x] No performance features in roadmap
- [x] Correctness and simplicity prioritized

### Article VI: Technology Constraints
- [x] All approved technologies used
- [x] HTMLParser for HTML parsing (no BeautifulSoup)
- [x] hatchling packaging

### Article VII: Immutable Data Model
- [x] Feature 1 establishes immutable tree
- [x] Feature 4 operations return new trees + change logs
- [x] Dry-run powered by change logs, not separate code path

### Article VIII: Browser Compatibility
- [x] Feature 3 includes browser import tests
- [x] Entity escaping in exporter
- [x] Attribute preservation

**Status:** Roadmap complies with all constitutional articles. One PRD conflict resolved (FR-8.2 dropped).

## Roadmap Execution Checklist

### Pre-Implementation
- [x] PRD reviewed
- [x] Constitution ratified (v1.0.0)
- [x] Features identified and numbered (10)
- [x] Dependencies mapped
- [x] Priorities assigned
- [x] Phases defined
- [x] Constitutional compliance verified

### Phase 1: Foundation
- [ ] Feature 1: Immutable Bookmark Tree Model
  - [ ] `/speckit-specify 1-tree-model`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 2: Project Scaffolding & Packaging
  - [ ] `/speckit-specify 2-project-scaffolding`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 3: Netscape HTML Parser & Exporter
  - [ ] `/speckit-specify 3-netscape-parser`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- **Phase 1 Gate:** Roundtrip test passes, `pip install -e .` works, 80%+ coverage

### Phase 2: Core Value
- [ ] Feature 4: Cleanup Operations Pipeline
  - [ ] `/speckit-specify 4-cleanup-operations`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 5: CLI Interface
  - [ ] `/speckit-specify 5-cli-interface`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- **Phase 2 Gate:** `bookmark-cleaner clean` produces correct output on real files, 80%+ coverage

### Phase 3: Intelligence
- [ ] Feature 6: Keyword/Domain Classifier
  - [ ] `/speckit-specify 6-keyword-classifier`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 7: Configuration System
  - [ ] `/speckit-specify 7-configuration`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- **Phase 3 Gate:** 70%+ classification accuracy, config overrides work, 80%+ coverage

### Phase 4: Extras
- [ ] Feature 8: Chrome JSON & Firefox JSON Parsers
  - [ ] `/speckit-specify 8-json-parsers`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 9: Dead Link Checker
  - [ ] `/speckit-specify 9-dead-link-checker`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- [ ] Feature 10: LLM-Assisted Classification
  - [ ] `/speckit-specify 10-llm-classifier`
  - [ ] `/speckit-plan`
  - [ ] `/speckit-tasks`
  - [ ] `/speckit-implement`
- **Phase 4 Gate:** All format roundtrips pass, dead link checker reports accurately, plugin system works

### Post-Implementation
- [ ] GitHub repository created
- [ ] README with usage examples
- [ ] LICENSE file (MIT)
- [ ] PyPI package published
- [ ] GitHub Actions CI (test + lint + type-check)
- [ ] Sample bookmark files in test fixtures

## Next Steps

Start with Phase 1, Feature 1:
```bash
/speckit-specify 1-tree-model
```
