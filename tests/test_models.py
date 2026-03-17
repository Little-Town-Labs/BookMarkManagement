"""Tests for bookmark_cleaner.models — BookmarkNode, FolderNode, BookmarkTree."""
from __future__ import annotations

import dataclasses

import pytest

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode

# ── BookmarkNode ──────────────────────────────────────────────────────


class TestBookmarkNodeCreation:
    def test_create_with_url_only(self) -> None:
        node = BookmarkNode(url="https://example.com")
        assert node.url == "https://example.com"
        assert node.title == ""
        assert node.add_date == 0
        assert node.icon == ""
        assert node.attrs == ()

    def test_create_with_all_fields(self) -> None:
        node = BookmarkNode(
            url="https://example.com",
            title="Example",
            add_date=1700000000,
            icon="data:image/png;base64,abc123",
            attrs=(("SHORTCUTURL", "ex"), ("TAGS", "test")),
        )
        assert node.url == "https://example.com"
        assert node.title == "Example"
        assert node.add_date == 1700000000
        assert node.icon == "data:image/png;base64,abc123"
        assert node.attrs == (("SHORTCUTURL", "ex"), ("TAGS", "test"))

    def test_empty_url_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="url"):
            BookmarkNode(url="")

    def test_unicode_title_preserved(self) -> None:
        node = BookmarkNode(url="https://example.jp", title="日本語テスト 🔖")
        assert node.title == "日本語テスト 🔖"

    def test_large_icon_stored(self) -> None:
        large_icon = "data:image/png;base64," + "A" * 50_000
        node = BookmarkNode(url="https://example.com", icon=large_icon)
        assert len(node.icon) > 50_000

    def test_attrs_accessible(self) -> None:
        node = BookmarkNode(
            url="https://example.com",
            attrs=(("PERSONAL_TOOLBAR_FOLDER", "true"), ("ADD_DATE", "12345")),
        )
        assert len(node.attrs) == 2
        assert node.attrs[0] == ("PERSONAL_TOOLBAR_FOLDER", "true")


class TestBookmarkNodeImmutability:
    def test_cannot_set_url(self) -> None:
        node = BookmarkNode(url="https://example.com")
        with pytest.raises(dataclasses.FrozenInstanceError):
            node.url = "https://other.com"  # type: ignore[misc]

    def test_cannot_set_title(self) -> None:
        node = BookmarkNode(url="https://example.com", title="Original")
        with pytest.raises(dataclasses.FrozenInstanceError):
            node.title = "Changed"  # type: ignore[misc]


class TestBookmarkNodeEquality:
    def test_same_fields_are_equal(self) -> None:
        a = BookmarkNode(url="https://example.com", title="Example")
        b = BookmarkNode(url="https://example.com", title="Example")
        assert a == b

    def test_different_url_not_equal(self) -> None:
        a = BookmarkNode(url="https://example.com")
        b = BookmarkNode(url="https://other.com")
        assert a != b

    def test_different_title_not_equal(self) -> None:
        a = BookmarkNode(url="https://example.com", title="A")
        b = BookmarkNode(url="https://example.com", title="B")
        assert a != b

    def test_hashable(self) -> None:
        node = BookmarkNode(url="https://example.com")
        assert isinstance(hash(node), int)


# ── FolderNode ────────────────────────────────────────────────────────


class TestFolderNodeCreation:
    def test_create_empty_folder(self) -> None:
        folder = FolderNode(name="Empty")
        assert folder.name == "Empty"
        assert folder.children == ()
        assert folder.bookmarks == ()
        assert folder.add_date == 0
        assert folder.last_modified == 0
        assert folder.attrs == ()

    def test_create_with_children_and_bookmarks(self) -> None:
        bm = BookmarkNode(url="https://example.com", title="Example")
        child = FolderNode(name="Child")
        folder = FolderNode(
            name="Parent",
            children=(child,),
            bookmarks=(bm,),
            add_date=1700000000,
            last_modified=1700000001,
        )
        assert len(folder.children) == 1
        assert len(folder.bookmarks) == 1
        assert folder.children[0].name == "Child"
        assert folder.bookmarks[0].url == "https://example.com"

    def test_deep_nesting(self) -> None:
        folder = FolderNode(name="level-20")
        for i in range(19, 0, -1):
            folder = FolderNode(name=f"level-{i}", children=(folder,))
        assert folder.name == "level-1"
        # Walk down to level 20
        current = folder
        for _ in range(19):
            current = current.children[0]
        assert current.name == "level-20"

    def test_order_preserved(self) -> None:
        bm_a = BookmarkNode(url="https://a.com", title="A")
        bm_b = BookmarkNode(url="https://b.com", title="B")
        bm_c = BookmarkNode(url="https://c.com", title="C")
        folder = FolderNode(name="Ordered", bookmarks=(bm_c, bm_a, bm_b))
        assert folder.bookmarks[0].title == "C"
        assert folder.bookmarks[1].title == "A"
        assert folder.bookmarks[2].title == "B"

    def test_children_order_preserved(self) -> None:
        child_z = FolderNode(name="Z")
        child_a = FolderNode(name="A")
        folder = FolderNode(name="Parent", children=(child_z, child_a))
        assert folder.children[0].name == "Z"
        assert folder.children[1].name == "A"


class TestFolderNodeImmutability:
    def test_cannot_set_name(self) -> None:
        folder = FolderNode(name="Original")
        with pytest.raises(dataclasses.FrozenInstanceError):
            folder.name = "Changed"  # type: ignore[misc]

    def test_cannot_set_children(self) -> None:
        folder = FolderNode(name="Test")
        with pytest.raises(dataclasses.FrozenInstanceError):
            folder.children = ()  # type: ignore[misc]


class TestFolderNodeEquality:
    def test_same_structure_equal(self) -> None:
        bm = BookmarkNode(url="https://example.com")
        a = FolderNode(name="Test", bookmarks=(bm,))
        b = FolderNode(name="Test", bookmarks=(bm,))
        assert a == b

    def test_different_bookmark_order_not_equal(self) -> None:
        bm1 = BookmarkNode(url="https://a.com")
        bm2 = BookmarkNode(url="https://b.com")
        a = FolderNode(name="Test", bookmarks=(bm1, bm2))
        b = FolderNode(name="Test", bookmarks=(bm2, bm1))
        assert a != b


# ── BookmarkTree ──────────────────────────────────────────────────────


class TestBookmarkTree:
    def test_create_with_defaults(self) -> None:
        tree = BookmarkTree()
        assert tree.root.name == ""
        assert tree.root.children == ()
        assert tree.root.bookmarks == ()
        assert tree.source_format == ""

    def test_create_with_populated_root(self) -> None:
        bm = BookmarkNode(url="https://example.com")
        folder = FolderNode(name="Bar", bookmarks=(bm,))
        root = FolderNode(name="", children=(folder,))
        tree = BookmarkTree(root=root, source_format="netscape")
        assert tree.source_format == "netscape"
        assert len(tree.root.children) == 1
        assert tree.root.children[0].bookmarks[0].url == "https://example.com"

    def test_frozen(self) -> None:
        tree = BookmarkTree()
        with pytest.raises(dataclasses.FrozenInstanceError):
            tree.root = FolderNode(name="hack")  # type: ignore[misc]

    def test_source_format_stored(self) -> None:
        tree = BookmarkTree(source_format="chrome_json")
        assert tree.source_format == "chrome_json"
