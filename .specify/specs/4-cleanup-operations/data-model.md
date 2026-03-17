# Data Model: 4-cleanup-operations

## New Types

### Change
Represents a single change made by an operation.

| Field | Type | Description |
|-------|------|-------------|
| op | str | Operation name (e.g., "dedup", "merge_folders") |
| description | str | Human-readable description of what changed |
| details | tuple of (str, str) pairs | Structured key-value details (e.g., url, folder_name, count) |

Immutable (frozen dataclass). The `details` field uses a tuple of pairs instead of a dict to maintain immutability.

### OpResult
Container for the output of any cleanup operation.

| Field | Type | Description |
|-------|------|-------------|
| tree | BookmarkTree | The new tree after the operation |
| changes | tuple of Change | All changes made by the operation |

Immutable (frozen dataclass).

## Existing Types Used (from models.py)

### BookmarkNode
| Field | Type | Relevant to Operations |
|-------|------|----------------------|
| url | str | Primary dedup key (after normalization) |
| title | str | Alternative dedup strategy (longest title) |
| add_date | int | Default dedup strategy (keep newest) |
| icon | str | Icon stripping target |

### FolderNode
| Field | Type | Relevant to Operations |
|-------|------|----------------------|
| name | str | Folder merge key (case-insensitive) |
| children | tuple of FolderNode | Folder merge, unwrap, dissolve targets |
| bookmarks | tuple of BookmarkNode | Contents to merge/move |
| add_date | int | Merge: keep earliest |
| last_modified | int | Merge: keep latest |
| attrs | tuple of (str, str) pairs | Merge: keep from first folder |

### BookmarkTree
| Field | Type | Relevant to Operations |
|-------|------|----------------------|
| root | FolderNode | Every operation transforms root |
| source_format | str | Preserved through all operations |

## Relationships

```
OpResult
├── tree: BookmarkTree
│   └── root: FolderNode (recursive tree)
│       ├── children: tuple[FolderNode, ...]
│       └── bookmarks: tuple[BookmarkNode, ...]
└── changes: tuple[Change, ...]
```

## URL Normalization (not a stored type — computed)

Normalization produces a canonical string from a URL:
- Lowercase scheme and hostname
- Strip default ports (80 for http, 443 for https)
- Strip trailing slash from path
- Sort query parameters alphabetically
- Treat http:// and https:// as equivalent (normalize to https)

The normalized form is used only for comparison — the original URL is preserved in the BookmarkNode.
