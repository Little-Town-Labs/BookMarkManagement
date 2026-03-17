"""Tests for Netscape HTML bookmark parser, exporter, and format detection."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode
from bookmark_cleaner.parsers import detect_format
from bookmark_cleaner.parsers.netscape import export_netscape, parse_netscape
from bookmark_cleaner.tree import (
    collect_bookmarks,
    collect_urls,
    count_items,
    find_folder,
    trees_equal,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ── detect_format ────────────────────────────────────────────────────


class TestDetectFormat:
    def test_netscape_file(self) -> None:
        assert detect_format(str(FIXTURES / "sample_simple.html")) == "netscape"

    def test_json_file(self) -> None:
        assert detect_format(str(FIXTURES / "sample_not_bookmarks.json")) == "unknown"

    def test_empty_file(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.html"
        empty.write_text("")
        assert detect_format(str(empty)) == "unknown"

    def test_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            detect_format("/nonexistent/file.html")

    def test_bom_file(self) -> None:
        assert detect_format(str(FIXTURES / "sample_bom.html")) == "netscape"

    def test_plain_text_file(self, tmp_path: Path) -> None:
        txt = tmp_path / "plain.txt"
        txt.write_text("just some text\nnothing special")
        assert detect_format(str(txt)) == "unknown"


# ── parse_netscape — basic ───────────────────────────────────────────


class TestParseNetscapeBasic:
    @pytest.fixture()
    def tree(self) -> BookmarkTree:
        return parse_netscape(str(FIXTURES / "sample_simple.html"))

    def test_source_format(self, tree: BookmarkTree) -> None:
        assert tree.source_format == "netscape"

    def test_top_level_folder_count(self, tree: BookmarkTree) -> None:
        assert len(tree.root.children) == 1  # "Favorites bar"

    def test_total_bookmark_count(self, tree: BookmarkTree) -> None:
        all_bm = collect_bookmarks(tree.root)
        assert len(all_bm) == 5

    def test_bookmark_urls(self, tree: BookmarkTree) -> None:
        urls = collect_urls(tree.root)
        assert "https://github.com" in urls
        assert "https://stackoverflow.com" in urls
        assert "https://reddit.com" in urls
        assert "https://example.com" in urls
        assert "https://python.org" in urls

    def test_bookmark_titles(self, tree: BookmarkTree) -> None:
        all_bm = collect_bookmarks(tree.root)
        titles = {bm.title for bm in all_bm}
        assert "GitHub" in titles
        assert "Stack Overflow" in titles

    def test_bookmark_add_date_is_int(self, tree: BookmarkTree) -> None:
        all_bm = collect_bookmarks(tree.root)
        for bm in all_bm:
            assert isinstance(bm.add_date, int)
            assert bm.add_date > 0

    def test_bookmark_icon_preserved(self, tree: BookmarkTree) -> None:
        all_bm = collect_bookmarks(tree.root)
        github = next(bm for bm in all_bm if bm.title == "GitHub")
        assert github.icon == "data:image/png;base64,abc123"

    def test_folder_names(self, tree: BookmarkTree) -> None:
        fav = tree.root.children[0]
        assert fav.name == "Favorites bar"
        child_names = {c.name for c in fav.children}
        assert "Development" in child_names
        assert "Social Media" in child_names

    def test_folder_add_date_is_int(self, tree: BookmarkTree) -> None:
        fav = tree.root.children[0]
        assert isinstance(fav.add_date, int)
        assert fav.add_date == 1700000000

    def test_folder_last_modified_is_int(self, tree: BookmarkTree) -> None:
        fav = tree.root.children[0]
        assert isinstance(fav.last_modified, int)
        assert fav.last_modified == 1700000001

    def test_personal_toolbar_folder_attr(self, tree: BookmarkTree) -> None:
        fav = tree.root.children[0]
        attr_dict = dict(fav.attrs)
        assert attr_dict.get("PERSONAL_TOOLBAR_FOLDER") == "true"

    def test_bookmark_ordering(self, tree: BookmarkTree) -> None:
        dev = find_folder(tree.root, "Development")
        assert dev is not None
        assert dev.bookmarks[0].title == "GitHub"
        assert dev.bookmarks[1].title == "Stack Overflow"

    def test_bookmarks_at_folder_level(self, tree: BookmarkTree) -> None:
        """Bookmarks directly under Favorites bar (not in subfolders)."""
        fav = tree.root.children[0]
        direct_titles = [bm.title for bm in fav.bookmarks]
        assert "Example Site" in direct_titles
        assert "Python" in direct_titles


# ── parse_netscape — edge cases ──────────────────────────────────────


class TestParseNetscapeEdgeCases:
    def test_empty_file(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_empty.html"))
        all_bm = collect_bookmarks(tree.root)
        assert len(all_bm) == 0
        assert len(tree.root.children) == 0

    def test_nested_levels(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_nested.html"))
        # Traverse down: root > Level 1 > Level 2 > Level 3 > Level 4 > Level 5
        folder = tree.root
        for name in ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]:
            found = find_folder(folder, name)
            assert found is not None, f"Could not find folder '{name}'"
            folder = found
        # Deepest folder has the bookmark
        assert len(folder.bookmarks) == 1
        assert folder.bookmarks[0].url == "https://deep.example.com"

    def test_entities_decoded(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_entities.html"))
        folder = tree.root.children[0]
        assert folder.name == "Banks & Credit Cards"
        bm_titles = [bm.title for bm in folder.bookmarks]
        assert "Search & Find" in bm_titles
        assert "Use <tags> here" in bm_titles

    def test_unicode_and_emoji(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_entities.html"))
        folder = tree.root.children[0]
        bm_titles = [bm.title for bm in folder.bookmarks]
        assert "日本語テスト 🔖" in bm_titles

    def test_entity_in_url(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_entities.html"))
        urls = collect_urls(tree.root)
        assert "https://example.com/search?a=1&b=2" in urls

    def test_no_href_skipped(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_no_href.html"))
        all_bm = collect_bookmarks(tree.root)
        assert len(all_bm) == 2
        urls = {bm.url for bm in all_bm}
        assert "https://good.example.com" in urls
        assert "https://also-good.example.com" in urls

    def test_bom_file_parses(self) -> None:
        tree = parse_netscape(str(FIXTURES / "sample_bom.html"))
        assert tree.source_format == "netscape"


# ── export_netscape ──────────────────────────────────────────────────


class TestExportNetscape:
    @pytest.fixture()
    def simple_tree(self) -> BookmarkTree:
        return BookmarkTree(
            root=FolderNode(
                name="",
                children=(
                    FolderNode(
                        name="Test Folder",
                        add_date=1000,
                        last_modified=2000,
                        attrs=(("PERSONAL_TOOLBAR_FOLDER", "true"),),
                        bookmarks=(
                            BookmarkNode(
                                url="https://example.com",
                                title="Example",
                                add_date=3000,
                                icon="data:image/png;base64,abc",
                            ),
                            BookmarkNode(
                                url="https://special.com",
                                title="A & B <C>",
                                add_date=4000,
                            ),
                        ),
                    ),
                ),
            ),
            source_format="netscape",
        )

    def test_starts_with_doctype(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>")

    def test_contains_meta_charset(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert "charset=UTF-8" in content

    def test_bookmark_href(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'HREF="https://example.com"' in content

    def test_bookmark_add_date(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'ADD_DATE="3000"' in content

    def test_bookmark_icon(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'ICON="data:image/png;base64,abc"' in content

    def test_no_empty_icon(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        # The second bookmark has no icon — should not have ICON=""
        lines = [l for l in content.splitlines() if "A &amp; B" in l]
        assert len(lines) == 1
        assert 'ICON=""' not in lines[0]

    def test_folder_add_date(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'ADD_DATE="1000"' in content

    def test_folder_last_modified(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'LAST_MODIFIED="2000"' in content

    def test_extra_attrs_preserved(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert 'PERSONAL_TOOLBAR_FOLDER="true"' in content

    def test_special_chars_escaped(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert "A &amp; B &lt;C&gt;" in content

    def test_indentation(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        export_netscape(simple_tree, str(out))
        lines = out.read_text(encoding="utf-8").splitlines()
        # Folder header should be at 4 spaces
        folder_lines = [l for l in lines if "Test Folder" in l]
        assert len(folder_lines) == 1
        assert folder_lines[0].startswith("    <DT><H3")

    def test_file_created(self, simple_tree: BookmarkTree, tmp_path: Path) -> None:
        out = tmp_path / "out.html"
        assert not out.exists()
        export_netscape(simple_tree, str(out))
        assert out.exists()

    def test_empty_tree(self, tmp_path: Path) -> None:
        tree = BookmarkTree(root=FolderNode(name=""), source_format="netscape")
        out = tmp_path / "empty_out.html"
        export_netscape(tree, str(out))
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in content
        assert "<DL><p>" in content


# ── Roundtrip tests ──────────────────────────────────────────────────


class TestRoundtrip:
    def test_simple_roundtrip(self, tmp_path: Path) -> None:
        original = parse_netscape(str(FIXTURES / "sample_simple.html"))
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert trees_equal(original, reparsed, ignore_metadata=True)

    def test_simple_url_count(self, tmp_path: Path) -> None:
        original = parse_netscape(str(FIXTURES / "sample_simple.html"))
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert collect_urls(original.root) == collect_urls(reparsed.root)

    def test_simple_folder_count(self, tmp_path: Path) -> None:
        original = parse_netscape(str(FIXTURES / "sample_simple.html"))
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert count_items(original.root) == count_items(reparsed.root)

    def test_entities_roundtrip(self, tmp_path: Path) -> None:
        original = parse_netscape(str(FIXTURES / "sample_entities.html"))
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert trees_equal(original, reparsed, ignore_metadata=True)

    def test_nested_roundtrip(self, tmp_path: Path) -> None:
        original = parse_netscape(str(FIXTURES / "sample_nested.html"))
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert trees_equal(original, reparsed, ignore_metadata=True)


# ── Real-file integration tests ──────────────────────────────────────


class TestParseNetscapeValidation:
    def test_non_bookmark_file_raises(self) -> None:
        with pytest.raises(ValueError, match="not a Netscape bookmark file"):
            parse_netscape(str(FIXTURES / "sample_not_bookmarks.json"))

    def test_plain_text_raises(self, tmp_path: Path) -> None:
        txt = tmp_path / "plain.txt"
        txt.write_text("just some text")
        with pytest.raises(ValueError, match="not a Netscape bookmark file"):
            parse_netscape(str(txt))


class TestRealFiles:
    @pytest.mark.skipif(
        not (Path("favorites_3_17_26.html").exists()),
        reason="Real bookmark file not available",
    )
    def test_parse_favorites(self) -> None:
        tree = parse_netscape("favorites_3_17_26.html")
        all_bm = collect_bookmarks(tree.root)
        assert len(all_bm) == 2503

    @pytest.mark.skipif(
        not (Path("bookmarks_1_23_26.html").exists()),
        reason="Real bookmark file not available",
    )
    def test_parse_bookmarks(self) -> None:
        tree = parse_netscape("bookmarks_1_23_26.html")
        all_bm = collect_bookmarks(tree.root)
        assert len(all_bm) > 0

    @pytest.mark.skipif(
        not (Path("favorites_3_17_26.html").exists()),
        reason="Real bookmark file not available",
    )
    def test_roundtrip_favorites(self, tmp_path: Path) -> None:
        original = parse_netscape("favorites_3_17_26.html")
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert collect_urls(original.root) == collect_urls(reparsed.root)

    @pytest.mark.skipif(
        not (Path("bookmarks_1_23_26.html").exists()),
        reason="Real bookmark file not available",
    )
    def test_roundtrip_bookmarks(self, tmp_path: Path) -> None:
        original = parse_netscape("bookmarks_1_23_26.html")
        out = tmp_path / "roundtrip.html"
        export_netscape(original, str(out))
        reparsed = parse_netscape(str(out))
        assert collect_urls(original.root) == collect_urls(reparsed.root)
