"""Tests for URL normalization."""
from __future__ import annotations

from bookmark_cleaner.normalize import normalize_url


class TestNormalizeUrl:
    def test_scheme_upgrade_http_to_https(self) -> None:
        assert normalize_url("http://example.com/path") == "https://example.com/path"

    def test_host_lowercase(self) -> None:
        assert normalize_url("https://Example.COM/path") == "https://example.com/path"

    def test_trailing_slash_stripped(self) -> None:
        assert normalize_url("https://example.com/path/") == "https://example.com/path"

    def test_query_params_sorted(self) -> None:
        assert (
            normalize_url("https://example.com/path?b=2&a=1")
            == "https://example.com/path?a=1&b=2"
        )

    def test_default_port_80_stripped(self) -> None:
        assert normalize_url("http://example.com:80/path") == "https://example.com/path"

    def test_default_port_443_stripped(self) -> None:
        assert normalize_url("https://example.com:443/path") == "https://example.com/path"

    def test_non_default_port_kept(self) -> None:
        assert (
            normalize_url("https://example.com:8080/path")
            == "https://example.com:8080/path"
        )

    def test_fragment_preserved(self) -> None:
        assert (
            normalize_url("https://example.com/path#section")
            == "https://example.com/path#section"
        )

    def test_no_trailing_slash_added(self) -> None:
        assert normalize_url("https://example.com") == "https://example.com"

    def test_unparseable_returned_as_is(self) -> None:
        assert normalize_url("not-a-url") == "not-a-url"

    def test_ftp_scheme_untouched(self) -> None:
        assert normalize_url("ftp://files.example.com/doc") == "ftp://files.example.com/doc"

    def test_path_case_preserved(self) -> None:
        assert normalize_url("HTTPS://EXAMPLE.COM/Path") == "https://example.com/Path"

    def test_equivalent_urls_normalize_equal(self) -> None:
        url_a = "http://Example.COM/path/"
        url_b = "https://example.com/path"
        assert normalize_url(url_a) == normalize_url(url_b)

    def test_empty_string(self) -> None:
        assert normalize_url("") == ""

    def test_root_path_trailing_slash(self) -> None:
        assert normalize_url("https://example.com/") == "https://example.com"
