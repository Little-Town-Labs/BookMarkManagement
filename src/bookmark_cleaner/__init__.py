"""bookmark-cleaner: Clean, deduplicate, and organize browser bookmark files."""
from __future__ import annotations

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode
from bookmark_cleaner.normalize import normalize_url
from bookmark_cleaner.operations import (
    Change,
    OpResult,
    dedup_urls,
    dissolve_generics,
    merge_folders,
    remove_empty_folders,
    run_pipeline,
    sort_tree,
    strip_icons,
    unwrap_wrappers,
)
from bookmark_cleaner.parsers import detect_format
from bookmark_cleaner.parsers.netscape import export_netscape, parse_netscape
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
    "Change",
    "FolderNode",
    "OpResult",
    "dedup_urls",
    "detect_format",
    "dissolve_generics",
    "export_netscape",
    "merge_folders",
    "normalize_url",
    "parse_netscape",
    "remove_empty_folders",
    "run_pipeline",
    "sort_tree",
    "strip_icons",
    "unwrap_wrappers",
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
