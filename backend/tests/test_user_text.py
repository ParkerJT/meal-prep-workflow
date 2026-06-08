import pytest

from app.services.user_text import (
    PERSONAL_INSTRUCTIONS_MAX_CHARS,
    RECIPE_TEXT_MAX_CHARS,
    sanitize_user_text,
)


def test_sanitize_strips_disallowed_control_characters():
    out = sanitize_user_text(
        "Line one\x00\x07\nLine two",
        max_chars=RECIPE_TEXT_MAX_CHARS,
        field_name="recipe_text",
    )
    assert out == "Line one\nLine two"


def test_sanitize_nfkc_normalization():
    out = sanitize_user_text(
        "caf\u00e9",
        max_chars=RECIPE_TEXT_MAX_CHARS,
        field_name="recipe_text",
    )
    assert "caf" in out


def test_sanitize_rejects_over_limit():
    with pytest.raises(ValueError, match="exceeds the maximum length"):
        sanitize_user_text(
            "a" * (RECIPE_TEXT_MAX_CHARS + 1),
            max_chars=RECIPE_TEXT_MAX_CHARS,
            field_name="recipe_text",
        )


def test_sanitize_rejects_empty_when_required():
    with pytest.raises(ValueError, match="required"):
        sanitize_user_text(
            "   ",
            max_chars=PERSONAL_INSTRUCTIONS_MAX_CHARS,
            field_name="personal_instructions",
            required=True,
        )


def test_sanitize_optional_empty_returns_empty_string():
    assert (
        sanitize_user_text(
            "  ",
            max_chars=PERSONAL_INSTRUCTIONS_MAX_CHARS,
            field_name="personal_instructions",
            required=False,
        )
        == ""
    )
