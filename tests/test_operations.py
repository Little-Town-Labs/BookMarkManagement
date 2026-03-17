"""Tests for cleanup operations and pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode
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
from bookmark_cleaner.tree import collect_bookmarks, collect_urls, count_items, find_folder


# ── Helpers ──────────────────────────────────────────────────────────


def _tree(root: FolderNode) -> BookmarkTree:
    return BookmarkTree(root=root, source_format="netscape")


def _bm(url: str, title: str = "", add_date: int = 0, icon: str = "") -> BookmarkNode:
    return BookmarkNode(url=url, title=title, add_date=add_date, icon=icon)


def _folder(
    name: str,
    children: tuple[FolderNode, ...] = (),
    bookmarks: tuple[BookmarkNode, ...] = (),
    add_date: int = 0,
    last_modified: int = 0,
    attrs: tuple[tuple[str, str], ...] = (),
) -> FolderNode:
    return FolderNode(
        name=name,
        children=children,
        bookmarks=bookmarks,
        add_date=add_date,
        last_modified=last_modified,
        attrs=attrs,
    )


# ── Change and OpResult ──────────────────────────────────────────────


class TestChangeAndOpResult:
    def test_change_fields(self) -> None:
        c = Change(op="dedup", description="Removed duplicate", details=(("url", "https://x.com"),))
        assert c.op == "dedup"
        assert c.description == "Removed duplicate"
        assert c.details == (("url", "https://x.com"),)

    def test_change_immutable(self) -> None:
        c = Change(op="dedup", description="test")
        with pytest.raises(AttributeError):
            c.op = "other"  # type: ignore[misc]

    def test_change_empty_details(self) -> None:
        c = Change(op="sort", description="Sorted")
        assert c.details == ()

    def test_opresult_fields(self) -> None:
        tree = _tree(_folder(""))
        changes = (Change(op="test", description="test"),)
        result = OpResult(tree=tree, changes=changes)
        assert result.tree == tree
        assert len(result.changes) == 1

    def test_opresult_empty_changes(self) -> None:
        tree = _tree(_folder(""))
        result = OpResult(tree=tree, changes=())
        assert result.changes == ()


# ── sort_tree ────────────────────────────────────────────────────────


class TestSortTree:
    def test_bookmarks_sorted_alphabetically(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://c.com", "Cherry"),
            _bm("https://a.com", "Apple"),
            _bm("https://b.com", "Banana"),
        )))
        result = sort_tree(tree)
        titles = [bm.title for bm in result.tree.root.bookmarks]
        assert titles == ["Apple", "Banana", "Cherry"]

    def test_folders_sorted_alphabetically(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Zebra"),
            _folder("Apple"),
            _folder("Mango"),
        )))
        result = sort_tree(tree)
        names = [c.name for c in result.tree.root.children]
        assert names == ["Apple", "Mango", "Zebra"]

    def test_case_insensitive(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://b.com", "banana"),
            _bm("https://a.com", "Apple"),
        )))
        result = sort_tree(tree)
        titles = [bm.title for bm in result.tree.root.bookmarks]
        assert titles == ["Apple", "banana"]

    def test_stable_sort(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "Same", add_date=1),
            _bm("https://b.com", "Same", add_date=2),
        )))
        result = sort_tree(tree)
        urls = [bm.url for bm in result.tree.root.bookmarks]
        assert urls == ["https://a.com", "https://b.com"]

    def test_recursive(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Parent", bookmarks=(
                _bm("https://b.com", "B"),
                _bm("https://a.com", "A"),
            )),
        )))
        result = sort_tree(tree)
        titles = [bm.title for bm in result.tree.root.children[0].bookmarks]
        assert titles == ["A", "B"]

    def test_empty_tree(self) -> None:
        tree = _tree(_folder(""))
        result = sort_tree(tree)
        assert len(result.changes) == 0

    def test_already_sorted(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "A"),
            _bm("https://b.com", "B"),
        )))
        result = sort_tree(tree)
        assert len(result.changes) == 0

    def test_change_log(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://b.com", "B"),
            _bm("https://a.com", "A"),
        )))
        result = sort_tree(tree)
        assert len(result.changes) > 0
        assert result.changes[0].op == "sort"


# ── remove_empty_folders ─────────────────────────────────────────────


class TestRemoveEmptyFolders:
    def test_empty_child_removed(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Empty"),
            _folder("HasBookmarks", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = remove_empty_folders(tree)
        assert len(result.tree.root.children) == 1
        assert result.tree.root.children[0].name == "HasBookmarks"

    def test_mix_of_empty_and_nonempty(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Empty1"),
            _folder("Full", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("Empty2"),
        )))
        result = remove_empty_folders(tree)
        assert len(result.tree.root.children) == 1

    def test_cascading_removal(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Outer", children=(
                _folder("Inner"),
            )),
        )))
        result = remove_empty_folders(tree)
        assert len(result.tree.root.children) == 0

    def test_root_never_removed(self) -> None:
        tree = _tree(_folder(""))
        result = remove_empty_folders(tree)
        assert result.tree.root is not None

    def test_folder_with_only_bookmarks_not_removed(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("OnlyBookmarks", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = remove_empty_folders(tree)
        assert len(result.tree.root.children) == 1

    def test_no_empty_folders_no_changes(self) -> None:
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A"),)))
        result = remove_empty_folders(tree)
        assert len(result.changes) == 0

    def test_change_log_reports_folder_path(self) -> None:
        tree = _tree(_folder("", children=(_folder("Empty"),)))
        result = remove_empty_folders(tree)
        assert len(result.changes) == 1
        assert result.changes[0].op == "remove_empty"
        assert "Empty" in result.changes[0].description


# ── strip_icons ──────────────────────────────────────────────────────


class TestStripIcons:
    def test_oversized_icon_stripped(self) -> None:
        big_icon = "x" * 2049
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A", icon=big_icon),)))
        result = strip_icons(tree)
        assert result.tree.root.bookmarks[0].icon == ""

    def test_exact_threshold_preserved(self) -> None:
        icon = "x" * 2048
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A", icon=icon),)))
        result = strip_icons(tree)
        assert result.tree.root.bookmarks[0].icon == icon

    def test_small_icon_preserved(self) -> None:
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A", icon="small"),)))
        result = strip_icons(tree)
        assert result.tree.root.bookmarks[0].icon == "small"

    def test_empty_icon_unchanged(self) -> None:
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A"),)))
        result = strip_icons(tree)
        assert result.tree.root.bookmarks[0].icon == ""

    def test_custom_threshold(self) -> None:
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A", icon="x" * 101),)))
        result = strip_icons(tree, threshold=100)
        assert result.tree.root.bookmarks[0].icon == ""

    def test_change_log(self) -> None:
        tree = _tree(_folder("", bookmarks=(_bm("https://a.com", "A", icon="x" * 3000),)))
        result = strip_icons(tree)
        assert len(result.changes) == 1
        assert result.changes[0].op == "strip_icon"

    def test_recursive(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Sub", bookmarks=(_bm("https://a.com", "A", icon="x" * 3000),)),
        )))
        result = strip_icons(tree)
        assert result.tree.root.children[0].bookmarks[0].icon == ""


# ── unwrap_wrappers ──────────────────────────────────────────────────


class TestUnwrapWrappers:
    def test_imported_from_chrome(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", bookmarks=(
                _bm("https://a.com", "A"),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 0
        assert len(result.tree.root.bookmarks) == 1

    def test_imported_with_subfolders(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", children=(
                _folder("Dev", bookmarks=(_bm("https://a.com", "A"),)),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 1
        assert result.tree.root.children[0].name == "Dev"

    def test_numbered_variant(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome (2)", bookmarks=(
                _bm("https://a.com", "A"),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 0
        assert len(result.tree.root.bookmarks) == 1

    def test_case_insensitive(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("imported from chrome", bookmarks=(
                _bm("https://a.com", "A"),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 0

    def test_imported_from_google_chrome(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported From Google Chrome", bookmarks=(
                _bm("https://a.com", "A"),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 0

    def test_imported_from_edge(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Edge", bookmarks=(
                _bm("https://a.com", "A"),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 0

    def test_nested_wrappers(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", children=(
                _folder("Imported from Chrome (2)", bookmarks=(
                    _bm("https://a.com", "A"),
                )),
            )),
        )))
        result = unwrap_wrappers(tree)
        assert len(collect_bookmarks(result.tree.root)) == 1

    def test_wrapper_child_overlaps_existing(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", bookmarks=(_bm("https://existing.com", "Existing"),)),
            _folder("Imported from Chrome", children=(
                _folder("Dev", bookmarks=(_bm("https://new.com", "New"),)),
            )),
        )))
        result = unwrap_wrappers(tree)
        # After unwrap, "Dev" from wrapper merges with existing "Dev"
        dev_folders = [c for c in result.tree.root.children if c.name.lower() == "dev"]
        assert len(dev_folders) == 1
        assert len(dev_folders[0].bookmarks) == 2

    def test_non_wrapper_untouched(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Development", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.tree.root.children) == 1
        assert result.tree.root.children[0].name == "Development"

    def test_custom_patterns(self) -> None:
        import re
        custom = (re.compile(r"(?i)^custom wrapper$"),)
        tree = _tree(_folder("", children=(
            _folder("Custom Wrapper", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = unwrap_wrappers(tree, patterns=custom)
        assert len(result.tree.root.children) == 0

    def test_change_log(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = unwrap_wrappers(tree)
        assert len(result.changes) > 0
        assert result.changes[0].op == "unwrap"

    def test_empty_tree(self) -> None:
        tree = _tree(_folder(""))
        result = unwrap_wrappers(tree)
        assert len(result.changes) == 0


# ── dissolve_generics ────────────────────────────────────────────────


class TestDissolveGenerics:
    def test_new_folder_dissolved(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("New folder", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 0
        assert len(result.tree.root.bookmarks) == 1

    def test_new_folder_numbered(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("New folder (2)", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 0

    def test_untitled_folder(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Untitled folder", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 0

    def test_case_insensitive(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("NEW FOLDER", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 0

    def test_generic_with_subfolders(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("New folder", children=(
                _folder("Sub", bookmarks=(_bm("https://a.com", "A"),)),
            )),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 1
        assert result.tree.root.children[0].name == "Sub"

    def test_non_generic_untouched(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("My Folder", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.tree.root.children) == 1

    def test_change_log(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("New folder", bookmarks=(_bm("https://a.com", "A"),)),
        )))
        result = dissolve_generics(tree)
        assert len(result.changes) > 0
        assert result.changes[0].op == "dissolve"


# ── merge_folders ────────────────────────────────────────────────────


class TestMergeFolders:
    def test_same_name_merged(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Social Media", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("Social Media", bookmarks=(_bm("https://b.com", "B"),)),
        )))
        result = merge_folders(tree)
        assert len(result.tree.root.children) == 1
        assert len(result.tree.root.children[0].bookmarks) == 2

    def test_case_insensitive_merge(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Social Media", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("social media", bookmarks=(_bm("https://b.com", "B"),)),
        )))
        result = merge_folders(tree)
        assert len(result.tree.root.children) == 1
        # Name from first folder preserved
        assert result.tree.root.children[0].name == "Social Media"

    def test_merged_children_recursive(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", children=(
                _folder("Python", bookmarks=(_bm("https://a.com", "A"),)),
            )),
            _folder("Dev", children=(
                _folder("Python", bookmarks=(_bm("https://b.com", "B"),)),
            )),
        )))
        result = merge_folders(tree)
        assert len(result.tree.root.children) == 1
        dev = result.tree.root.children[0]
        assert len(dev.children) == 1
        assert dev.children[0].name == "Python"
        assert len(dev.children[0].bookmarks) == 2

    def test_earliest_add_date(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", add_date=200),
            _folder("Dev", add_date=100),
        )))
        result = merge_folders(tree)
        assert result.tree.root.children[0].add_date == 100

    def test_latest_last_modified(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", last_modified=100),
            _folder("Dev", last_modified=200),
        )))
        result = merge_folders(tree)
        assert result.tree.root.children[0].last_modified == 200

    def test_attrs_from_first(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", attrs=(("PERSONAL_TOOLBAR_FOLDER", "true"),)),
            _folder("Dev"),
        )))
        result = merge_folders(tree)
        assert result.tree.root.children[0].attrs == (("PERSONAL_TOOLBAR_FOLDER", "true"),)

    def test_three_folders_merged(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("Dev", bookmarks=(_bm("https://b.com", "B"),)),
            _folder("Dev", bookmarks=(_bm("https://c.com", "C"),)),
        )))
        result = merge_folders(tree)
        assert len(result.tree.root.children) == 1
        assert len(result.tree.root.children[0].bookmarks) == 3

    def test_no_duplicates_no_changes(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev"),
            _folder("Social"),
        )))
        result = merge_folders(tree)
        assert len(result.changes) == 0

    def test_change_log(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Dev", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("Dev", bookmarks=(_bm("https://b.com", "B"),)),
        )))
        result = merge_folders(tree)
        assert len(result.changes) > 0
        assert result.changes[0].op == "merge"


# ── dedup_urls ───────────────────────────────────────────────────────


class TestDedupUrls:
    def test_same_url_same_folder(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "A", add_date=100),
            _bm("https://a.com", "A copy", add_date=200),
        )))
        result = dedup_urls(tree)
        assert len(result.tree.root.bookmarks) == 1

    def test_same_url_different_folders(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("F1", bookmarks=(_bm("https://a.com", "A", add_date=100),)),
            _folder("F2", bookmarks=(_bm("https://a.com", "A copy", add_date=200),)),
        )))
        result = dedup_urls(tree)
        all_bm = collect_bookmarks(result.tree.root)
        assert len(all_bm) == 1

    def test_strategy_newest(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "Old", add_date=100),
            _bm("https://a.com", "New", add_date=200),
        )))
        result = dedup_urls(tree, strategy="newest")
        assert result.tree.root.bookmarks[0].title == "New"

    def test_strategy_oldest(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "Old", add_date=100),
            _bm("https://a.com", "New", add_date=200),
        )))
        result = dedup_urls(tree, strategy="oldest")
        assert result.tree.root.bookmarks[0].title == "Old"

    def test_strategy_longest_title(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "Short", add_date=100),
            _bm("https://a.com", "Much Longer Title", add_date=200),
        )))
        result = dedup_urls(tree, strategy="longest_title")
        assert result.tree.root.bookmarks[0].title == "Much Longer Title"

    def test_invalid_strategy_raises(self) -> None:
        tree = _tree(_folder(""))
        with pytest.raises(ValueError, match="Unknown dedup strategy"):
            dedup_urls(tree, strategy="invalid")

    def test_no_duplicates_no_changes(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "A"),
            _bm("https://b.com", "B"),
        )))
        result = dedup_urls(tree)
        assert len(result.changes) == 0

    def test_normalized_http_https_duplicate(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("http://example.com", "HTTP", add_date=100),
            _bm("https://example.com", "HTTPS", add_date=200),
        )))
        result = dedup_urls(tree)
        assert len(result.tree.root.bookmarks) == 1

    def test_normalized_trailing_slash_duplicate(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://example.com/path/", "Slash", add_date=100),
            _bm("https://example.com/path", "NoSlash", add_date=200),
        )))
        result = dedup_urls(tree)
        assert len(result.tree.root.bookmarks) == 1

    def test_normalized_query_order_duplicate(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://example.com?b=2&a=1", "QA", add_date=100),
            _bm("https://example.com?a=1&b=2", "QB", add_date=200),
        )))
        result = dedup_urls(tree)
        assert len(result.tree.root.bookmarks) == 1

    def test_different_fragments_not_duplicate(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://example.com#a", "A"),
            _bm("https://example.com#b", "B"),
        )))
        result = dedup_urls(tree)
        assert len(result.tree.root.bookmarks) == 2

    def test_unique_url_count_preserved(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("F1", bookmarks=(
                _bm("https://a.com", "A1", add_date=100),
                _bm("https://b.com", "B", add_date=100),
            )),
            _folder("F2", bookmarks=(
                _bm("https://a.com", "A2", add_date=200),
                _bm("https://c.com", "C", add_date=100),
            )),
        )))
        original_urls = collect_urls(tree.root)
        result = dedup_urls(tree)
        result_urls = collect_urls(result.tree.root)
        assert len(result_urls) == len(original_urls)

    def test_original_tree_unchanged(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "A", add_date=100),
            _bm("https://a.com", "A copy", add_date=200),
        )))
        dedup_urls(tree)
        assert len(tree.root.bookmarks) == 2

    def test_change_log(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://a.com", "A", add_date=100),
            _bm("https://a.com", "A copy", add_date=200),
        )))
        result = dedup_urls(tree)
        assert len(result.changes) > 0
        assert result.changes[0].op == "dedup"


# ── run_pipeline ─────────────────────────────────────────────────────


class TestRunPipeline:
    def test_full_pipeline_on_fixture(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", children=(
                _folder("Dev", bookmarks=(
                    _bm("https://a.com", "A", add_date=100),
                    _bm("https://a.com", "A dup", add_date=200),
                )),
            )),
            _folder("Dev", bookmarks=(
                _bm("https://b.com", "B", add_date=100),
            )),
            _folder("New folder", bookmarks=(
                _bm("https://c.com", "C", add_date=100),
            )),
            _folder("Empty"),
        )))
        result = run_pipeline(tree)
        # Wrapper unwrapped, generics dissolved, folders merged, deduped, empties removed, sorted
        all_bm = collect_bookmarks(result.tree.root)
        urls = {bm.url for bm in all_bm}
        assert urls == {"https://a.com", "https://b.com", "https://c.com"}
        # No empty folders
        _, folder_count = count_items(result.tree.root)
        for_check = result.tree.root
        assert all(
            len(c.bookmarks) > 0 or len(c.children) > 0
            for c in result.tree.root.children
        )

    def test_pipeline_change_log_combined(self) -> None:
        tree = _tree(_folder("", children=(
            _folder("Imported from Chrome", bookmarks=(_bm("https://a.com", "A"),)),
            _folder("Empty"),
        )))
        result = run_pipeline(tree)
        ops = {c.op for c in result.changes}
        assert "unwrap" in ops

    def test_pipeline_custom_operations(self) -> None:
        tree = _tree(_folder("", bookmarks=(
            _bm("https://b.com", "B"),
            _bm("https://a.com", "A"),
        )))
        result = run_pipeline(tree, operations=[sort_tree])
        titles = [bm.title for bm in result.tree.root.bookmarks]
        assert titles == ["A", "B"]

    def test_pipeline_empty_tree(self) -> None:
        tree = _tree(_folder(""))
        result = run_pipeline(tree)
        assert len(result.changes) == 0

    def test_pipeline_preserves_source_format(self) -> None:
        tree = _tree(_folder(""))
        result = run_pipeline(tree)
        assert result.tree.source_format == "netscape"

    def test_pipeline_url_count_preserved(self) -> None:
        from bookmark_cleaner.normalize import normalize_url

        tree = _tree(_folder("", children=(
            _folder("F1", bookmarks=(
                _bm("https://a.com", "A", add_date=100),
                _bm("https://b.com", "B", add_date=100),
            )),
            _folder("F2", bookmarks=(
                _bm("https://a.com", "A2", add_date=200),
            )),
        )))
        original = {normalize_url(bm.url) for bm in collect_bookmarks(tree.root)}
        result = run_pipeline(tree)
        after = {normalize_url(bm.url) for bm in collect_bookmarks(result.tree.root)}
        assert len(after) == len(original)


# ── Real-file integration tests ──────────────────────────────────────


class TestRealFilePipeline:
    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_favorites_unique_urls_preserved(self) -> None:
        from bookmark_cleaner.normalize import normalize_url
        from bookmark_cleaner.parsers.netscape import parse_netscape

        tree = parse_netscape("favorites_3_17_26.html")
        original_normalized = {normalize_url(bm.url) for bm in collect_bookmarks(tree.root)}

        result = run_pipeline(tree)
        result_normalized = {normalize_url(bm.url) for bm in collect_bookmarks(result.tree.root)}
        assert len(result_normalized) == len(original_normalized)

    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_favorites_no_wrappers_remain(self) -> None:
        import re

        from bookmark_cleaner.parsers.netscape import parse_netscape
        from bookmark_cleaner.tree import folder_paths

        tree = parse_netscape("favorites_3_17_26.html")
        result = run_pipeline(tree)
        paths = folder_paths(result.tree.root)
        wrapper_re = re.compile(r"(?i)imported\s+from")
        wrappers = [p for p in paths if wrapper_re.search(p.split(" > ")[-1])]
        assert len(wrappers) == 0

    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_favorites_no_empty_folders(self) -> None:
        from bookmark_cleaner.parsers.netscape import parse_netscape

        tree = parse_netscape("favorites_3_17_26.html")
        result = run_pipeline(tree)

        def has_empty(folder: FolderNode) -> list[str]:
            empties: list[str] = []
            for child in folder.children:
                if not child.children and not child.bookmarks:
                    empties.append(child.name)
                empties.extend(has_empty(child))
            return empties

        empties = has_empty(result.tree.root)
        assert len(empties) == 0

    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_favorites_no_new_folders(self) -> None:
        import re

        from bookmark_cleaner.parsers.netscape import parse_netscape
        from bookmark_cleaner.tree import folder_paths

        tree = parse_netscape("favorites_3_17_26.html")
        result = run_pipeline(tree)
        paths = folder_paths(result.tree.root)
        generic_re = re.compile(r"(?i)^(new|untitled)\s+folder")
        generics = [p for p in paths if generic_re.match(p.split(" > ")[-1])]
        assert len(generics) == 0

    @pytest.mark.skipif(
        not Path("bookmarks_1_23_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_bookmarks_url_count_preserved(self) -> None:
        from bookmark_cleaner.normalize import normalize_url
        from bookmark_cleaner.parsers.netscape import parse_netscape

        tree = parse_netscape("bookmarks_1_23_26.html")
        original_normalized = {normalize_url(bm.url) for bm in collect_bookmarks(tree.root)}
        result = run_pipeline(tree)
        result_normalized = {normalize_url(bm.url) for bm in collect_bookmarks(result.tree.root)}
        assert len(result_normalized) == len(original_normalized)
