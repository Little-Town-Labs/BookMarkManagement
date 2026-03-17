"""URL normalization for deduplication."""
from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication comparison.

    Rules:
    - Lowercase scheme and hostname
    - Upgrade http to https
    - Strip default ports (80 for http, 443 for https)
    - Strip trailing slash from path
    - Sort query parameters alphabetically
    - Preserve fragments, auth info, and path case

    Returns the URL as-is if it cannot be parsed.
    """
    if not url:
        return url

    try:
        parsed = urlparse(url)
    except ValueError:
        return url

    # Only normalize http/https URLs
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return url

    # Upgrade http to https
    scheme = "https"

    # Lowercase hostname
    hostname = (parsed.hostname or "").lower()

    # Strip default ports
    port = parsed.port
    if port in (80, 443, None):
        netloc = hostname
    else:
        netloc = f"{hostname}:{port}"

    # Preserve userinfo if present
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        netloc = f"{userinfo}@{netloc}"

    # Strip trailing slash from path (but keep root as empty)
    path = parsed.path.rstrip("/")

    # Sort query parameters
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        sorted_query = urlencode(sorted(params.items()), doseq=True)
    else:
        sorted_query = ""

    return urlunparse((scheme, netloc, path, "", sorted_query, parsed.fragment))
