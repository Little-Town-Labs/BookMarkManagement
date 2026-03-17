#!/usr/bin/env python3
"""
Clean up a Netscape bookmark HTML file by deduplicating URLs,
merging duplicate folders, removing empty folders, and sorting.
"""

import re
import sys
from html.parser import HTMLParser
from collections import defaultdict

INPUT_FILE = "/mnt/g/BookMarkManagement/favorites_3_17_26.html"
OUTPUT_FILE = "/mnt/g/BookMarkManagement/favorites_3_17_26_cleaned.html"

# Max icon data size in characters (roughly 2KB base64 ~ 2730 chars)
MAX_ICON_SIZE = 2730


class Bookmark:
    def __init__(self, href, title, add_date=0, icon="", attrs=None):
        self.href = href
        self.title = title
        self.add_date = int(add_date) if add_date else 0
        self.icon = icon
        self.attrs = attrs or {}

    def __repr__(self):
        return f"Bookmark({self.title!r}, {self.href!r})"


class Folder:
    def __init__(self, name, add_date=0, attrs=None):
        self.name = name
        self.add_date = int(add_date) if add_date else 0
        self.attrs = attrs or {}
        self.bookmarks = []  # list of Bookmark
        self.subfolders = []  # list of Folder

    def __repr__(self):
        return f"Folder({self.name!r}, {len(self.bookmarks)} bm, {len(self.subfolders)} sub)"


