"""Tests for bookmark_cleaner.tree — traversal, transformation, and comparison utilities."""
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

# ── Fixtures ──────────────────────────────────────────────────────────

BM_GITHUB = BookmarkNode(url="https://github.com", title="GitHub")
BM_STACKOVERFLOW = BookmarkNode(url="https://stackoverflow.com", title="Stack Overflow")
BM_PYTHON = BookmarkNode(url="https://python.org", title="Python")
BM_REDDIT = BookmarkNode(url="https://reddit.com", title="Reddit")
BM_GITHUB_DUP = BookmarkNode(url="https://github.com", title="GitHub (Duplicate)")


def _make_sample_tree() -> BookmarkTree:
    """Build a realistic bookmark tree for testing.

    Structure:
        root
        ├── Development (bookmarks: GitHub, StackOverflow)
        │   └── Python (bookmarks: Python)
        └── Social Media (bookmarks: Reddit)
    """
    python_folder = FolderNode(name="Python", bookmarks=(BM_PYTHON,))
    dev_folder = FolderNode(
        name="Development",
        children=(python_folder,),
        bookmarks=(BM_GITHUB, BM_STACKOVERFLOW),
    )
    social_folder = FolderNode(name="Social Media", bookmarks=(BM_REDDIT,))
    root = FolderNode(name="", children=(dev_folder, social_folder))
    return BookmarkTree(root=root, source_format="netscape")


# ── Task 2.1: Traversal & Query Functions ─────────────────────────────


class TestCollectBookmarks:
    def test_empty_folder(self) -> None:
        folder = FolderNode(name="Empty")
        assert collect_bookmarks(folder) == ()

    def test_flat_folder(self) -> None:
        folder = FolderNode(name="Flat", bookmarks=(BM_GITHUB, BM_PYTHON))
        result = collect_bookmarks(folder)
        assert len(result) == 2
        assert BM_GITHUB in result
        assert BM_PYTHON in result

    def test_nested_folders_depth_first(self) -> None:
        tree = _make_sample_tree()
        result = collect_bookmarks(tree.root)
        assert len(result) == 4
        urls = [bm.url for bm in result]
        assert "https://github.com" in urls
        assert "https://stackoverflow.com" in urls
        assert "https://python.org" in urls
        assert "https://reddit.com" in urls

    def test_duplicate_urls_not_deduplicated(self) -> None:
        folder = FolderNode(name="Dupes", bookmarks=(BM_GITHUB, BM_GITHUB_DUP))
        result = collect_bookmarks(folder)
        assert len(result) == 2


class TestCollectUrls:
    def test_empty_folder(self) -> None:
        folder = FolderNode(name="Empty")
        assert collect_urls(folder) == frozenset()

    def test_unique_urls(self) -> None:
        folder = FolderNode(name="Test", bookmarks=(BM_GITHUB, BM_PYTHON))
        assert collect_urls(folder) == frozenset({"https://github.com", "https://python.org"})

    def test_duplicates_deduplicated(self) -> None:
        folder = FolderNode(name="Dupes", bookmarks=(BM_GITHUB, BM_GITHUB_DUP))
        result = collect_urls(folder)
        assert len(result) == 1
        assert "https://github.com" in result

    def test_nested_folders_included(self) -> None:
        tree = _make_sample_tree()
        result = collect_urls(tree.root)
        assert len(result) == 4


class TestCountItems:
    def test_empty_tree(self) -> None:
        folder = FolderNode(name="Empty")
        bm_count, folder_count = count_items(folder)
        assert bm_count == 0
        assert folder_count == 0

    def test_flat_folder(self) -> None:
        folder = FolderNode(name="Flat", bookmarks=(BM_GITHUB, BM_PYTHON, BM_REDDIT))
        bm_count, folder_count = count_items(folder)
        assert bm_count == 3
        assert folder_count == 0

    def test_nested_recursive(self) -> None:
        tree = _make_sample_tree()
        bm_count, folder_count = count_items(tree.root)
        assert bm_count == 4
        assert folder_count == 3  # Development, Python, Social Media


class TestFolderPaths:
    def test_empty_folder(self) -> None:
        folder = FolderNode(name="Lonely")
        result = folder_paths(folder)
        assert result == ()

    def test_single_child(self) -> None:
        grandchild = FolderNode(name="Grandchild")
        child = FolderNode(name="Child", children=(grandchild,))
        root = FolderNode(name="", children=(child,))
        result = folder_paths(root)
        assert "Child" in result
        assert "Child > Grandchild" in result

    def test_nested_paths(self) -> None:
        tree = _make_sample_tree()
        result = folder_paths(tree.root)
        assert "Development" in result
        assert "Development > Python" in result
        assert "Social Media" in result

    def test_root_empty_name_not_prefixed(self) -> None:
        tree = _make_sample_tree()
        result = folder_paths(tree.root)
        # Paths should not start with " > "
        for path in result:
            assert not path.startswith(" > ")
            assert not path.startswith(">")


