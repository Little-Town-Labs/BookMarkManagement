"""Tests for the CLI interface."""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookmark_cleaner.cli import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"


class TestCleanCommand:
    def test_clean_simple_file(self, tmp_path: Path) -> None:
        out = tmp_path / "cleaned.html"
        result = runner.invoke(app, ["clean", str(FIXTURES / "sample_simple.html"), "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "NETSCAPE-Bookmark-file-1" in content

    def test_clean_default_output_name(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Copy fixture to tmp_path so default output goes there
        src = FIXTURES / "sample_simple.html"
        dest = tmp_path / "bookmarks.html"
        dest.write_text(src.read_text())
        result = runner.invoke(app, ["clean", str(dest)])
        assert result.exit_code == 0
        expected = tmp_path / "bookmarks_cleaned.html"
        assert expected.exists()

    def test_clean_dry_run(self) -> None:
        result = runner.invoke(app, ["clean", str(FIXTURES / "sample_simple.html"), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run" in result.output or "dry run" in result.output or "changes" in result.output.lower()

    def test_clean_nonexistent_file(self) -> None:
        result = runner.invoke(app, ["clean", "/nonexistent/file.html"])
        assert result.exit_code != 0

    def test_clean_not_a_bookmark_file(self) -> None:
        result = runner.invoke(app, ["clean", str(FIXTURES / "sample_not_bookmarks.json")])
        assert result.exit_code != 0

    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_clean_real_file(self, tmp_path: Path) -> None:
        out = tmp_path / "cleaned.html"
        result = runner.invoke(app, ["clean", "favorites_3_17_26.html", "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        # Verify cleaned file is parseable and has fewer bookmarks
        from bookmark_cleaner.parsers.netscape import parse_netscape
        from bookmark_cleaner.tree import collect_bookmarks

        tree = parse_netscape(str(out))
        bms = collect_bookmarks(tree.root)
        assert len(bms) < 2503
        assert len(bms) >= 960  # ~970 unique, normalization may merge a few http/https variants


class TestInfoCommand:
    def test_info_simple_file(self) -> None:
        result = runner.invoke(app, ["info", str(FIXTURES / "sample_simple.html")])
        assert result.exit_code == 0
        assert "5" in result.output  # 5 bookmarks

    def test_info_nonexistent_file(self) -> None:
        result = runner.invoke(app, ["info", "/nonexistent/file.html"])
        assert result.exit_code != 0

    @pytest.mark.skipif(
        not Path("favorites_3_17_26.html").exists(),
        reason="Real bookmark file not available",
    )
    def test_info_real_file(self) -> None:
        result = runner.invoke(app, ["info", "favorites_3_17_26.html"])
        assert result.exit_code == 0
        assert "2503" in result.output or "2,503" in result.output


class TestVersion:
    def test_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
