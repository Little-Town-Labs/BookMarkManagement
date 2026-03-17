"""Netscape HTML bookmark parser and exporter."""
from __future__ import annotations

import html
from html.parser import HTMLParser

from bookmark_cleaner.models import BookmarkNode, BookmarkTree, FolderNode


# ── Internal mutable structures for parsing ──────────────────────────


class _MutableFolder:
    """Mutable folder used during parsing, frozen to FolderNode afterwards."""

    __slots__ = ("name", "children", "bookmarks", "add_date", "last_modified", "attrs")

    def __init__(
        self,
        name: str = "",
        add_date: int = 0,
        last_modified: int = 0,
        attrs: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.name = name
        self.children: list[_MutableFolder] = []
        self.bookmarks: list[BookmarkNode] = []
        self.add_date = add_date
        self.last_modified = last_modified
        self.attrs = attrs


def _freeze(mf: _MutableFolder) -> FolderNode:
    """Recursively convert a mutable folder tree to an immutable FolderNode tree."""
    return FolderNode(
        name=mf.name,
        children=tuple(_freeze(child) for child in mf.children),
        bookmarks=tuple(mf.bookmarks),
        add_date=mf.add_date,
        last_modified=mf.last_modified,
        attrs=mf.attrs,
    )


# ── Known attribute sets ─────────────────────────────────────────────

_BOOKMARK_KNOWN = {"HREF", "ADD_DATE", "ICON"}
_FOLDER_KNOWN = {"ADD_DATE", "LAST_MODIFIED"}


def _safe_int(value: str) -> int:
    """Convert a string to int, returning 0 on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _extra_attrs(
    raw_attrs: list[tuple[str, str | None]], known: set[str]
) -> tuple[tuple[str, str], ...]:
    """Extract attrs not in the known set as a tuple of (KEY, value) pairs.

    Keys are uppercased to match Netscape format convention.
    """
    return tuple(
        (k.upper(), v or "")
        for k, v in raw_attrs
        if k.upper() not in known and v is not None
    )


# ── HTML parser handler ──────────────────────────────────────────────


class _NetscapeHandler(HTMLParser):
    """Event-driven Netscape bookmark HTML parser."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _MutableFolder(name="")
        self.folder_stack: list[_MutableFolder] = [self.root]
        self._pending_folder_attrs: list[tuple[str, str | None]] | None = None
        self._pending_folder_name: str = ""
        self._in_folder_title = False
        self._current_bm_attrs: list[tuple[str, str | None]] | None = None
        self._current_bm_title: str = ""
        self._in_bookmark = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower == "h3":
            self._pending_folder_attrs = attrs
            self._pending_folder_name = ""
            self._in_folder_title = True
        elif tag_lower == "a":
            self._current_bm_attrs = attrs
            self._current_bm_title = ""
            self._in_bookmark = True

    def handle_data(self, data: str) -> None:
        if self._in_folder_title:
            self._pending_folder_name += data
        elif self._in_bookmark:
            self._current_bm_title += data

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "h3" and self._pending_folder_attrs is not None:
            self._in_folder_title = False
            raw = {k.upper(): v or "" for k, v in self._pending_folder_attrs}
            folder = _MutableFolder(
                name=self._pending_folder_name,
                add_date=_safe_int(raw.get("ADD_DATE", "")),
                last_modified=_safe_int(raw.get("LAST_MODIFIED", "")),
                attrs=_extra_attrs(self._pending_folder_attrs, _FOLDER_KNOWN),
            )
            self.folder_stack[-1].children.append(folder)
            self.folder_stack.append(folder)
            self._pending_folder_attrs = None

        elif tag_lower == "a" and self._current_bm_attrs is not None:
            self._in_bookmark = False
            raw = {k.upper(): v or "" for k, v in self._current_bm_attrs}
            url = raw.get("HREF", "")
            if url:  # Skip bookmarks without HREF
                bm = BookmarkNode(
                    url=url,
                    title=self._current_bm_title,
                    add_date=_safe_int(raw.get("ADD_DATE", "")),
                    icon=raw.get("ICON", ""),
                    attrs=_extra_attrs(self._current_bm_attrs, _BOOKMARK_KNOWN),
                )
                self.folder_stack[-1].bookmarks.append(bm)
            self._current_bm_attrs = None

        elif tag_lower == "dl":
            # Pop folder stack, but never pop past root
            if len(self.folder_stack) > 1:
                self.folder_stack.pop()


# ── Public API ───────────────────────────────────────────────────────


def parse_netscape(file_path: str) -> BookmarkTree:
    """Parse a Netscape HTML bookmark file into an immutable BookmarkTree.

    Raises ValueError if the file is not a Netscape bookmark file.
    """
    with open(file_path, encoding="utf-8-sig") as f:
        content = f.read()

    if "NETSCAPE-Bookmark-file-1" not in content[:1000]:
        raise ValueError(f"File is not a Netscape bookmark file: {file_path}")

    handler = _NetscapeHandler()
    handler.feed(content)

    return BookmarkTree(
        root=_freeze(handler.root),
        source_format="netscape",
    )


def export_netscape(tree: BookmarkTree, file_path: str) -> None:
    """Export a BookmarkTree to a Netscape HTML bookmark file."""
    lines: list[str] = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>",
    ]

    _write_folder_contents(tree.root, depth=1, lines=lines)

    lines.append("</DL><p>")

    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")


def _write_folder_contents(
    folder: FolderNode, depth: int, lines: list[str]
) -> None:
    """Write the contents of a folder (children and bookmarks) at the given depth."""
    indent = "    " * depth

    for child in folder.children:
        # Build folder attrs string
        folder_attrs = f' ADD_DATE="{child.add_date}"'
        if child.last_modified:
            folder_attrs += f' LAST_MODIFIED="{child.last_modified}"'
        for key, value in child.attrs:
            folder_attrs += f' {key}="{html.escape(value, quote=True)}"'

        lines.append(f"{indent}<DT><H3{folder_attrs}>{html.escape(child.name)}</H3>")
        lines.append(f"{indent}<DL><p>")
        _write_folder_contents(child, depth + 1, lines)
        lines.append(f"{indent}</DL><p>")

    for bm in folder.bookmarks:
        bm_attrs = f' HREF="{html.escape(bm.url, quote=True)}"'
        bm_attrs += f' ADD_DATE="{bm.add_date}"'
        if bm.icon:
            bm_attrs += f' ICON="{html.escape(bm.icon, quote=True)}"'
        for key, value in bm.attrs:
            bm_attrs += f' {key}="{html.escape(value, quote=True)}"'
        lines.append(f"{indent}<DT><A{bm_attrs}>{html.escape(bm.title)}</A>")
