"""Tree traversal, transformation, and comparison utilities for bookmark trees."""
from __future__ import annotations

from collections.abc import Callable

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode

# ── Traversal & Query ─────────────────────────────────────────────────


def collect_bookmarks(folder: FolderNode) -> tuple[BookmarkNode, ...]:
    """Collect all bookmarks in the subtree, depth-first."""
    result: list[BookmarkNode] = []
    for child in folder.children:
        result.extend(collect_bookmarks(child))
    result.extend(folder.bookmarks)
    return tuple(result)


def collect_urls(folder: FolderNode) -> frozenset[str]:
    """Collect unique URLs across the entire subtree."""
    urls: set[str] = set()
    for bm in collect_bookmarks(folder):
        urls.add(bm.url)
    return frozenset(urls)


def count_items(folder: FolderNode) -> tuple[int, int]:
    """Count (total_bookmarks, total_folders) in the subtree.

    Does not count the folder itself, only its descendants.
    """
    bm_count = len(folder.bookmarks)
    folder_count = len(folder.children)
    for child in folder.children:
        child_bm, child_folders = count_items(child)
        bm_count += child_bm
        folder_count += child_folders
    return bm_count, folder_count


def folder_paths(folder: FolderNode, _prefix: str = "") -> tuple[str, ...]:
    """Generate all folder paths in the subtree (e.g., 'A > B > C').

    The folder itself is included if it has a non-empty name.
    """
    result: list[str] = []
    for child in folder.children:
        if _prefix:
            child_path = f"{_prefix} > {child.name}"
        else:
            child_path = child.name
        result.append(child_path)
        result.extend(folder_paths(child, child_path))
    return tuple(result)


def find_folder(folder: FolderNode, name: str) -> FolderNode | None:
    """Find a folder by name (case-insensitive), depth-first."""
    target = name.lower()
    for child in folder.children:
        if child.name.lower() == target:
            return child
        found = find_folder(child, name)
        if found is not None:
            return found
    return None


# ── Transformation ────────────────────────────────────────────────────


def replace_bookmarks(
    folder: FolderNode,
    bookmarks: tuple[BookmarkNode, ...],
) -> FolderNode:
    """Return a new FolderNode with replaced bookmarks, preserving other fields."""
    return FolderNode(
        name=folder.name,
        children=folder.children,
        bookmarks=bookmarks,
        add_date=folder.add_date,
        last_modified=folder.last_modified,
        attrs=folder.attrs,
    )


def replace_children(
    folder: FolderNode,
    children: tuple[FolderNode, ...],
) -> FolderNode:
    """Return a new FolderNode with replaced children, preserving other fields."""
    return FolderNode(
        name=folder.name,
        children=children,
        bookmarks=folder.bookmarks,
        add_date=folder.add_date,
        last_modified=folder.last_modified,
        attrs=folder.attrs,
    )


def map_tree(
    folder: FolderNode,
    fn: Callable[[FolderNode], FolderNode],
) -> FolderNode:
    """Apply fn to every folder bottom-up (children processed before parent)."""
    new_children = tuple(map_tree(child, fn) for child in folder.children)
    updated = replace_children(folder, new_children)
    return fn(updated)


# ── Equality & Comparison ─────────────────────────────────────────────


def trees_equal(
    a: BookmarkTree,
    b: BookmarkTree,
    ignore_metadata: bool = False,
) -> bool:
    """Compare two trees for structural equality.

    If ignore_metadata is True, only compares URLs, titles, and folder names/structure.
    Dates, icons, and attrs are ignored.
    """
    if not ignore_metadata:
        return a.root == b.root
    return _folders_equal_content(a.root, b.root)


def _bookmarks_equal_content(a: BookmarkNode, b: BookmarkNode) -> bool:
    """Compare two bookmarks ignoring metadata (dates, icons, attrs)."""
    return a.url == b.url and a.title == b.title


def _folders_equal_content(a: FolderNode, b: FolderNode) -> bool:
    """Compare two folders ignoring metadata, recursively."""
    if a.name != b.name:
        return False
    if len(a.bookmarks) != len(b.bookmarks):
        return False
    if len(a.children) != len(b.children):
        return False
    for bm_a, bm_b in zip(a.bookmarks, b.bookmarks):
        if not _bookmarks_equal_content(bm_a, bm_b):
            return False
    for ch_a, ch_b in zip(a.children, b.children):
        if not _folders_equal_content(ch_a, ch_b):
            return False
    return True


def first_difference(
    a: BookmarkTree,
    b: BookmarkTree,
) -> str | None:
    """Return a human-readable description of the first difference, or None if equal."""
    return _folder_diff(a.root, b.root, "root")


def _folder_diff(a: FolderNode, b: FolderNode, path: str) -> str | None:
    """Recursively find the first difference between two folders."""
    if a.name != b.name:
        return f"Folder name differs at {path}: '{a.name}' vs '{b.name}'"

    if len(a.bookmarks) != len(b.bookmarks):
        return (
            f"Bookmark count differs in '{a.name or path}': "
            f"{len(a.bookmarks)} vs {len(b.bookmarks)}"
        )

    for i, (bm_a, bm_b) in enumerate(zip(a.bookmarks, b.bookmarks)):
        if bm_a != bm_b:
            location = a.name or path
            return (
                f"Bookmark {i} differs in '{location}': "
                f"'{bm_a.url}' vs '{bm_b.url}'"
            )

    if len(a.children) != len(b.children):
        return (
            f"Child folder count differs in '{a.name or path}': "
            f"{len(a.children)} vs {len(b.children)}"
        )

    for ch_a, ch_b in zip(a.children, b.children):
        child_path = f"{path} > {ch_a.name}" if path != "root" else ch_a.name
        diff = _folder_diff(ch_a, ch_b, child_path)
        if diff is not None:
            return diff

    return None
