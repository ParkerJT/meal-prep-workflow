"""Deterministic recipe_id from source URL (BUILD_PLAN: sha256 of normalized URL, first 32 hex chars)."""

from __future__ import annotations

import hashlib
import uuid
from urllib.parse import urlsplit, urlunsplit

TEXT_SOURCE_SCHEME = "text"


def normalize_source_url(url: str) -> str:
    """
    Stable normalization for deduplication. Changing this function changes recipe_id values.
    - Strips surrounding whitespace
    - Lowercases scheme and host
    - Drops default ports (:443 for https, :80 for http)
    - Removes empty fragment
    - Strips a single trailing slash from path (except root "/")
    """
    s = url.strip()
    if not s:
        raise ValueError("source_url is empty")

    parts = urlsplit(s)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()

    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    elif netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    return urlunsplit((scheme, netloc, path, parts.query, ""))


def compute_recipe_id(normalized_url: str) -> str:
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:32]


def normalize_source_key(key: str) -> str:
    """
    Normalize a source key for persistence.

    Synthetic pasted-text keys use ``text://{uuid}`` and are validated but not
    URL-normalized like HTTPS sources.
    """
    s = key.strip()
    if not s:
        raise ValueError("source_url is empty")

    parts = urlsplit(s)
    if parts.scheme.lower() == TEXT_SOURCE_SCHEME:
        raw_id = (parts.netloc or parts.path.lstrip("/")).lower()
        try:
            parsed = uuid.UUID(raw_id)
        except ValueError as exc:
            raise ValueError(f"Invalid text source key: {key}") from exc
        return f"{TEXT_SOURCE_SCHEME}://{parsed}"

    return normalize_source_url(s)
