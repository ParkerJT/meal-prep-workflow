"""Sanitization and length limits for user-authored text fields."""

from __future__ import annotations

import re
import unicodedata

RECIPE_TEXT_MAX_CHARS = 50_000
PERSONAL_INSTRUCTIONS_MAX_CHARS = 500
GLOBAL_INSTRUCTIONS_MAX_CHARS = 1_000

_DISALLOWED_CONTROL_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def sanitize_user_text(
    value: str,
    *,
    max_chars: int,
    field_name: str,
    required: bool = False,
) -> str:
    """
    Normalize and validate user-authored text before LLM or persistence use.

    Raises ValueError with a user-facing message when validation fails.
    """
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required.")
        return ""

    normalized = unicodedata.normalize("NFKC", value)
    cleaned = _DISALLOWED_CONTROL_RE.sub("", normalized).strip()

    if required and not cleaned:
        raise ValueError(f"{field_name} is required.")
    if not cleaned:
        return ""

    if len(cleaned) > max_chars:
        raise ValueError(
            f"{field_name} exceeds the maximum length of {max_chars} characters."
        )

    return cleaned
