# Data Model: 1-tree-model

## Types

### BookmarkNode

Represents a single bookmark (leaf node).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| url | str | (required) | Bookmark URL |
| title | str | "" | Display title |
| add_date | int | 0 | Unix timestamp when bookmark was created |
| icon | str | "" | Base64-encoded icon data (may be empty) |
| attrs | tuple[tuple[str, str], ...] | () | Additional browser-specific attributes as key-value pairs |

**Constraints:**
- All fields read-only after creation
- `url` must be a non-empty string
- Content equality based on `url` + `title` (all fields for full equality)

### FolderNode

Represents a bookmark folder (branch node).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| name | str | (required) | Folder display name |
| children | tuple[FolderNode, ...] | () | Ordered child subfolders |
| bookmarks | tuple[BookmarkNode, ...] | () | Ordered child bookmarks |
| add_date | int | 0 | Unix timestamp when folder was created |
| last_modified | int | 0 | Unix timestamp when folder was last modified |
| attrs | tuple[tuple[str, str], ...] | () | Additional browser-specific attributes as key-value pairs |

**Constraints:**
- All fields read-only after creation
- `name` must be a string (empty string allowed for unnamed folders)
- Order of `children` and `bookmarks` is significant (preserved from source)
- A folder is "empty" when `len(children) == 0 and len(bookmarks) == 0`

### BookmarkTree

Root container holding the complete bookmark collection.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| root | FolderNode | FolderNode(name="") | Root folder containing all top-level content |
| source_format | str | "" | Detected source format: "netscape", "chrome_json", "firefox_json", or "" |

**Constraints:**
- All fields read-only after creation
- Multiple top-level folders (bookmark bar, other bookmarks, mobile) are children of root
- `source_format` is informational only — does not affect model behavior

## Relationships

```
BookmarkTree
  └── root: FolderNode
        ├── children: tuple[FolderNode, ...]
        │     ├── children: tuple[FolderNode, ...]  (recursive)
        │     └── bookmarks: tuple[BookmarkNode, ...]
        └── bookmarks: tuple[BookmarkNode, ...]
```

- BookmarkTree contains exactly one root FolderNode
- FolderNode contains zero or more child FolderNodes (recursive)
- FolderNode contains zero or more BookmarkNodes
- BookmarkNode is always a leaf (no children)
- Nesting depth is unbounded (limited only by Python recursion limit)

## Utility Functions (tree.py)

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `collect_bookmarks` | FolderNode | tuple[BookmarkNode, ...] | All bookmarks in subtree (depth-first) |
| `collect_urls` | FolderNode | frozenset[str] | Unique URLs in subtree |
| `count_items` | FolderNode | tuple[int, int] | (bookmark_count, folder_count) |
| `folder_paths` | FolderNode | tuple[str, ...] | All folder paths (e.g., "A > B > C") |
| `map_tree` | FolderNode, fn | FolderNode | Apply fn bottom-up to every folder, return new tree |
| `replace_bookmarks` | FolderNode, bookmarks | FolderNode | New folder with replaced bookmarks |
| `replace_children` | FolderNode, children | FolderNode | New folder with replaced child folders |
| `find_folder` | FolderNode, name | FolderNode or None | Find folder by name (case-insensitive) |
| `trees_equal` | BookmarkTree, BookmarkTree, ignore_metadata | bool | Structural equality check |
| `first_difference` | BookmarkTree, BookmarkTree | str or None | Description of first difference found |
