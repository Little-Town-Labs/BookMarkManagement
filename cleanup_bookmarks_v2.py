#!/usr/bin/env python3
"""
Bookmark Cleanup Tool v2 - Fixed HTML structure
"""

from html.parser import HTMLParser
from collections import defaultdict
import re

class Bookmark:
    def __init__(self, url: str, title: str, add_date: str, icon: str = ""):
        self.url = url
        self.title = title
        self.add_date = add_date
        self.icon = icon

class Folder:
    def __init__(self, name: str):
        self.name = name
        self.bookmarks = []
        self.subfolders = []

class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = Folder("Root")
        self.folder_stack = [self.root]
        self.pending_folder_name = None
        self.current_bookmark = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h3':
            self.pending_folder_name = ''
        elif tag == 'dl':
            pass
        elif tag == 'a':
            self.current_bookmark = Bookmark(
                url=attrs_dict.get('href', ''),
                title='',
                add_date=attrs_dict.get('add_date', ''),
                icon=attrs_dict.get('icon', '')
            )

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.pending_folder_name is not None:
            self.pending_folder_name = data
        elif self.current_bookmark:
            self.current_bookmark.title = data

    def handle_endtag(self, tag):
        if tag == 'h3' and self.pending_folder_name:
            folder = Folder(self.pending_folder_name)
            self.folder_stack[-1].subfolders.append(folder)
            self.folder_stack.append(folder)
            self.pending_folder_name = None
        elif tag == 'a' and self.current_bookmark:
            if self.current_bookmark.url:
                self.folder_stack[-1].bookmarks.append(self.current_bookmark)
            self.current_bookmark = None
        elif tag == 'dl' and len(self.folder_stack) > 1:
            self.folder_stack.pop()

def parse_bookmarks(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    parser = BookmarkParser()
    parser.feed(content)
    return parser.root

def collect_all_bookmarks(folder, path=""):
    bookmarks = []
    current_path = f"{path}/{folder.name}" if path else folder.name

    for bookmark in folder.bookmarks:
        bookmarks.append((current_path, bookmark))

    for subfolder in folder.subfolders:
        bookmarks.extend(collect_all_bookmarks(subfolder, current_path))

    return bookmarks

def deduplicate_bookmarks(all_bookmarks):
    url_to_bookmark = {}

    for path, bookmark in all_bookmarks:
        if not bookmark.url:
            continue

        url = bookmark.url.rstrip('/')

        if url not in url_to_bookmark:
            url_to_bookmark[url] = (path, bookmark)
        else:
            existing_path, existing = url_to_bookmark[url]
            # Keep the one with better title
            if len(bookmark.title) > len(existing.title):
                url_to_bookmark[url] = (path, bookmark)

    return url_to_bookmark

def categorize_bookmarks(unique_bookmarks):
    # Define categories and their keywords
    categories = {
        'Development': {
            'keywords': ['azure', 'certification', 'programming', 'code', 'developer', 'github', 'api', 'database'],
            'bookmarks': []
        },
        'AI & Machine Learning': {
            'keywords': ['ai', 'machine learning', 'deep learning', 'neural', 'gpt', 'openai', 'claude', 'chatbot'],
            'bookmarks': []
        },
        'Business Tools': {
            'keywords': ['business', 'tool', 'productivity', 'saas', 'crm', 'project'],
            'bookmarks': []
        },
        'Gaming': {
            'keywords': ['bowling', 'archery', 'game', 'eve', 'lol', 'drone', 'shooting', 'd&d'],
            'bookmarks': []
        },
        'Entertainment': {
            'keywords': ['youtube', 'video', 'stream', 'twitch', 'movie', 'tv'],
            'bookmarks': []
        },
        'Learning': {
            'keywords': ['learn', 'course', 'tutorial', 'podcast', 'education', 'training', 'book'],
            'bookmarks': []
        },
        'Finance': {
            'keywords': ['bank', 'finance', 'bitcoin', 'crypto', 'currency', 'money', 'invest'],
            'bookmarks': []
        },
        'Personal': {
            'keywords': ['church', 'genealogy', 'family', 'hunting', 'scout'],
            'bookmarks': []
        },
        'Writing': {
            'keywords': ['writing', 'author', 'blog', 'publish', 'edit'],
            'bookmarks': []
        },
        'Social Media': {
            'keywords': ['social', 'twitter', 'facebook', 'linkedin', 'instagram'],
            'bookmarks': []
        },
        'Uncategorized': {
            'keywords': [],
            'bookmarks': []
        }
    }

    for url, (path, bookmark) in unique_bookmarks.items():
        path_lower = path.lower()
        title_lower = bookmark.title.lower()
        url_lower = url.lower()
        combined = f"{path_lower} {title_lower} {url_lower}"

        placed = False
        for category_name, category_data in categories.items():
            if category_name == 'Uncategorized':
                continue
            if any(keyword in combined for keyword in category_data['keywords']):
                category_data['bookmarks'].append(bookmark)
                placed = True
                break

        if not placed:
            categories['Uncategorized']['bookmarks'].append(bookmark)

    return categories

def write_html(categories, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
        f.write('<!-- This is an automatically generated file.\n')
        f.write('     It will be read and overwritten.\n')
        f.write('     DO NOT EDIT! -->\n')
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write('<TITLE>Bookmarks</TITLE>\n')
        f.write('<H1>Bookmarks</H1>\n')
        f.write('<DL><p>\n')

        # Write main "Bookmarks" folder (bookmarks bar)
        f.write('    <DT><H3 ADD_DATE="1682599650" LAST_MODIFIED="1769180566" PERSONAL_TOOLBAR_FOLDER="true">Bookmarks</H3>\n')
        f.write('    <DL><p>\n')

        # Write each category
        for category_name in ['Development', 'AI & Machine Learning', 'Business Tools',
                             'Gaming', 'Entertainment', 'Learning', 'Finance',
                             'Personal', 'Writing', 'Social Media', 'Uncategorized']:

            category_data = categories[category_name]
            bookmarks = category_data['bookmarks']

            if not bookmarks:
                continue

            # Write category folder
            f.write(f'        <DT><H3 ADD_DATE="1682599695" LAST_MODIFIED="0">{category_name}</H3>\n')
            f.write('        <DL><p>\n')

            # Write bookmarks (sorted by title)
            for bookmark in sorted(bookmarks, key=lambda b: b.title.lower()):
                icon_attr = f' ICON="{bookmark.icon}"' if bookmark.icon else ''
                add_date_attr = f' ADD_DATE="{bookmark.add_date}"' if bookmark.add_date else ''

                # Escape HTML entities in title
                title = bookmark.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                f.write(f'            <DT><A HREF="{bookmark.url}"{add_date_attr}{icon_attr}>{title}</A>\n')

            # Close category folder
            f.write('        </DL><p>\n')

        # Close main Bookmarks folder
        f.write('    </DL><p>\n')

        # Close root
        f.write('</DL><p>\n')

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

    print("📁 Categorizing bookmarks...")
    categories = categorize_bookmarks(unique_bookmarks)

    # Print category summary
    for category_name, category_data in categories.items():
        count = len(category_data['bookmarks'])
        if count > 0:
            print(f"   {category_name}: {count} bookmarks")

    print("💾 Writing cleaned bookmarks...")
    write_html(categories, output_file)

    print("\n✅ Cleanup Complete!")
    print(f"   Input:  {len(all_bookmarks)} bookmarks")
    print(f"   Output: {len(unique_bookmarks)} unique bookmarks")
    print(f"   File:   {output_file}")

if __name__ == '__main__':
    main()
