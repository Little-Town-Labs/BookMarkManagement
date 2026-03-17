"""bookmark-cleaner: Clean, deduplicate, and organize browser bookmark files."""
from __future__ import annotations

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode
from bookmark_cleaner.tree import (
    collect_bookmarks,
    collect_urls,
    count_items,
    find_folder,
    first_difference,
    folder_paths,
    map_tree,
    replace_bookmarks,
    replace_children,
    trees_equal,
)

__version__ = "0.1.0"

__all__ = [
    "BookmarkNode",
    "BookmarkTree",
    "FolderNode",
    "collect_bookmarks",
    "collect_urls",
    "count_items",
    "find_folder",
    "first_difference",
    "folder_paths",
    "map_tree",
    "replace_bookmarks",
    "replace_children",
    "trees_equal",
]
