# Implementation Roadmap: bookmark-cleaner

**PRD Source:** `PRD.md`
**Constitution:** `.specify/memory/constitution.md` v1.0.0
**Created:** 2026-03-17
**Revised:** 2026-03-17 — Trimmed from 10 features to 5 for v1.0

## Executive Summary

**Product:** bookmark-cleaner — open-source Python CLI for cleaning, deduplicating, and organizing browser bookmarks
**Total Features:** 5 (v1.0 scope)
**Critical Path:** Feature 1 → Feature 3 → Feature 4 → Feature 5

## v1.0 Feature Inventory

### Feature 1: Immutable Bookmark Tree Model
**Status:** ✅ Complete
**Description:** Frozen dataclass tree model (BookmarkNode, FolderNode, BookmarkTree) with tree traversal utilities.

### Feature 2: Project Scaffolding & Packaging
**Status:** ⚠️ Partial (pyproject.toml exists, CLI entry point needed)
**Description:** pyproject.toml, hatchling build, CLI entry point, `pip install` / `uvx` support.

### Feature 3: Netscape HTML Parser & Exporter
**Status:** ✅ Complete
**Description:** HTMLParser-based parser, exporter with entity escaping, format auto-detection, roundtrip fidelity.

### Feature 4: Cleanup Operations Pipeline
**Status:** ✅ Complete
**Description:** 7 composable pure-function operations (dedup, merge folders, unwrap wrappers, dissolve generics, remove empties, strip icons, sort) with change logs.

### Feature 5: CLI Interface
**Status:** Not started
**Description:** Typer CLI with `clean` and `info` commands. Rich terminal output. `--dry-run` support.

## Deferred to v2.0+ (only if users request)

- Keyword/domain bookmark classifier
- Configuration system (TOML config file)
- Chrome JSON & Firefox JSON parsers
- Dead link checker
- LLM-assisted classification

## v1.0 Exit Criteria

- `pip install bookmark-cleaner` works
- `bookmark-cleaner clean bookmarks.html` produces cleaned output
- `bookmark-cleaner clean --dry-run bookmarks.html` previews changes
- `bookmark-cleaner info bookmarks.html` shows stats
- 80%+ test coverage
- Roundtrip tests pass on real files
