"""CLI interface for bookmark-cleaner."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from bookmark_cleaner.operations import run_pipeline
from bookmark_cleaner.parsers import detect_format
from bookmark_cleaner.parsers.netscape import export_netscape, parse_netscape
from bookmark_cleaner.tree import collect_bookmarks, collect_urls, count_items, folder_paths

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="bookmark-cleaner",
    help="Clean, deduplicate, and organize browser bookmark files.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        console.print("bookmark-cleaner 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit.", callback=version_callback, is_eager=True
    ),
) -> None:
    """bookmark-cleaner: Clean, deduplicate, and organize browser bookmark files."""


@app.command()
def clean(
    file: Path = typer.Argument(..., help="Bookmark file to clean.", exists=True),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path."),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview changes without writing."),
    strategy: str = typer.Option("newest", "--strategy", "-s", help="Dedup strategy: newest, oldest, longest_title."),
) -> None:
    """Clean a bookmark file: deduplicate, merge folders, remove empties, sort."""
    fmt = detect_format(str(file))
    if fmt != "netscape":
        err_console.print(f"[red]Error:[/red] '{file}' is not a supported bookmark file.")
        raise typer.Exit(code=1)

    tree = parse_netscape(str(file))
    before_bm = len(collect_bookmarks(tree.root))
    before_urls = len(collect_urls(tree.root))
    _, before_folders = count_items(tree.root)

    result = run_pipeline(tree, strategy=strategy)
    after_bm = len(collect_bookmarks(result.tree.root))
    after_urls = len(collect_urls(result.tree.root))
    _, after_folders = count_items(result.tree.root)

    # Summary table
    table = Table(title="Cleanup Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("Removed", justify="right", style="green")
    table.add_row("Bookmarks", str(before_bm), str(after_bm), str(before_bm - after_bm))
    table.add_row("Unique URLs", str(before_urls), str(after_urls), "")
    table.add_row("Folders", str(before_folders), str(after_folders), str(before_folders - after_folders))
    table.add_row("Changes", "", "", str(len(result.changes)))
    console.print(table)

    if dry_run:
        console.print(f"\n[bold]Dry run[/bold] — {len(result.changes)} changes would be applied:")
        for change in result.changes[:20]:
            console.print(f"  [{change.op}] {change.description}")
        if len(result.changes) > 20:
            console.print(f"  ... and {len(result.changes) - 20} more")
        console.print("\nNo files written. Run without --dry-run to apply.")
        return

    # Determine output path
    if output is None:
        output = file.parent / f"{file.stem}_cleaned{file.suffix}"

    export_netscape(result.tree, str(output))
    console.print(f"\n[green]Cleaned file written to:[/green] {output}")


@app.command()
def info(
    file: Path = typer.Argument(..., help="Bookmark file to analyze.", exists=True),
) -> None:
    """Display bookmark file statistics."""
    fmt = detect_format(str(file))
    if fmt != "netscape":
        err_console.print(f"[red]Error:[/red] '{file}' is not a supported bookmark file.")
        raise typer.Exit(code=1)

    tree = parse_netscape(str(file))
    all_bm = collect_bookmarks(tree.root)
    urls = collect_urls(tree.root)
    bm_count, folder_count = count_items(tree.root)
    paths = folder_paths(tree.root)

    table = Table(title=f"Bookmark Info: {file.name}")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Format", "Netscape HTML")
    table.add_row("Total bookmarks", str(bm_count))
    table.add_row("Unique URLs", str(len(urls)))
    table.add_row("Duplicates", str(bm_count - len(urls)))
    table.add_row("Folders", str(folder_count))
    console.print(table)

    if paths:
        console.print("\n[bold]Folder tree:[/bold]")
        for path in paths[:30]:
            depth = path.count(" > ")
            name = path.split(" > ")[-1]
            console.print(f"  {'  ' * depth}{name}")
        if len(paths) > 30:
            console.print(f"  ... and {len(paths) - 30} more folders")
