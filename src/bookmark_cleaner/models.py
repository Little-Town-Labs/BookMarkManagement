"""Core immutable data model for bookmark-cleaner."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BookmarkNode:
    """An immutable bookmark leaf node."""

    url: str
    title: str = ""
    add_date: int = 0
    icon: str = ""
    attrs: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("BookmarkNode url must be a non-empty string")


@dataclass(frozen=True, slots=True)
class FolderNode:
    """An immutable folder node containing bookmarks and subfolders."""

    name: str
    children: tuple[FolderNode, ...] = ()
    bookmarks: tuple[BookmarkNode, ...] = ()
    add_date: int = 0
    last_modified: int = 0
    attrs: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class BookmarkTree:
    """Root container for a complete bookmark collection."""

    root: FolderNode = field(default_factory=lambda: FolderNode(name=""))
    source_format: str = ""
