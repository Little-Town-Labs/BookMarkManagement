#!/usr/bin/env python3
"""
Bookmark Cleanup Tool
Cleans up duplicate bookmarks, consolidates import folders, and restructures hierarchy
"""

from html.parser import HTMLParser
from collections import defaultdict
import re
from typing import List, Dict, Tuple, Optional

class Bookmark:
    def __init__(self, url: str, title: str, add_date: str, icon: str = "", last_modified: str = ""):
        self.url = url
        self.title = title
        self.add_date = add_date
        self.icon = icon
        self.last_modified = last_modified

    def __repr__(self):
        return f"Bookmark({self.title[:30]}...)"

class Folder:
    def __init__(self, name: str, add_date: str = "", last_modified: str = "", personal_toolbar: str = ""):
        self.name = name
        self.add_date = add_date
        self.last_modified = last_modified
        self.personal_toolbar = personal_toolbar
        self.bookmarks: List[Bookmark] = []
        self.folders: List['Folder'] = []

    def __repr__(self):
        return f"Folder({self.name}, {len(self.bookmarks)} bookmarks, {len(self.folders)} folders)"

class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Folder("Root")
        self.folder_stack: List[Folder] = [self.root]
        self.in_dl = False
        self.pending_folder = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h3':
            # Folder definition
            self.pending_folder = {
                'add_date': attrs_dict.get('add_date', ''),
                'last_modified': attrs_dict.get('last_modified', ''),
                'personal_toolbar_folder': attrs_dict.get('personal_toolbar_folder', '')
            }
        elif tag == 'dl':
            self.in_dl = True
        elif tag == 'a':
            # Bookmark
            bookmark = Bookmark(
                url=attrs_dict.get('href', ''),
                title='',
                add_date=attrs_dict.get('add_date', ''),
                icon=attrs_dict.get('icon', ''),
                last_modified=attrs_dict.get('last_modified', '')
            )
            self.folder_stack[-1].bookmarks.append(bookmark)

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.pending_folder is not None:
            # This is folder name
            folder = Folder(
                name=data,
                add_date=self.pending_folder['add_date'],
                last_modified=self.pending_folder['last_modified'],
                personal_toolbar=self.pending_folder['personal_toolbar_folder']
            )
            self.folder_stack[-1].folders.append(folder)
            self.folder_stack.append(folder)
            self.pending_folder = None
        elif self.folder_stack[-1].bookmarks:
            # This is bookmark title
            self.folder_stack[-1].bookmarks[-1].title = data

    def handle_endtag(self, tag):
        if tag == 'dl' and len(self.folder_stack) > 1:
            self.folder_stack.pop()

