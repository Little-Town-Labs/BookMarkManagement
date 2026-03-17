"""Composable cleanup operations for bookmark trees."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode
from bookmark_cleaner.normalize import normalize_url
from bookmark_cleaner.tree import (
    collect_urls,
    map_tree,
    replace_bookmarks,
    replace_children,
)


# ── Result Types ─────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Change:
    """A single change made by an operation."""

    op: str
    description: str
    details: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class OpResult:
    """Result of a cleanup operation: new tree + change log."""

    tree: BookmarkTree
    changes: tuple[Change, ...]


# ── Default Patterns ─────────────────────────────────────────────────

_DEFAULT_WRAPPER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)^imported\s+from\s+.+?(\s*\(\d+\))?$"),
)

_DEFAULT_GENERIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)^(new|untitled)\s+folder(\s*\(\d+\))?$"),
)


def _matches_any(name: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(p.match(name) for p in patterns)


# ── sort_tree ────────────────────────────────────────────────────────


def sort_tree(tree: BookmarkTree) -> OpResult:
    """Sort folders and bookmarks alphabetically within each folder."""
    changes: list[Change] = []

    def _sort_folder(folder: FolderNode) -> FolderNode:
        sorted_children = tuple(sorted(folder.children, key=lambda c: c.name.lower()))
        sorted_bookmarks = tuple(sorted(folder.bookmarks, key=lambda b: b.title.lower()))

        if sorted_children != folder.children or sorted_bookmarks != folder.bookmarks:
            changes.append(Change(
                op="sort",
                description=f"Sorted contents of '{folder.name or 'root'}'",
            ))
            return FolderNode(
                name=folder.name,
                children=sorted_children,
                bookmarks=sorted_bookmarks,
                add_date=folder.add_date,
                last_modified=folder.last_modified,
                attrs=folder.attrs,
            )
        return folder

    new_root = map_tree(tree.root, _sort_folder)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── remove_empty_folders ─────────────────────────────────────────────


def remove_empty_folders(tree: BookmarkTree) -> OpResult:
    """Remove folders with no bookmarks and no children (bottom-up)."""
    changes: list[Change] = []

    def _remove_empties(folder: FolderNode) -> FolderNode:
        non_empty = []
        for child in folder.children:
            if child.children or child.bookmarks:
                non_empty.append(child)
            else:
                changes.append(Change(
                    op="remove_empty",
                    description=f"Removed empty folder '{child.name}'",
                    details=(("folder", child.name),),
                ))
        if len(non_empty) == len(folder.children):
            return folder
        return replace_children(folder, tuple(non_empty))

    new_root = map_tree(tree.root, _remove_empties)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── strip_icons ──────────────────────────────────────────────────────


def strip_icons(tree: BookmarkTree, threshold: int = 2048) -> OpResult:
    """Replace bookmark icons exceeding threshold bytes with empty string."""
    changes: list[Change] = []

    def _strip(folder: FolderNode) -> FolderNode:
        new_bookmarks: list[BookmarkNode] = []
        changed = False
        for bm in folder.bookmarks:
            if bm.icon and len(bm.icon) > threshold:
                new_bookmarks.append(BookmarkNode(
                    url=bm.url,
                    title=bm.title,
                    add_date=bm.add_date,
                    icon="",
                    attrs=bm.attrs,
                ))
                changes.append(Change(
                    op="strip_icon",
                    description=f"Stripped {len(bm.icon)} byte icon from '{bm.title}'",
                    details=(("url", bm.url), ("bytes", str(len(bm.icon)))),
                ))
                changed = True
            else:
                new_bookmarks.append(bm)
        if not changed:
            return folder
        return replace_bookmarks(folder, tuple(new_bookmarks))

    new_root = map_tree(tree.root, _strip)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── Shared: dissolve folders matching patterns ───────────────────────


def _dissolve_matching(
    folder: FolderNode,
    patterns: tuple[re.Pattern[str], ...],
    op_name: str,
    changes: list[Change],
) -> FolderNode:
    """Dissolve children matching patterns, lifting their contents into this folder."""
    new_children: list[FolderNode] = []
    lifted_bookmarks: list[BookmarkNode] = list(folder.bookmarks)
    lifted_children: list[FolderNode] = []

    for child in folder.children:
        # Recurse first so nested matches are handled
        processed_child = _dissolve_matching(child, patterns, op_name, changes)
        if _matches_any(processed_child.name, patterns):
            lifted_bookmarks.extend(processed_child.bookmarks)
            lifted_children.extend(processed_child.children)
            changes.append(Change(
                op=op_name,
                description=f"Dissolved '{processed_child.name}' "
                f"({len(processed_child.bookmarks)} bookmarks, "
                f"{len(processed_child.children)} folders lifted)",
                details=(("folder", processed_child.name),),
            ))
        else:
            new_children.append(processed_child)

    all_children = new_children + lifted_children

    # Merge any children that now share the same name
    merged_children = _merge_children_by_name(tuple(all_children), changes)

    if (
        merged_children == folder.children
        and tuple(lifted_bookmarks) == folder.bookmarks
    ):
        return folder

    return FolderNode(
        name=folder.name,
        children=merged_children,
        bookmarks=tuple(lifted_bookmarks),
        add_date=folder.add_date,
        last_modified=folder.last_modified,
        attrs=folder.attrs,
    )


# ── unwrap_wrappers ──────────────────────────────────────────────────


def unwrap_wrappers(
    tree: BookmarkTree,
    patterns: tuple[re.Pattern[str], ...] | None = None,
) -> OpResult:
    """Dissolve import wrapper folders, lifting their contents into the parent."""
    effective = patterns if patterns is not None else _DEFAULT_WRAPPER_PATTERNS
    changes: list[Change] = []
    new_root = _dissolve_matching(tree.root, effective, "unwrap", changes)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── dissolve_generics ────────────────────────────────────────────────


def dissolve_generics(
    tree: BookmarkTree,
    patterns: tuple[re.Pattern[str], ...] | None = None,
) -> OpResult:
    """Dissolve generic placeholder folders (e.g., 'New folder')."""
    effective = patterns if patterns is not None else _DEFAULT_GENERIC_PATTERNS
    changes: list[Change] = []
    new_root = _dissolve_matching(tree.root, effective, "dissolve", changes)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── merge_folders ────────────────────────────────────────────────────


def _merge_children_by_name(
    children: tuple[FolderNode, ...],
    changes: list[Change],
) -> tuple[FolderNode, ...]:
    """Merge children sharing the same name (case-insensitive)."""
    if not children:
        return children

    groups: dict[str, list[FolderNode]] = {}
    order: list[str] = []
    for child in children:
        key = child.name.lower()
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(child)

    result: list[FolderNode] = []
    for key in order:
        group = groups[key]
        if len(group) == 1:
            result.append(group[0])
        else:
            merged = _merge_folder_group(group, changes)
            result.append(merged)

    return tuple(result)


def _merge_folder_group(
    folders: list[FolderNode],
    changes: list[Change],
) -> FolderNode:
    """Merge a group of folders with the same name into one."""
    first = folders[0]

    all_bookmarks: list[BookmarkNode] = []
    all_children: list[FolderNode] = []
    earliest_add_date = first.add_date
    latest_last_modified = first.last_modified

    for f in folders:
        all_bookmarks.extend(f.bookmarks)
        all_children.extend(f.children)
        if f.add_date and (not earliest_add_date or f.add_date < earliest_add_date):
            earliest_add_date = f.add_date
        if f.last_modified > latest_last_modified:
            latest_last_modified = f.last_modified

    # Recursively merge children that share names
    merged_children = _merge_children_by_name(tuple(all_children), changes)

    changes.append(Change(
        op="merge",
        description=f"Merged {len(folders)} '{first.name}' folders "
        f"({len(all_bookmarks)} bookmarks combined)",
        details=(("folder", first.name), ("count", str(len(folders)))),
    ))

    return FolderNode(
        name=first.name,
        children=merged_children,
        bookmarks=tuple(all_bookmarks),
        add_date=earliest_add_date,
        last_modified=latest_last_modified,
        attrs=first.attrs,
    )


def merge_folders(tree: BookmarkTree) -> OpResult:
    """Merge folders with the same name at each nesting level."""
    changes: list[Change] = []

    def _merge_level(folder: FolderNode) -> FolderNode:
        merged = _merge_children_by_name(folder.children, changes)
        if merged == folder.children:
            return folder
        return replace_children(folder, merged)

    new_root = map_tree(tree.root, _merge_level)
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


# ── dedup_urls ───────────────────────────────────────────────────────


def dedup_urls(
    tree: BookmarkTree,
    strategy: str = "newest",
) -> OpResult:
    """Remove duplicate bookmarks by normalized URL."""
    strategies = {"newest", "oldest", "longest_title"}
    if strategy not in strategies:
        raise ValueError(f"Unknown dedup strategy '{strategy}'. Choose from: {strategies}")

    # Collect all bookmarks with their folder path and index
    entries: list[tuple[str, BookmarkNode, tuple[str, ...], int]] = []
    _collect_with_path(tree.root, (), entries)

    # Group by normalized URL
    groups: dict[str, list[tuple[BookmarkNode, tuple[str, ...], int]]] = {}
    for norm_url, bm, path, idx in entries:
        groups.setdefault(norm_url, []).append((bm, path, idx))

    # Pick winners — track losers by (path, index) for removal
    losers: set[tuple[tuple[str, ...], int]] = set()
    changes: list[Change] = []

    for norm_url, group in groups.items():
        if len(group) == 1:
            continue

        if strategy == "newest":
            group.sort(key=lambda x: x[0].add_date, reverse=True)
        elif strategy == "oldest":
            group.sort(key=lambda x: x[0].add_date)
        elif strategy == "longest_title":
            group.sort(key=lambda x: len(x[0].title), reverse=True)

        # First entry is the winner, rest are losers
        for bm, path, idx in group[1:]:
            losers.add((path, idx))
            changes.append(Change(
                op="dedup",
                description=f"Removed duplicate '{bm.title}' ({bm.url})",
                details=(("url", bm.url), ("normalized", norm_url)),
            ))

    if not losers:
        return OpResult(tree=tree, changes=())

    # Rebuild tree excluding losers
    def _rebuild(folder: FolderNode, current_path: tuple[str, ...]) -> FolderNode:
        new_children = tuple(
            _rebuild(child, current_path + (child.name,))
            for child in folder.children
        )
        new_bookmarks = tuple(
            bm for i, bm in enumerate(folder.bookmarks)
            if (current_path, i) not in losers
        )
        if new_children == folder.children and new_bookmarks == folder.bookmarks:
            return folder
        return FolderNode(
            name=folder.name,
            children=new_children,
            bookmarks=new_bookmarks,
            add_date=folder.add_date,
            last_modified=folder.last_modified,
            attrs=folder.attrs,
        )

    new_root = _rebuild(tree.root, ())
    return OpResult(
        tree=BookmarkTree(root=new_root, source_format=tree.source_format),
        changes=tuple(changes),
    )


def _flat_bookmarks(folder: FolderNode) -> list[BookmarkNode]:
    """Collect all bookmarks in the subtree as a flat list."""
    result: list[BookmarkNode] = list(folder.bookmarks)
    for child in folder.children:
        result.extend(_flat_bookmarks(child))
    return result


def _collect_with_path(
    folder: FolderNode,
    path: tuple[str, ...],
    out: list[tuple[str, BookmarkNode, tuple[str, ...], int]],
) -> None:
    """Collect (normalized_url, bookmark, folder_path, index) tuples."""
    for i, bm in enumerate(folder.bookmarks):
        out.append((normalize_url(bm.url), bm, path, i))
    for child in folder.children:
        _collect_with_path(child, path + (child.name,), out)


# ── run_pipeline ─────────────────────────────────────────────────────


def run_pipeline(
    tree: BookmarkTree,
    operations: list[Callable[..., OpResult]] | None = None,
    *,
    strategy: str = "newest",
    icon_threshold: int = 2048,
    wrapper_patterns: tuple[re.Pattern[str], ...] | None = None,
    generic_patterns: tuple[re.Pattern[str], ...] | None = None,
) -> OpResult:
    """Run a pipeline of cleanup operations on a bookmark tree.

    Default pipeline order:
    1. unwrap_wrappers
    2. dissolve_generics
    3. merge_folders
    4. dedup_urls
    5. strip_icons
    6. remove_empty_folders
    7. sort_tree
    """
    if operations is not None:
        # Custom operation list — run each with tree as only arg
        all_changes: list[Change] = []
        current = tree
        for op in operations:
            result = op(current)
            current = result.tree
            all_changes.extend(result.changes)
        return OpResult(tree=current, changes=tuple(all_changes))

    original_normalized = frozenset(
        normalize_url(bm.url) for bm in _flat_bookmarks(tree.root)
    )
    all_changes: list[Change] = []
    current = tree

    # 1. Unwrap wrappers
    r = unwrap_wrappers(current, patterns=wrapper_patterns)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 2. Dissolve generics
    r = dissolve_generics(current, patterns=generic_patterns)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 3. Merge folders
    r = merge_folders(current)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 4. Dedup URLs
    r = dedup_urls(current, strategy=strategy)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 5. Strip icons
    r = strip_icons(current, threshold=icon_threshold)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 6. Remove empty folders
    r = remove_empty_folders(current)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # 7. Sort
    r = sort_tree(current)
    current, all_changes = r.tree, all_changes + list(r.changes)

    # Validate: no unique normalized URLs lost
    result_normalized = frozenset(
        normalize_url(bm.url) for bm in _flat_bookmarks(current.root)
    )
    if len(result_normalized) < len(original_normalized):
        missing = original_normalized - result_normalized
        raise ValueError(
            f"Pipeline lost {len(original_normalized) - len(result_normalized)} unique URLs! "
            f"Missing: {list(missing)[:5]}"
        )

    return OpResult(tree=current, changes=tuple(all_changes))