class TestFindFolder:
    def test_exact_match(self) -> None:
        tree = _make_sample_tree()
        result = find_folder(tree.root, "Development")
        assert result is not None
        assert result.name == "Development"

    def test_case_insensitive(self) -> None:
        tree = _make_sample_tree()
        result = find_folder(tree.root, "social media")
        assert result is not None
        assert result.name == "Social Media"

    def test_not_found(self) -> None:
        tree = _make_sample_tree()
        result = find_folder(tree.root, "Nonexistent")
        assert result is None

    def test_finds_nested(self) -> None:
        tree = _make_sample_tree()
        result = find_folder(tree.root, "Python")
        assert result is not None
        assert result.name == "Python"

    def test_returns_first_depth_first(self) -> None:
        dup1 = FolderNode(name="Shared", bookmarks=(BM_GITHUB,))
        dup2 = FolderNode(name="Shared", bookmarks=(BM_PYTHON,))
        root = FolderNode(name="", children=(dup1, dup2))
        result = find_folder(root, "Shared")
        assert result is not None
        assert result.bookmarks[0].url == "https://github.com"


# ── Task 2.3: Transformation Functions ────────────────────────────────


class TestReplaceBookmarks:
    def test_returns_new_folder(self) -> None:
        original = FolderNode(name="Test", bookmarks=(BM_GITHUB,))
        new_bms = (BM_PYTHON, BM_REDDIT)
        result = replace_bookmarks(original, new_bms)
        assert result.bookmarks == new_bms
        assert result is not original

    def test_preserves_other_fields(self) -> None:
        child = FolderNode(name="Child")
        original = FolderNode(
            name="Test",
            children=(child,),
            bookmarks=(BM_GITHUB,),
            add_date=100,
            last_modified=200,
            attrs=(("key", "val"),),
        )
        result = replace_bookmarks(original, (BM_PYTHON,))
        assert result.name == "Test"
        assert result.children == (child,)
        assert result.add_date == 100
        assert result.last_modified == 200
        assert result.attrs == (("key", "val"),)

    def test_original_unchanged(self) -> None:
        original = FolderNode(name="Test", bookmarks=(BM_GITHUB,))
        replace_bookmarks(original, (BM_PYTHON,))
        assert original.bookmarks == (BM_GITHUB,)


class TestReplaceChildren:
    def test_returns_new_folder(self) -> None:
        original = FolderNode(name="Test", children=(FolderNode(name="Old"),))
        new_child = FolderNode(name="New")
        result = replace_children(original, (new_child,))
        assert result.children == (new_child,)
        assert result is not original

    def test_preserves_other_fields(self) -> None:
        original = FolderNode(
            name="Test",
            bookmarks=(BM_GITHUB,),
            add_date=100,
        )
        result = replace_children(original, (FolderNode(name="Child"),))
        assert result.name == "Test"
        assert result.bookmarks == (BM_GITHUB,)
        assert result.add_date == 100

    def test_original_unchanged(self) -> None:
        old_child = FolderNode(name="Old")
        original = FolderNode(name="Test", children=(old_child,))
        replace_children(original, (FolderNode(name="New"),))
        assert original.children == (old_child,)


class TestMapTree:
    def test_identity_returns_equal(self) -> None:
        tree = _make_sample_tree()
        result = map_tree(tree.root, lambda f: f)
        assert result == tree.root

    def test_renames_all_folders(self) -> None:
        tree = _make_sample_tree()

        def upper_name(f: FolderNode) -> FolderNode:
            return FolderNode(
                name=f.name.upper(),
                children=f.children,
                bookmarks=f.bookmarks,
                add_date=f.add_date,
                last_modified=f.last_modified,
                attrs=f.attrs,
            )

        result = map_tree(tree.root, upper_name)
        # Check nested folder was also renamed
        dev = result.children[0]
        assert dev.name == "DEVELOPMENT"
        python_folder = dev.children[0]
        assert python_folder.name == "PYTHON"

    def test_bottom_up_order(self) -> None:
        """Children should be processed before their parent."""
        order: list[str] = []

        def track(f: FolderNode) -> FolderNode:
            if f.name:  # skip root
                order.append(f.name)
            return f

        tree = _make_sample_tree()
        map_tree(tree.root, track)
        # Python should appear before Development (child before parent)
        assert order.index("Python") < order.index("Development")

    def test_original_unchanged(self) -> None:
        tree = _make_sample_tree()
        original_name = tree.root.children[0].name

        def upper_name(f: FolderNode) -> FolderNode:
            return FolderNode(
                name=f.name.upper(),
                children=f.children,
                bookmarks=f.bookmarks,
            )

        map_tree(tree.root, upper_name)
        assert tree.root.children[0].name == original_name

    def test_works_on_deep_tree(self) -> None:
        folder = FolderNode(name="level-3", bookmarks=(BM_GITHUB,))
        folder = FolderNode(name="level-2", children=(folder,))
        folder = FolderNode(name="level-1", children=(folder,))

        def add_suffix(f: FolderNode) -> FolderNode:
            return FolderNode(name=f.name + "-mapped", children=f.children, bookmarks=f.bookmarks)

        result = map_tree(folder, add_suffix)
        assert result.name == "level-1-mapped"
        assert result.children[0].name == "level-2-mapped"
        assert result.children[0].children[0].name == "level-3-mapped"