def parse_bookmarks(filepath):
    """Parse the Netscape bookmark HTML file into a tree of Folder/Bookmark objects."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    root = Folder("root")
    folder_stack = [root]

    # We'll parse line by line using regex
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Folder header: <DT><H3 ...>Name</H3>
        m = re.match(r'<DT><H3\s+(.*?)>(.*?)</H3>', line, re.IGNORECASE)
        if m:
            attrs_str, name = m.group(1), m.group(2)
            attrs = parse_attrs(attrs_str)
            add_date = attrs.get("ADD_DATE", "0")
            folder = Folder(name, add_date=add_date, attrs=attrs)
            folder_stack[-1].subfolders.append(folder)
            # Next line should be <DL><p>
            i += 1
            # Push folder onto stack
            folder_stack.append(folder)
            i += 1
            continue

        # Bookmark: <DT><A HREF="..." ...>Title</A>
        m = re.match(r'<DT><A\s+(.*?)>(.*?)</A>', line, re.IGNORECASE)
        if m:
            attrs_str, title = m.group(1), m.group(2)
            attrs = parse_attrs(attrs_str)
            href = attrs.get("HREF", "")
            add_date = attrs.get("ADD_DATE", "0")
            icon = attrs.get("ICON", "")
            bm = Bookmark(href=href, title=title, add_date=add_date, icon=icon, attrs=attrs)
            folder_stack[-1].bookmarks.append(bm)
            i += 1
            continue

        # End of folder: </DL><p>
        if re.match(r'</DL>', line, re.IGNORECASE):
            if len(folder_stack) > 1:
                folder_stack.pop()
            i += 1
            continue

        i += 1

    return root


def parse_attrs(attrs_str):
    """Parse HTML attributes from a string like 'HREF="..." ADD_DATE="..."'."""
    attrs = {}
    for m in re.finditer(r'(\w+)="([^"]*)"', attrs_str):
        attrs[m.group(1).upper()] = m.group(2)
    return attrs


def count_items(folder):
    """Count total bookmarks and folders recursively."""
    bm_count = len(folder.bookmarks)
    f_count = len(folder.subfolders)
    for sub in folder.subfolders:
        b, f = count_items(sub)
        bm_count += b
        f_count += f
    return bm_count, f_count


def flatten_folder(folder):
    """Return all bookmarks and subfolders from a folder, flattening it."""
    bookmarks = list(folder.bookmarks)
    subfolders = list(folder.subfolders)
    return bookmarks, subfolders


# Canonical name mapping (case-insensitive key -> canonical name)
CANONICAL_NAMES = {
    "social media": "Social Media",
    "businesstools": "BusinessTools",
    "business tools": "BusinessTools",
    "bowling": "Bowling",
    "datasciencetools": "DataScienceTools",
    "podcasts": "PodCasts",
    "apex": "apex",
    "drone sites": "Drone Sites",
}

CHROME_IMPORT_PATTERNS = [
    r"imported\s+from\s+(google\s+)?chrome",
    r"imported\s+from\s+chrome",
]

REMOVE_WRAPPER_NAMES = [
    "other bookmarks",
    "mobile bookmarks",
]

BOOKMARKS_BAR_NAMES = [
    "bookmarks bar",
    "favorites bar",
]


def is_chrome_import(name):
    for pat in CHROME_IMPORT_PATTERNS:
        if re.match(pat, name.strip(), re.IGNORECASE):
            return True
    return False


def is_remove_wrapper(name):
    return name.strip().lower() in REMOVE_WRAPPER_NAMES


def is_bookmarks_bar(name):
    return name.strip().lower() in BOOKMARKS_BAR_NAMES


def is_new_folder(name):
    return name.strip().lower() in ("new folder", "new folder (2)", "new folder (3)")


def canonical_name(name):
    key = name.strip().lower()
    return CANONICAL_NAMES.get(key, name.strip())


def merge_into_target(target, source_bookmarks, source_subfolders):
    """Merge bookmarks and subfolders from source into target folder."""
    target.bookmarks.extend(source_bookmarks)
    target.subfolders.extend(source_subfolders)


def unwrap_chrome_imports(folder):
    """Recursively unwrap 'Imported from Chrome' folders, merging their contents into parent."""
    new_subfolders = []
    extra_bookmarks = []
    extra_subfolders = []

    for sub in folder.subfolders:
        # First recurse
        unwrap_chrome_imports(sub)

        if is_chrome_import(sub.name):
            # Unwrap: merge contents into parent
            extra_bookmarks.extend(sub.bookmarks)
            extra_subfolders.extend(sub.subfolders)
        elif is_remove_wrapper(sub.name):
            # Unwrap Other bookmarks, Mobile bookmarks
            extra_bookmarks.extend(sub.bookmarks)
            extra_subfolders.extend(sub.subfolders)
        elif is_bookmarks_bar(sub.name) and any(is_bookmarks_bar(f.name) for f in [folder]):
            # If parent is also a bookmarks bar variant, merge
            extra_bookmarks.extend(sub.bookmarks)
            extra_subfolders.extend(sub.subfolders)
        elif is_new_folder(sub.name):
            # Merge "New folder" contents into parent
            extra_bookmarks.extend(sub.bookmarks)
            extra_subfolders.extend(sub.subfolders)
        else:
            new_subfolders.append(sub)

    folder.bookmarks.extend(extra_bookmarks)
    folder.subfolders = new_subfolders + extra_subfolders

    # Now also unwrap any Bookmarks bar duplicates inside a Favorites bar
    if is_bookmarks_bar(folder.name):
        new_subs2 = []
        for sub in folder.subfolders:
            if is_bookmarks_bar(sub.name):
                folder.bookmarks.extend(sub.bookmarks)
                new_subs2.extend(sub.subfolders)
            else:
                new_subs2.append(sub)
        folder.subfolders = new_subs2


def merge_duplicate_folders(folder):
    """Merge subfolders with the same name (case-insensitive) within each folder."""
    # Recurse first
    for sub in folder.subfolders:
        merge_duplicate_folders(sub)

    # Group subfolders by canonical name (case-insensitive)
    groups = defaultdict(list)
    for sub in folder.subfolders:
        key = canonical_name(sub.name).lower()
        groups[key].append(sub)

    merged = []
    seen_keys = set()
    for sub in folder.subfolders:
        key = canonical_name(sub.name).lower()
        if key in seen_keys:
            continue
        seen_keys.add(key)

        group = groups[key]
        if len(group) == 1:
            group[0].name = canonical_name(group[0].name)
            merged.append(group[0])
        else:
            # Merge all into the first one
            primary = group[0]
            primary.name = canonical_name(primary.name)
            for other in group[1:]:
                primary.bookmarks.extend(other.bookmarks)
                primary.subfolders.extend(other.subfolders)
            # Recurse on the merged folder to handle nested duplicates
            merge_duplicate_folders(primary)
            merged.append(primary)

    folder.subfolders = merged


def dedup_urls(folder, seen_urls=None):
    """
    Globally deduplicate URLs, keeping the bookmark with the most recent ADD_DATE.
    Two passes: first collect all bookmarks, then keep best and remove rest.
    """
    if seen_urls is None:
        seen_urls = {}

    # First pass: collect all bookmarks with their URLs to find best ADD_DATE
    all_bookmarks = []
    collect_all_bookmarks(folder, all_bookmarks)

    # Group by URL (case-sensitive for HREF)
    url_best = {}
    for bm in all_bookmarks:
        url = bm.href.strip()
        if not url:
            continue
        if url not in url_best or bm.add_date > url_best[url].add_date:
            url_best[url] = bm

    # Second pass: remove duplicates, keeping only the first occurrence that matches the best
    seen = set()
    remove_dup_bookmarks(folder, url_best, seen)


def collect_all_bookmarks(folder, result):
    for bm in folder.bookmarks:
        result.append(bm)
    for sub in folder.subfolders:
        collect_all_bookmarks(sub, result)


def remove_dup_bookmarks(folder, url_best, seen):
    """Remove duplicate bookmarks. Keep the one matching url_best (most recent ADD_DATE)."""
    new_bookmarks = []
    for bm in folder.bookmarks:
        url = bm.href.strip()
        if not url:
            new_bookmarks.append(bm)
            continue
        if url in seen:
            continue  # duplicate, skip
        # Keep this one only if it's the best (most recent ADD_DATE)
        best = url_best.get(url)
        if best and best.add_date == bm.add_date:
            seen.add(url)
            new_bookmarks.append(bm)
        elif url not in seen:
            # If we haven't seen it yet and it's not the best, still skip
            # But we need to handle the case where the best is elsewhere
            # Mark as seen but don't add here - the best version will be added elsewhere
            pass

    folder.bookmarks = new_bookmarks

    for sub in folder.subfolders:
        remove_dup_bookmarks(sub, url_best, seen)


def remove_empty_folders(folder):
    """Recursively remove empty folders."""
    for sub in folder.subfolders:
        remove_empty_folders(sub)

    folder.subfolders = [
        sub for sub in folder.subfolders
        if sub.bookmarks or sub.subfolders
    ]


def sort_contents(folder):
    """Sort folders alphabetically and bookmarks alphabetically by title within each folder."""
    folder.subfolders.sort(key=lambda f: f.name.lower())
    folder.bookmarks.sort(key=lambda b: b.title.lower())
    for sub in folder.subfolders:
        sort_contents(sub)


def strip_large_icons(folder):
    """Strip base64 ICON data that is excessively large (>2KB)."""
    for bm in folder.bookmarks:
        if bm.icon and len(bm.icon) > MAX_ICON_SIZE:
            bm.icon = ""
    for sub in folder.subfolders:
        strip_large_icons(sub)


def handle_special_folders(folder):
    """Handle Eve Gas and Tabs set aside > Group 1 per the rules."""
    # These will be handled by remove_empty_folders naturally
    pass


def handle_uncategorized(root):
    """
    After unwrapping Other/Mobile bookmarks, any bookmarks that ended up
    at root level without a folder should go into 'Uncategorized'.
    """
    # Find the main favorites bar
    fav_bar = None
    for sub in root.subfolders:
        if is_bookmarks_bar(sub.name):
            fav_bar = sub
            break

    if not fav_bar:
        return

    # Check if root has direct bookmarks (from unwrapped Other/Mobile)
    if root.bookmarks:
        # Try to find existing Uncategorized folder
        uncat = None
        for sub in fav_bar.subfolders:
            if sub.name.lower() == "uncategorized":
                uncat = sub
                break
        if not uncat:
            uncat = Folder("Uncategorized")
            fav_bar.subfolders.append(uncat)
        uncat.bookmarks.extend(root.bookmarks)
        root.bookmarks = []

    # Also move any root-level subfolders that aren't the favorites bar
    extra = []
    keep = []
    for sub in root.subfolders:
        if is_bookmarks_bar(sub.name):
            keep.append(sub)
        else:
            extra.append(sub)
    if extra and fav_bar:
        for ex in extra:
            # Try to merge into existing folder by name
            matched = False
            for fsub in fav_bar.subfolders:
                if fsub.name.lower() == ex.name.lower():
                    fsub.bookmarks.extend(ex.bookmarks)
                    fsub.subfolders.extend(ex.subfolders)
                    matched = True
                    break
            if not matched:
                fav_bar.subfolders.append(ex)
        root.subfolders = keep


def escape_html(text):
    """Escape HTML special characters in text."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def write_bookmarks(folder, filepath):
    """Write the cleaned bookmark tree as a Netscape Bookmark HTML file."""
    lines = []
    lines.append("<!DOCTYPE NETSCAPE-Bookmark-file-1>")
    lines.append("<!-- This is an automatically generated file.")
    lines.append("     It will be read and overwritten.")
    lines.append("     DO NOT EDIT! -->")
    lines.append('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">')
    lines.append("<TITLE>Bookmarks</TITLE>")
    lines.append("<H1>Bookmarks</H1>")
    lines.append("<DL><p>")

    # Write the root's subfolders (should be just Favorites bar)
    for sub in folder.subfolders:
        write_folder(sub, lines, indent=1)

    # Write any root-level bookmarks
    for bm in folder.bookmarks:
        write_bookmark(bm, lines, indent=1)

    lines.append("</DL><p>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_folder(folder, lines, indent):
    prefix = "    " * indent
    # Build H3 attributes
    attrs_parts = []
    if folder.add_date:
        attrs_parts.append(f'ADD_DATE="{folder.add_date}"')
    if "LAST_MODIFIED" in folder.attrs:
        attrs_parts.append(f'LAST_MODIFIED="{folder.attrs["LAST_MODIFIED"]}"')
    if "PERSONAL_TOOLBAR_FOLDER" in folder.attrs:
        attrs_parts.append(f'PERSONAL_TOOLBAR_FOLDER="{folder.attrs["PERSONAL_TOOLBAR_FOLDER"]}"')

    attrs_str = " ".join(attrs_parts)
    if attrs_str:
        attrs_str = " " + attrs_str

    lines.append(f"{prefix}<DT><H3{attrs_str}>{folder.name}</H3>")
    lines.append(f"{prefix}<DL><p>")

    # Write subfolders first (sorted)
    for sub in folder.subfolders:
        write_folder(sub, lines, indent + 1)

    # Write bookmarks (sorted)
    for bm in folder.bookmarks:
        write_bookmark(bm, lines, indent + 1)

    lines.append(f"{prefix}</DL><p>")


def write_bookmark(bm, lines, indent):
    prefix = "    " * indent
    attrs_parts = []
    attrs_parts.append(f'HREF="{bm.href}"')
    if bm.add_date:
        attrs_parts.append(f'ADD_DATE="{bm.add_date}"')
    if bm.icon:
        attrs_parts.append(f'ICON="{bm.icon}"')

    attrs_str = " ".join(attrs_parts)
    lines.append(f"{prefix}<DT><A {attrs_str}>{bm.title}</A>")


def count_unique_urls(folder):
    urls = set()
    _collect_urls(folder, urls)
    return len(urls)


def _collect_urls(folder, urls):
    for bm in folder.bookmarks:
        if bm.href.strip():
            urls.add(bm.href.strip())
    for sub in folder.subfolders:
        _collect_urls(sub, urls)


def validate_output(filepath):
    """Validate the output has balanced DL tags."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    open_dl = len(re.findall(r"<DL>", content, re.IGNORECASE))
    close_dl = len(re.findall(r"</DL>", content, re.IGNORECASE))

    if open_dl == close_dl:
        print(f"VALID: {open_dl} opening <DL> tags match {close_dl} closing </DL> tags")
    else:
        print(f"ERROR: {open_dl} opening <DL> tags != {close_dl} closing </DL> tags")

    return open_dl == close_dl


def main():
    print("Parsing input file...")
    root = parse_bookmarks(INPUT_FILE)

    bm_before, f_before = count_items(root)
    print(f"\nBEFORE cleaning:")
    print(f"  Bookmarks: {bm_before}")
    print(f"  Folders:   {f_before}")
    print(f"  Unique URLs: {count_unique_urls(root)}")

    print("\nStep 1: Unwrapping Chrome imports, Other/Mobile bookmarks, New folders...")
    unwrap_chrome_imports(root)

    print("Step 2: Handling root-level uncategorized bookmarks...")
    handle_uncategorized(root)

    print("Step 3: Merging duplicate folders...")
    merge_duplicate_folders(root)

    print("Step 4: Deduplicating URLs globally (keeping most recent ADD_DATE)...")
    dedup_urls(root)

    print("Step 5: Stripping large icons (>2KB)...")
    strip_large_icons(root)

    print("Step 6: Removing empty folders...")
    remove_empty_folders(root)

    print("Step 7: Sorting contents alphabetically...")
    sort_contents(root)

    bm_after, f_after = count_items(root)
    unique_after = count_unique_urls(root)
    print(f"\nAFTER cleaning:")
    print(f"  Bookmarks: {bm_after}")
    print(f"  Folders:   {f_after}")
    print(f"  Unique URLs: {unique_after}")
    print(f"\nSUMMARY:")
    print(f"  Folders: {f_before} -> {f_after} (removed {f_before - f_after})")
    print(f"  Bookmarks: {bm_before} -> {bm_after} (removed {bm_before - bm_after})")
    print(f"  Duplicates removed: {bm_before - bm_after}")

    print(f"\nWriting cleaned file to: {OUTPUT_FILE}")
    write_bookmarks(root, OUTPUT_FILE)

    print("\nValidating output...")
    valid = validate_output(OUTPUT_FILE)

    print(f"Unique bookmark count in output: {unique_after}")

    if valid:
        print("\nDone! Cleaned bookmark file is valid.")
    else:
        print("\nWARNING: Output file has unbalanced DL tags!")

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