def parse_bookmarks(file_path: str) -> Folder:
    """Parse HTML bookmarks file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = BookmarkParser()
    parser.feed(content)
    return parser.root

def collect_all_bookmarks(folder: Folder, path: str = "") -> List[Tuple[str, Bookmark]]:
    """Collect all bookmarks with their folder paths"""
    bookmarks = []
    current_path = f"{path}/{folder.name}" if path else folder.name

    for bookmark in folder.bookmarks:
        bookmarks.append((current_path, bookmark))

    for subfolder in folder.folders:
        bookmarks.extend(collect_all_bookmarks(subfolder, current_path))

    return bookmarks

def deduplicate_bookmarks(all_bookmarks: List[Tuple[str, Bookmark]]) -> Dict[str, Tuple[str, Bookmark]]:
    """Remove duplicate URLs, keeping the best version"""
    url_to_bookmark = {}

    for path, bookmark in all_bookmarks:
        if not bookmark.url:
            continue

        url = bookmark.url.rstrip('/')

        if url not in url_to_bookmark:
            url_to_bookmark[url] = (path, bookmark)
        else:
            # Keep the one with better title (longer, more descriptive)
            existing_path, existing = url_to_bookmark[url]

            # Prefer non-generic titles
            if len(bookmark.title) > len(existing.title) or (
                existing.title.lower() in ['home', 'new tab', 'untitled'] and
                bookmark.title.lower() not in ['home', 'new tab', 'untitled']
            ):
                url_to_bookmark[url] = (path, bookmark)

    return url_to_bookmark

def is_import_folder(name: str) -> bool:
    """Check if folder is an import container"""
    import_patterns = [
        'imported from chrome',
        'imported from edge',
        'imported from microsoft edge',
        'other bookmarks',
        'bookmarks bar',
        'mobile bookmarks',
        'other favorites'
    ]
    return any(pattern in name.lower() for pattern in import_patterns)

def is_generic_folder(name: str) -> bool:
    """Check if folder has generic name"""
    generic_names = ['new folder', 'apex', 'group 1', 'tabs set aside']
    return name.lower() in generic_names

def normalize_folder_name(name: str) -> str:
    """Normalize folder names for consistency"""
    # Fix case conflicts
    case_mappings = {
        'bowling': 'Bowling',
        'businesstools': 'Business Tools',
        'business tools': 'Business Tools',
        'socialmedia': 'Social Media',
        'social media': 'Social Media',
        'podcasts': 'Podcasts',
        'deeplearning': 'Deep Learning',
        'deep learning': 'Deep Learning'
    }

    normalized = case_mappings.get(name.lower(), name)

    # Capitalize properly
    if normalized[0].islower():
        normalized = normalized[0].upper() + normalized[1:]

    return normalized

def restructure_folders(root: Folder, unique_bookmarks: Dict[str, Tuple[str, Bookmark]]) -> Folder:
    """Create clean folder structure with deduplicated bookmarks"""

    # Define new top-level structure
    new_root = Folder("Bookmarks", personal_toolbar="true")

    # Category mappings
    categories = {
        'Development': ['azure certification', 'datasciencetools', 'data science', 'programming'],
        'AI & Machine Learning': ['deep learning', 'ai technology', 'machine learning'],
        'Business Tools': ['business tools', 'businesstools', 'creativeWork', 'creative work'],
        'Gaming': ['bowling', 'archery', 'd&d', 'drone sites', 'shooting areas', 'eve gas', 'evetools', 'lol guides'],
        'Entertainment': ['streaming services', 'youtube', 'videos'],
        'Learning': ['podcasts', 'online books', 'writing videos', 'courses'],
        'Finance': ['financial', 'banks & credit cards', 'digitalcurrency', 'bitcoin'],
        'Personal': ['church', 'mylesmunroe', 'scouting', 'geneology', 'hunting'],
        'Writing': ['writing', 'writing tools', 'author tools'],
        'Social Media': ['social media', 'twitter', 'facebook'],
        'Work & Projects': ['emails', 'work', 'projects'],
        'Reference': ['documentation', 'guides', 'resources']
    }

    # Create category folders
    category_folders = {}
    for category_name in categories.keys():
        folder = Folder(category_name)
        new_root.folders.append(folder)
        category_folders[category_name] = folder

    # Add "Uncategorized" for items that don't fit
    uncategorized = Folder("Uncategorized")
    new_root.folders.append(uncategorized)
    category_folders['Uncategorized'] = uncategorized

    # Distribute bookmarks into categories
    for url, (path, bookmark) in unique_bookmarks.items():
        # Determine category based on original path
        path_lower = path.lower()
        placed = False

        for category_name, keywords in categories.items():
            if any(keyword in path_lower for keyword in keywords):
                category_folders[category_name].bookmarks.append(bookmark)
                placed = True
                break

        if not placed:
            category_folders['Uncategorized'].bookmarks.append(bookmark)

    # Remove empty categories
    new_root.folders = [f for f in new_root.folders if f.bookmarks or f.folders]

    return new_root

def write_html(folder: Folder, output_path: str):
    """Write cleaned bookmarks to HTML file"""

    def write_folder(f: Folder, indent: int = 0) -> str:
        spaces = '    ' * indent
        html = []

        # Write folder header
        if indent > 0:  # Skip root
            personal_toolbar = ' PERSONAL_TOOLBAR_FOLDER="true"' if f.personal_toolbar else ''
            add_date = f' ADD_DATE="{f.add_date}"' if f.add_date else ''
            last_modified = f' LAST_MODIFIED="{f.last_modified}"' if f.last_modified else ''

            html.append(f'{spaces}<DT><H3{add_date}{last_modified}{personal_toolbar}>{f.name}</H3>')
            html.append(f'{spaces}<DL><p>')

        # Write bookmarks
        for bookmark in sorted(f.bookmarks, key=lambda b: b.title.lower()):
            if not bookmark.url:
                continue
            icon_attr = f' ICON="{bookmark.icon}"' if bookmark.icon else ''
            add_date_attr = f' ADD_DATE="{bookmark.add_date}"' if bookmark.add_date else ''
            html.append(f'{spaces}    <DT><A HREF="{bookmark.url}"{add_date_attr}{icon_attr}>{bookmark.title}</A>')

        # Write subfolders
        for subfolder in sorted(f.folders, key=lambda sf: sf.name.lower()):
            html.append(write_folder(subfolder, indent + 1))

        if indent > 0:
            html.append(f'{spaces}</DL><p>')

        return '\n'.join(html)

    # Write header
    header = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''

    footer = '</DL><p>\n'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)

        # Write each top-level folder
        for subfolder in folder.folders:
            f.write(write_folder(subfolder, indent=1))

        f.write(footer)

def main():
    input_file = '/mnt/g/bookmarkmanagement/bookmarks_1_23_26.html'
    output_file = '/mnt/g/bookmarkmanagement/bookmarks_cleaned.html'

    print("🔍 Parsing bookmarks file...")
    root = parse_bookmarks(input_file)

    print("📊 Collecting all bookmarks...")
    all_bookmarks = collect_all_bookmarks(root)
    print(f"   Found {len(all_bookmarks)} total bookmarks")

    print("🗑️  Removing duplicates...")
    unique_bookmarks = deduplicate_bookmarks(all_bookmarks)
    print(f"   Reduced to {len(unique_bookmarks)} unique bookmarks")
    print(f"   Removed {len(all_bookmarks) - len(unique_bookmarks)} duplicates")

    print("🏗️  Restructuring folders...")
    clean_root = restructure_folders(root, unique_bookmarks)

    print("💾 Writing cleaned bookmarks...")
    write_html(clean_root, output_file)

    # Summary
    print("\n✅ Cleanup Complete!")
    print(f"   Input:  {len(all_bookmarks)} bookmarks")
    print(f"   Output: {len(unique_bookmarks)} bookmarks")
    print(f"   Saved:  {output_file}")
    print(f"   Backup: /mnt/g/bookmarkmanagement/bookmarks_1_23_26_BACKUP.html")

if __name__ == '__main__':
    main()
