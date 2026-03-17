# bookmark-cleaner

A local-first Python CLI that cleans, deduplicates, and organizes browser bookmark files.

Browsers accumulate bookmark rot over time — duplicate imports, redundant folders, dead "New folder" placeholders, and the same URL saved dozens of times across migrations. **bookmark-cleaner** fixes this in one command while preserving every unique URL.

## What it does

```
$ bookmark-cleaner clean bookmarks.html --dry-run

             Cleanup Summary
┏━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Metric      ┃ Before ┃ After ┃ Removed ┃
┡━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ Bookmarks   │   2503 │   968 │    1535 │
│ Unique URLs │    970 │   968 │         │
│ Folders     │    131 │    40 │      91 │
│ Changes     │        │       │    1628 │
└─────────────┴────────┴───────┴─────────┘
```

- **Deduplicates URLs** with normalization (http/https, trailing slashes, query param order)
- **Unwraps import wrappers** — dissolves "Imported from Chrome", "Imported from Chrome (2)", etc.
- **Merges duplicate folders** — "Social Media" appearing 9 times becomes one folder
- **Dissolves generic folders** — "New folder", "Untitled folder" contents lifted to parent
- **Removes empty folders** after cleanup
- **Sorts** folders and bookmarks alphabetically
- **Strips oversized icons** to reduce file size

## Install

```bash
pip install bookmark-cleaner
```

Or run without installing:

```bash
uvx bookmark-cleaner clean bookmarks.html
```

## Usage

### Clean bookmarks

```bash
# Preview changes (recommended first step)
bookmark-cleaner clean bookmarks.html --dry-run

# Clean and write to bookmarks_cleaned.html
bookmark-cleaner clean bookmarks.html

# Specify output file
bookmark-cleaner clean bookmarks.html --output cleaned.html

# Choose dedup strategy (newest, oldest, longest_title)
bookmark-cleaner clean bookmarks.html --strategy oldest
```

### Inspect a bookmark file

```bash
bookmark-cleaner info bookmarks.html
```

## How to use

1. **Export bookmarks** from your browser (Chrome, Firefox, Edge, Brave all export to HTML)
2. **Run the cleaner** with `--dry-run` first to preview
3. **Run for real** to produce the cleaned file
4. **Import** the cleaned file back into your browser

The original file is **never modified**. Output always goes to a separate file.

## Supported formats

- Netscape Bookmark HTML (exported by all major browsers)

## Design principles

- **Non-destructive** — the input file is never touched
- **Zero data loss** — every unique URL is preserved
- **Local-only** — no network requests, no telemetry, no accounts
- **Minimal dependencies** — Python stdlib + typer + rich
- **Predictable** — `--dry-run` shows exactly what will change

## Development

```bash
git clone https://github.com/bookmark-cleaner/bookmark-cleaner
cd bookmark-cleaner
pip install -e .
pytest
```

224 tests, 97% coverage.

## License

MIT
