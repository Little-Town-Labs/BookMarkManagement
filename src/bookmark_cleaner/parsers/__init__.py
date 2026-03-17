"""Bookmark file format detection and parser/exporter registry."""
from __future__ import annotations

from bookmark_cleaner.parsers.netscape import export_netscape, parse_netscape


def detect_format(file_path: str) -> str:
    """Detect the bookmark file format by inspecting the first 1000 bytes.

    Returns "netscape" for Netscape HTML bookmark files, "unknown" otherwise.
    Raises FileNotFoundError if the file does not exist.
    """
    with open(file_path, "rb") as f:
        head = f.read(1000)
    # Strip UTF-8 BOM if present
    if head.startswith(b"\xef\xbb\xbf"):
        head = head[3:]
    if b"NETSCAPE-Bookmark-file-1" in head:
        return "netscape"
    return "unknown"


__all__ = ["detect_format", "export_netscape", "parse_netscape"]