# ── Task 2.5: Equality & Comparison ──────────────────────────────────


class TestTreesEqual:
    def test_identical_trees(self) -> None:
        a = _make_sample_tree()
        b = _make_sample_tree()
        assert trees_equal(a, b) is True

    def test_different_bookmark_url(self) -> None:
        a = _make_sample_tree()
        different_bm = BookmarkNode(url="https://different.com", title="GitHub")
        dev = a.root.children[0]
        new_dev = replace_bookmarks(dev, (different_bm, BM_STACKOVERFLOW))
        new_root = replace_children(a.root, (new_dev, a.root.children[1]))
        b = BookmarkTree(root=new_root, source_format="netscape")
        assert trees_equal(a, b) is False

    def test_different_folder_name(self) -> None:
        a = _make_sample_tree()
        renamed = FolderNode(
            name="Dev",
            children=a.root.children[0].children,
            bookmarks=a.root.children[0].bookmarks,
        )
        new_root = replace_children(a.root, (renamed, a.root.children[1]))
        b = BookmarkTree(root=new_root, source_format="netscape")
        assert trees_equal(a, b) is False

    def test_different_folder_structure(self) -> None:
        a = _make_sample_tree()
        # Remove Social Media folder
        new_root = replace_children(a.root, (a.root.children[0],))
        b = BookmarkTree(root=new_root, source_format="netscape")
        assert trees_equal(a, b) is False

    def test_different_bookmark_order(self) -> None:
        a = _make_sample_tree()
        dev = a.root.children[0]
        reordered = replace_bookmarks(dev, (BM_STACKOVERFLOW, BM_GITHUB))
        new_root = replace_children(a.root, (reordered, a.root.children[1]))
        b = BookmarkTree(root=new_root, source_format="netscape")
        assert trees_equal(a, b) is False

    def test_ignore_metadata_dates(self) -> None:
        bm_a = BookmarkNode(url="https://github.com", title="GitHub", add_date=100)
        bm_b = BookmarkNode(url="https://github.com", title="GitHub", add_date=999)
        folder_a = FolderNode(name="Test", bookmarks=(bm_a,))
        folder_b = FolderNode(name="Test", bookmarks=(bm_b,))
        a = BookmarkTree(root=folder_a)
        b = BookmarkTree(root=folder_b)
        assert trees_equal(a, b, ignore_metadata=False) is False
        assert trees_equal(a, b, ignore_metadata=True) is True

    def test_ignore_metadata_icons(self) -> None:
        bm_a = BookmarkNode(url="https://x.com", title="X", icon="icon-a")
        bm_b = BookmarkNode(url="https://x.com", title="X", icon="icon-b")
        a = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_a,)))
        b = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_b,)))
        assert trees_equal(a, b, ignore_metadata=True) is True

    def test_ignore_metadata_still_checks_urls(self) -> None:
        bm_a = BookmarkNode(url="https://a.com", title="A", add_date=100)
        bm_b = BookmarkNode(url="https://b.com", title="A", add_date=100)
        a = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_a,)))
        b = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_b,)))
        assert trees_equal(a, b, ignore_metadata=True) is False


class TestFirstDifference:
    def test_identical_trees_none(self) -> None:
        a = _make_sample_tree()
        b = _make_sample_tree()
        assert first_difference(a, b) is None

    def test_different_folder_name(self) -> None:
        a = BookmarkTree(root=FolderNode(name="A"))
        b = BookmarkTree(root=FolderNode(name="B"))
        diff = first_difference(a, b)
        assert diff is not None
        assert "A" in diff or "B" in diff

    def test_different_bookmark_count(self) -> None:
        a = BookmarkTree(root=FolderNode(name="", bookmarks=(BM_GITHUB,)))
        b = BookmarkTree(root=FolderNode(name="", bookmarks=(BM_GITHUB, BM_PYTHON)))
        diff = first_difference(a, b)
        assert diff is not None

    def test_different_url(self) -> None:
        bm_a = BookmarkNode(url="https://a.com", title="A")
        bm_b = BookmarkNode(url="https://b.com", title="B")
        a = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_a,)))
        b = BookmarkTree(root=FolderNode(name="", bookmarks=(bm_b,)))
        diff = first_difference(a, b)
        assert diff is not None

    def test_nested_difference_includes_path(self) -> None:
        inner_a = FolderNode(name="Inner", bookmarks=(BM_GITHUB,))
        inner_b = FolderNode(name="Inner", bookmarks=(BM_PYTHON,))
        a = BookmarkTree(root=FolderNode(name="", children=(inner_a,)))
        b = BookmarkTree(root=FolderNode(name="", children=(inner_b,)))
        diff = first_difference(a, b)
        assert diff is not None
        assert "Inner" in diff
